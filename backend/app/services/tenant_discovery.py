"""
Tenant Discovery Service
Orchestrates tenant discovery from application-level connectors

ARCHITECTURAL PRINCIPLE:
- Tenant discovery is STRUCTURE DISCOVERY only
- NO identity or access operations during discovery
- Discovered tenants start as PENDING_ONBOARDING
- Admin approval required before governance begins
"""

import re
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import (
    Application, Tenant, TenantStatus, TenantType, TenantOnboardingStatus,
    ApplicationConnector, TenantDiscoveryJob, DiscoveryJobStatus,
    ConnectorTemplate, ConnectorScope, AuditEvent
)

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredTenant:
    """Data class for tenant data discovered from external application"""
    external_id: str
    name: str
    metadata: Dict[str, Any] = None


class TenantDiscoveryService:
    """
    Service for discovering tenants from application-level connectors.
    
    This service:
    1. Validates connector scope and capabilities
    2. Creates discovery jobs for audit tracking
    3. Executes discovery (synchronously for now)
    4. Reconciles discovered tenants with existing tenants
    5. Logs all operations for audit
    
    GUARDRAILS:
    - Only APPLICATION-scoped connectors can be used
    - SSO connectors are explicitly blocked
    - No identity/access operations occur
    - Discovered tenants start as PENDING_ONBOARDING
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_application_connector(
        self,
        application_id: str,
        template_id: str,
        name: str,
        config: Dict[str, Any]
    ) -> ApplicationConnector:
        """
        Create an application-level connector.
        
        GUARDRAILS:
        - Template must be APPLICATION-scoped
        - Template must support tenant discovery
        - SSO templates are blocked
        """
        # Fetch and validate template
        template = self.db.query(ConnectorTemplate).filter(
            ConnectorTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # GUARDRAIL: Only APPLICATION-scoped templates
        if template.scope != ConnectorScope.APPLICATION.value:
            raise ValueError(
                f"Template {template.name} is TENANT-scoped. "
                "Only APPLICATION-scoped templates can be used for application connectors."
            )
        
        # GUARDRAIL: Must support tenant discovery
        if not template.supports_tenant_discovery:
            raise ValueError(
                f"Template {template.name} does not support tenant discovery."
            )
        
        # GUARDRAIL: SSO connectors cannot discover tenants
        if template.category == "SSO":
            raise ValueError(
                "SSO connectors cannot be used for tenant discovery. "
                "SSO is for authentication, not structure discovery."
            )
        
        # Verify application exists
        application = self.db.query(Application).filter(
            Application.id == application_id
        ).first()
        
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        # Create connector
        connector = ApplicationConnector(
            application_id=application_id,
            template_id=template_id,
            name=name,
            config=config,
            status="active"
        )
        
        self.db.add(connector)
        self.db.commit()
        self.db.refresh(connector)
        
        logger.info(f"Created application connector: {connector.id} for app {application_id}")
        
        return connector
    
    async def trigger_discovery(
        self,
        application_id: str,
        connector_id: str,
        triggered_by: str
    ) -> TenantDiscoveryJob:
        """
        Trigger tenant discovery for an application.
        
        Creates a discovery job and executes asynchronously.
        Returns the completed job with results.
        """
        # Validate connector
        connector = self.db.query(ApplicationConnector).filter(
            and_(
                ApplicationConnector.id == connector_id,
                ApplicationConnector.application_id == application_id
            )
        ).first()
        
        if not connector:
            raise ValueError(f"Connector {connector_id} not found for application {application_id}")
        
        if not connector.is_enabled:
            raise ValueError(f"Connector {connector.name} is disabled")
        
        # Create discovery job
        job = TenantDiscoveryJob(
            application_id=application_id,
            connector_id=connector_id,
            triggered_by=triggered_by,
            status=DiscoveryJobStatus.PENDING.value
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # Log audit event
        self._log_audit_event(
            event_type="TENANT_DISCOVERY_STARTED",
            application_id=application_id,
            details={
                "job_id": str(job.id),
                "connector_id": str(connector_id),
                "triggered_by": triggered_by
            }
        )
        
        # Execute discovery
        try:
            await self._execute_discovery(job, connector)
        except Exception as e:
            job.mark_failed(str(e))
            self.db.commit()
            
            self._log_audit_event(
                event_type="TENANT_DISCOVERY_FAILED",
                application_id=application_id,
                details={"job_id": str(job.id), "error": str(e)}
            )
            raise
        
        return job
    
    async def _execute_discovery(
        self,
        job: TenantDiscoveryJob,
        connector: ApplicationConnector
    ):
        """Execute the actual discovery process"""
        job.mark_started()
        self.db.commit()
        
        # Fetch tenants from connector using async HTTP call
        discovered_tenants = await self._fetch_tenants(connector)
        
        # Reconcile with existing tenants
        created = 0
        updated = 0
        
        existing_external_ids = set()
        
        for tenant_data in discovered_tenants:
            job.add_log_entry(
                action="discovered",
                external_id=tenant_data.external_id,
                name=tenant_data.name
            )
            
            existing_external_ids.add(tenant_data.external_id)
            
            result = self._reconcile_tenant(
                application_id=job.application_id,
                tenant_data=tenant_data,
                job_id=job.id
            )
            
            if result == "created":
                created += 1
            elif result == "updated":
                updated += 1
        
        # Deactivate tenants not in source
        deactivated = self._deactivate_missing_tenants(
            application_id=job.application_id,
            current_external_ids=existing_external_ids,
            job_id=job.id
        )
        
        # Update connector stats
        connector.last_discovery_at = datetime.utcnow()
        connector.discovery_stats = {
            "total_tenants_discovered": len(discovered_tenants),
            "last_discovery_duration_ms": 0,  # Would calculate in real impl
            "tenants_created": created,
            "tenants_updated": updated
        }
        
        # Complete job
        job.mark_completed(
            discovered=len(discovered_tenants),
            created=created,
            updated=updated,
            deactivated=deactivated
        )
        
        self.db.commit()
        
        # Log completion
        self._log_audit_event(
            event_type="TENANT_DISCOVERY_COMPLETED",
            application_id=str(job.application_id),
            details={
                "job_id": str(job.id),
                "discovered": len(discovered_tenants),
                "created": created,
                "updated": updated,
                "deactivated": deactivated
            }
        )
    
    async def _fetch_tenants(self, connector: ApplicationConnector) -> List[DiscoveredTenant]:
        """
        Fetch tenants from external application using connector config.
        
        This method:
        1. Uses the connector's config to make an HTTP call
        2. Logs all request/response details for visibility
        3. Transforms the response into DiscoveredTenant objects
        """
        from app.services.application_connector_service import ApplicationConnectorService
        from app.schemas.application_connector_config import ConnectorOperation as ConfigOperation
        
        logger.info("=" * 60)
        logger.info("TENANT DISCOVERY - HTTP CALL START")
        logger.info("=" * 60)
        logger.info(f"Connector Name: {connector.name}")
        logger.info(f"Connector ID: {connector.id}")
        logger.info(f"Application ID: {connector.application_id}")
        
        # Log config (mask sensitive fields)
        safe_config = {}
        for key, value in (connector.config or {}).items():
            if any(s in key.lower() for s in ['secret', 'password', 'token', 'key']):
                safe_config[key] = "********"
            else:
                safe_config[key] = value
        logger.info(f"Config: {safe_config}")
        
        try:
            # Transform flat config to nested ApplicationConnectorConfig format
            flat_config = connector.config or {}
            
            # Build auth_config based on auth_type
            auth_config = {}
            auth_type = flat_config.get("auth_type", "NONE")
            if auth_type == "Bearer Token" or auth_type == "API_KEY":
                auth_type = "API_KEY"
                auth_config = {
                    "header_name": "Authorization",
                    "header_value": f"Bearer {flat_config.get('auth_token', '')}"
                }
            elif auth_type == "BASIC":
                auth_config = {
                    "username": flat_config.get("username", ""),
                    "password": flat_config.get("password", "")
                }
            elif auth_type == "OAUTH2":
                auth_config = {
                    "client_id": flat_config.get("client_id", ""),
                    "client_secret": flat_config.get("client_secret", ""),
                    "token_url": flat_config.get("token_url", "")
                }
            else:
                auth_type = "NONE"
            
            # Build the nested config structure
            nested_config = {
                "connection": {
                    "base_url": flat_config.get("base_url", ""),
                    "auth_type": auth_type,
                    "auth_config": auth_config,
                    "custom_headers": flat_config.get("custom_headers", {}),
                    "timeout_seconds": flat_config.get("timeout_seconds", 30)
                },
                "endpoints": [
                    {
                        "operation": "FETCH_TENANTS",
                        "method": "GET",
                        "path": flat_config.get("tenants_endpoint", "/api/tenants"),
                        "enabled": True
                    }
                ],
                "response_mapping": {
                    "FETCH_TENANTS": {
                        "root_path": flat_config.get("tenant_root_path", flat_config.get("root_path", flat_config.get("tenant_response_path", flat_config.get("response_path")))),
                        "id_field": flat_config.get("tenant_id_field", "id"),
                        "name_field": flat_config.get("tenant_name_field", "name"),
                        "description_field": flat_config.get("tenant_description_field", "description")
                    }
                }
            }
            
            logger.info(f"Transformed config for HTTP call")
            
            # Execute the HTTP call (now properly awaited)
            raw_results = await ApplicationConnectorService.execute_operation(
                nested_config, 
                ConfigOperation.FETCH_TENANTS
            )
            
            logger.info("=" * 60)
            logger.info("TENANT DISCOVERY - RESULTS")
            logger.info("=" * 60)
            logger.info(f"Total items discovered: {len(raw_results)}")
            
            # Log each discovered item
            for idx, item in enumerate(raw_results, 1):
                logger.info(f"  [{idx}] ID: {item.get('id')}, Name: {item.get('name')}")
                if item.get('description'):
                    logger.info(f"       Description: {item.get('description')}")
            
            # Transform to DiscoveredTenant objects
            discovered = []
            for item in raw_results:
                discovered.append(DiscoveredTenant(
                    external_id=str(item.get("id", "")),
                    name=str(item.get("name", "Unknown")),
                    metadata=item
                ))
            
            logger.info("=" * 60)
            logger.info(f"TENANT DISCOVERY - COMPLETE ({len(discovered)} tenants)")
            logger.info("=" * 60)
            
            return discovered
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error("TENANT DISCOVERY - FAILED")
            logger.error("=" * 60)
            logger.error(f"Error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _reconcile_tenant(
        self,
        application_id: str,
        tenant_data: DiscoveredTenant,
        job_id: str
    ) -> str:
        """
        Reconcile a discovered tenant with existing data.
        
        Returns: "created", "updated", or "unchanged"
        """
        existing = self.db.query(Tenant).filter(
            and_(
                Tenant.application_id == application_id,
                Tenant.external_id == tenant_data.external_id
            )
        ).first()
        
        if existing:
            # Update existing tenant metadata
            existing.external_metadata = tenant_data.metadata or {}
            existing.discovered_at = datetime.utcnow()
            existing.discovered_by_job_id = job_id
            existing.updated_at = datetime.utcnow()
            
            self.db.commit()
            return "updated"
        else:
            # Create new tenant - ALWAYS starts as PENDING_ONBOARDING
            slug = self._generate_slug(tenant_data.name)
            
            new_tenant = Tenant(
                application_id=application_id,
                name=tenant_data.name,
                slug=slug,
                external_id=tenant_data.external_id,
                external_metadata=tenant_data.metadata or {},
                discovered_at=datetime.utcnow(),
                discovered_by_job_id=job_id,
                tenant_type=TenantType.CUSTOMER.value,
                status=TenantStatus.PENDING.value,  # NOT active
                onboarding_status=TenantOnboardingStatus.PENDING_ONBOARDING.value  # Requires approval
            )
            
            self.db.add(new_tenant)
            self.db.commit()
            
            self._log_audit_event(
                event_type="TENANT_CREATED",
                application_id=str(application_id),
                details={
                    "tenant_id": str(new_tenant.id),
                    "external_id": tenant_data.external_id,
                    "name": tenant_data.name,
                    "onboarding_status": "pending_onboarding"
                }
            )
            
            return "created"
    
    def _deactivate_missing_tenants(
        self,
        application_id: str,
        current_external_ids: set,
        job_id: str
    ) -> int:
        """
        Mark tenants as inactive if they're no longer in source.
        
        Only affects discovered tenants (external_id is not NULL).
        """
        discovered_tenants = self.db.query(Tenant).filter(
            and_(
                Tenant.application_id == application_id,
                Tenant.external_id.isnot(None),
                Tenant.external_id.notin_(current_external_ids),
                Tenant.status != TenantStatus.INACTIVE.value
            )
        ).all()
        
        count = 0
        for tenant in discovered_tenants:
            tenant.status = TenantStatus.INACTIVE.value
            tenant.updated_at = datetime.utcnow()
            count += 1
            
            self._log_audit_event(
                event_type="TENANT_DEACTIVATED",
                application_id=str(application_id),
                details={
                    "tenant_id": str(tenant.id),
                    "external_id": tenant.external_id,
                    "reason": "not_in_source"
                }
            )
        
        self.db.commit()
        return count
    
    def approve_tenant(
        self,
        tenant_id: str,
        approved_by: str,
        justification: Optional[str] = None
    ) -> Tenant:
        """
        Approve a discovered tenant for governance.
        
        Changes onboarding_status from PENDING_ONBOARDING to APPROVED.
        Activates the tenant status.
        """
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        if tenant.onboarding_status != TenantOnboardingStatus.PENDING_ONBOARDING.value:
            raise ValueError(
                f"Tenant {tenant.name} is not pending onboarding. "
                f"Current status: {tenant.onboarding_status}"
            )
        
        tenant.onboarding_status = TenantOnboardingStatus.APPROVED.value
        tenant.status = TenantStatus.ACTIVE.value
        tenant.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(tenant)
        
        self._log_audit_event(
            event_type="TENANT_APPROVED",
            application_id=str(tenant.application_id),
            details={
                "tenant_id": str(tenant_id),
                "approved_by": approved_by,
                "justification": justification
            }
        )
        
        return tenant
    
    def reject_tenant(
        self,
        tenant_id: str,
        rejected_by: str,
        reason: Optional[str] = None
    ) -> Tenant:
        """
        Reject a discovered tenant for governance.
        
        Changes onboarding_status to REJECTED.
        """
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        if tenant.onboarding_status != TenantOnboardingStatus.PENDING_ONBOARDING.value:
            raise ValueError(
                f"Tenant {tenant.name} is not pending onboarding."
            )
        
        tenant.onboarding_status = TenantOnboardingStatus.REJECTED.value
        tenant.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(tenant)
        
        self._log_audit_event(
            event_type="TENANT_REJECTED",
            application_id=str(tenant.application_id),
            details={
                "tenant_id": str(tenant_id),
                "rejected_by": rejected_by,
                "reason": reason
            }
        )
        
        return tenant
    
    def _generate_slug(self, name: str) -> str:
        """Generate a URL-safe slug from name"""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug
    
    def _log_audit_event(
        self,
        event_type: str,
        application_id: str,
        details: Dict[str, Any]
    ):
        """Log an audit event"""
        try:
            # Get first tenant for application (for tenant_id, if available)
            application = self.db.query(Application).filter(
                Application.id == application_id
            ).first()
            
            tenant_id = None
            if application and application.tenants:
                tenant_id = application.tenants[0].id
            
            # Extract action from event_type (e.g., TENANT_DISCOVERY_STARTED -> started)
            action = event_type.split("_")[-1].lower() if event_type else "unknown"
            
            event = AuditEvent(
                tenant_id=tenant_id,
                event_type=event_type,
                action=action,  # Required NOT NULL field
                actor="system",
                decision="allow",  # Required NOT NULL field
                details=details
            )
            self.db.add(event)
            self.db.commit()
        except Exception as e:
            # Important: Rollback the session to prevent cascading failures
            self.db.rollback()
            logger.warning(f"Failed to log audit event: {e}")

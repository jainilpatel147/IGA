"""Initial consolidated schema

Revision ID: 0001_initial
Revises: None
Create Date: 2026-02-03

This is the consolidated initial migration containing all IGA platform tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all IGA platform tables in dependency order."""
    
    # =========================================================================
    # TIER 1: Standalone lookup/reference tables (no FKs)
    # =========================================================================
    
    # User roles (platform-level role definitions)
    op.create_table('user_roles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Control mappings (GRC compliance controls)
    op.create_table('control_mappings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('control_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('required_evidence_type', sa.String(length=50), nullable=False),
        sa.Column('framework', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('control_id')
    )
    
    # API keys
    op.create_table('api_keys',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_prefix', sa.String(length=8), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('scopes', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Connector templates (SSO/Application connector catalog)
    op.create_table('connector_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),  # SSO, APPLICATION, DIRECTORY, CLOUD
        sa.Column('connector_type', sa.String(length=20), nullable=False),  # oauth2, scim, saml, rest
        sa.Column('config_schema', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('capabilities', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('documentation_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    
    # Legacy connectors table (kept for backwards compatibility)
    op.create_table('connectors',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('connector_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Access reviews (campaign-level)
    op.create_table('access_reviews',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='draft'),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('resource_filter', sa.String(length=200), nullable=True),
        sa.Column('total_items', sa.Integer(), nullable=True, default=0),
        sa.Column('certified_count', sa.Integer(), nullable=True, default=0),
        sa.Column('revoked_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Migration tracker (for seeder idempotency)
    op.create_table('migration_tracker',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('migration_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('executed_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('executed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('migration_name')
    )
    
    # =========================================================================
    # TIER 2: Applications (root of tenant hierarchy)
    # =========================================================================
    
    op.create_table('applications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner', sa.String(length=100), nullable=False),
        sa.Column('deployment_type', sa.String(length=20), nullable=False, server_default='on_premise'),
        sa.Column('integration_type', sa.String(length=20), nullable=True, default='readonly'),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('base_url', sa.String(length=500), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # =========================================================================
    # TIER 3: Tenants (depends on applications)
    # =========================================================================
    
    op.create_table('tenants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tenant_type', sa.String(length=20), nullable=False, server_default='customer'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('settings', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id', 'name', name='uq_tenant_app_name')
    )
    op.create_index('ix_tenants_application_id', 'tenants', ['application_id'])
    
    # =========================================================================
    # TIER 4: Tenant-scoped core entities
    # =========================================================================
    
    # Identities (users/services per tenant)
    op.create_table('identities',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('identity_type', sa.String(length=50), nullable=False, server_default='user'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('attributes', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_identity_tenant_email'),
        sa.UniqueConstraint('tenant_id', 'external_id', name='uq_identity_tenant_external_id')
    )
    op.create_index('ix_identities_id', 'identities', ['id'])
    op.create_index('ix_identities_name', 'identities', ['name'])
    op.create_index('ix_identities_email', 'identities', ['email'])
    op.create_index('ix_identities_tenant_id', 'identities', ['tenant_id'])
    
    # Roles (per tenant)
    op.create_table('roles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=150), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_privileged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('risk_level', sa.String(length=20), nullable=False, server_default='low'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('extra_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_role_tenant_name')
    )
    op.create_index('ix_roles_tenant_id', 'roles', ['tenant_id'])
    
    # Identity providers (per tenant)
    op.create_table('identity_providers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('provider_type', sa.String(length=20), nullable=False),
        sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_idp_tenant_name')
    )
    op.create_index('ix_identity_providers_tenant_id', 'identity_providers', ['tenant_id'])
    
    # Tenant connectors (per tenant, links to connector_templates)
    op.create_table('tenant_connectors',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('template_id', sa.UUID(), nullable=False),
        sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('sync_stats', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['connector_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'template_id', name='uq_tenant_connector')
    )
    op.create_index('ix_tenant_connectors_tenant_id', 'tenant_connectors', ['tenant_id'])
    op.create_index('ix_tenant_connectors_template_id', 'tenant_connectors', ['template_id'])
    
    # =========================================================================
    # TIER 5: Application-scoped entities
    # =========================================================================
    
    # Entitlements (application-scoped permissions)
    op.create_table('entitlements',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=150), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=True),
        sa.Column('is_privileged', sa.Boolean(), nullable=True, default=False),
        sa.Column('risk_level', sa.String(length=20), nullable=True, default='low'),
        sa.Column('extra_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id', 'name', name='uq_entitlement_app_name')
    )
    op.create_index('ix_entitlements_application_id', 'entitlements', ['application_id'])
    
    # =========================================================================
    # TIER 6: Junction/relationship tables
    # =========================================================================
    
    # Identity-Role assignments
    op.create_table('identity_roles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('identity_id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.Column('assigned_by', sa.UUID(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identity_id', 'role_id', name='uq_identity_role')
    )
    op.create_index('ix_identity_roles_identity_id', 'identity_roles', ['identity_id'])
    op.create_index('ix_identity_roles_role_id', 'identity_roles', ['role_id'])
    
    # Role-Entitlement mapping
    op.create_table('role_entitlements',
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.Column('entitlement_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entitlement_id'], ['entitlements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'entitlement_id')
    )
    
    # Application assignments (identity to application/entitlement)
    op.create_table('application_assignments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('identity_id', sa.UUID(), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('entitlement_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, default='active'),
        sa.Column('access_request_id', sa.UUID(), nullable=True),
        sa.Column('granted_by', sa.String(length=100), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_by', sa.String(length=100), nullable=True),
        sa.Column('revoke_reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id']),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id']),
        sa.ForeignKeyConstraint(['entitlement_id'], ['entitlements.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # =========================================================================
    # TIER 7: Access request workflow
    # =========================================================================
    
    op.create_table('access_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('requester_identity_id', sa.UUID(), nullable=True),
        sa.Column('target_identity_id', sa.UUID(), nullable=True),
        sa.Column('role_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.UUID(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('requested_valid_from', sa.DateTime(), nullable=True),
        sa.Column('requested_valid_until', sa.DateTime(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requester_identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_access_requests_id', 'access_requests', ['id'])
    op.create_index('ix_access_requests_tenant_id', 'access_requests', ['tenant_id'])
    op.create_index('ix_access_requests_requester_identity_id', 'access_requests', ['requester_identity_id'])
    op.create_index('ix_access_requests_target_identity_id', 'access_requests', ['target_identity_id'])
    op.create_index('ix_access_requests_role_id', 'access_requests', ['role_id'])
    
    # Access review items
    op.create_table('access_review_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('review_id', sa.UUID(), nullable=False),
        sa.Column('identity_id', sa.UUID(), nullable=False),
        sa.Column('identity_name', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.String(length=20), nullable=True),
        sa.Column('decision_by', sa.String(length=100), nullable=True),
        sa.Column('decision_at', sa.DateTime(), nullable=True),
        sa.Column('decision_note', sa.Text(), nullable=True),
        sa.Column('risk_level', sa.String(length=20), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['review_id'], ['access_reviews.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # =========================================================================
    # TIER 8: Admin tables
    # =========================================================================
    
    op.create_table('platform_admins',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('identity_id', sa.UUID(), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('granted_by', sa.UUID(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identity_id', name='uq_platform_admin_identity')
    )
    op.create_index('ix_platform_admins_identity_id', 'platform_admins', ['identity_id'])
    
    op.create_table('application_admins',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('identity_id', sa.UUID(), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('granted_by', sa.UUID(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id', 'identity_id', name='uq_app_admin_identity')
    )
    op.create_index('ix_application_admins_application_id', 'application_admins', ['application_id'])
    op.create_index('ix_application_admins_identity_id', 'application_admins', ['identity_id'])
    
    op.create_table('tenant_admins',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('identity_id', sa.UUID(), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('granted_by', sa.UUID(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'identity_id', name='uq_tenant_admin_identity')
    )
    op.create_index('ix_tenant_admins_tenant_id', 'tenant_admins', ['tenant_id'])
    op.create_index('ix_tenant_admins_identity_id', 'tenant_admins', ['identity_id'])
    
    # =========================================================================
    # TIER 9: Audit and governance
    # =========================================================================
    
    op.create_table('audit_events',
        sa.Column('event_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('actor', sa.String(length=255), nullable=False),
        sa.Column('actor_identity_id', sa.UUID(), nullable=True),
        sa.Column('target', sa.String(length=255), nullable=True),
        sa.Column('target_type', sa.String(length=100), nullable=True),
        sa.Column('target_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['actor_identity_id'], ['identities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('event_id')
    )
    op.create_index('ix_audit_events_event_id', 'audit_events', ['event_id'])
    op.create_index('ix_audit_events_event_type', 'audit_events', ['event_type'])
    op.create_index('ix_audit_events_actor', 'audit_events', ['actor'])
    op.create_index('ix_audit_events_timestamp', 'audit_events', ['timestamp'])
    op.create_index('ix_audit_events_tenant_id', 'audit_events', ['tenant_id'])
    op.create_index('ix_audit_events_actor_identity_id', 'audit_events', ['actor_identity_id'])
    
    op.create_table('governance_evidence',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('audit_event_id', sa.String(length=100), nullable=False),
        sa.Column('identity_id', sa.UUID(), nullable=True),
        sa.Column('identity_name', sa.String(length=100), nullable=True),
        sa.Column('application_id', sa.UUID(), nullable=True),
        sa.Column('application_name', sa.String(length=100), nullable=True),
        sa.Column('entitlement_id', sa.UUID(), nullable=True),
        sa.Column('entitlement_name', sa.String(length=100), nullable=True),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('immutable_reference', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    
    # Tier 9
    op.drop_table('governance_evidence')
    op.drop_index('ix_audit_events_actor_identity_id', table_name='audit_events')
    op.drop_index('ix_audit_events_tenant_id', table_name='audit_events')
    op.drop_index('ix_audit_events_timestamp', table_name='audit_events')
    op.drop_index('ix_audit_events_actor', table_name='audit_events')
    op.drop_index('ix_audit_events_event_type', table_name='audit_events')
    op.drop_index('ix_audit_events_event_id', table_name='audit_events')
    op.drop_table('audit_events')
    
    # Tier 8
    op.drop_index('ix_tenant_admins_identity_id', table_name='tenant_admins')
    op.drop_index('ix_tenant_admins_tenant_id', table_name='tenant_admins')
    op.drop_table('tenant_admins')
    op.drop_index('ix_application_admins_identity_id', table_name='application_admins')
    op.drop_index('ix_application_admins_application_id', table_name='application_admins')
    op.drop_table('application_admins')
    op.drop_index('ix_platform_admins_identity_id', table_name='platform_admins')
    op.drop_table('platform_admins')
    
    # Tier 7
    op.drop_table('access_review_items')
    op.drop_index('ix_access_requests_role_id', table_name='access_requests')
    op.drop_index('ix_access_requests_target_identity_id', table_name='access_requests')
    op.drop_index('ix_access_requests_requester_identity_id', table_name='access_requests')
    op.drop_index('ix_access_requests_tenant_id', table_name='access_requests')
    op.drop_index('ix_access_requests_id', table_name='access_requests')
    op.drop_table('access_requests')
    
    # Tier 6
    op.drop_table('application_assignments')
    op.drop_table('role_entitlements')
    op.drop_index('ix_identity_roles_role_id', table_name='identity_roles')
    op.drop_index('ix_identity_roles_identity_id', table_name='identity_roles')
    op.drop_table('identity_roles')
    
    # Tier 5
    op.drop_index('ix_entitlements_application_id', table_name='entitlements')
    op.drop_table('entitlements')
    
    # Tier 4
    op.drop_index('ix_tenant_connectors_template_id', table_name='tenant_connectors')
    op.drop_index('ix_tenant_connectors_tenant_id', table_name='tenant_connectors')
    op.drop_table('tenant_connectors')
    op.drop_index('ix_identity_providers_tenant_id', table_name='identity_providers')
    op.drop_table('identity_providers')
    op.drop_index('ix_roles_tenant_id', table_name='roles')
    op.drop_table('roles')
    op.drop_index('ix_identities_tenant_id', table_name='identities')
    op.drop_index('ix_identities_email', table_name='identities')
    op.drop_index('ix_identities_name', table_name='identities')
    op.drop_index('ix_identities_id', table_name='identities')
    op.drop_table('identities')
    
    # Tier 3
    op.drop_index('ix_tenants_application_id', table_name='tenants')
    op.drop_table('tenants')
    
    # Tier 2
    op.drop_table('applications')
    
    # Tier 1
    op.drop_table('migration_tracker')
    op.drop_table('access_reviews')
    op.drop_table('connectors')
    op.drop_table('connector_templates')
    op.drop_table('api_keys')
    op.drop_table('control_mappings')
    op.drop_table('user_roles')

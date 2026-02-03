"""
Application-Level Connectors & Tenant Discovery Migration

Adds:
- application_connectors table: Application-scoped connectors for tenant discovery
- tenant_discovery_jobs table: Discovery job tracking with audit trail
- scope and supports_tenant_discovery columns to connector_templates
- external_id, external_metadata, discovered_at, onboarding_status columns to tenants

Revision ID: 0002_application_connectors
Revises: 0001_initial
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '0002_application_connectors'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # 1. Add new columns to connector_templates
    # ==========================================================================
    op.add_column('connector_templates', 
        sa.Column('scope', sa.String(20), nullable=False, server_default='TENANT')
    )
    op.add_column('connector_templates',
        sa.Column('supports_tenant_discovery', sa.Boolean(), nullable=False, server_default='false')
    )
    
    # ==========================================================================
    # 2. Create application_connectors table
    # ==========================================================================
    op.create_table(
        'application_connectors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('applications.id', ondelete='CASCADE'), 
                  nullable=False, index=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('connector_templates.id', ondelete='RESTRICT'),
                  nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_discovery_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('discovery_stats', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('application_id', 'template_id', name='uq_app_connector'),
    )
    
    # ==========================================================================
    # 3. Create tenant_discovery_jobs table
    # ==========================================================================
    op.create_table(
        'tenant_discovery_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('applications.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('connector_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('application_connectors.id', ondelete='SET NULL'),
                  nullable=True, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('triggered_by', sa.String(255), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('discovered_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deactivated_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('discovery_log', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # ==========================================================================
    # 4. Add discovery metadata columns to tenants
    # ==========================================================================
    op.add_column('tenants',
        sa.Column('external_id', sa.String(255), nullable=True, index=True)
    )
    op.add_column('tenants',
        sa.Column('external_metadata', postgresql.JSONB(), nullable=False, server_default='{}')
    )
    op.add_column('tenants',
        sa.Column('discovered_at', sa.DateTime(), nullable=True)
    )
    op.add_column('tenants',
        sa.Column('discovered_by_job_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column('tenants',
        sa.Column('onboarding_status', sa.String(30), nullable=False, server_default='manually_created')
    )
    
    # Add foreign key for discovered_by_job_id
    op.create_foreign_key(
        'fk_tenant_discovery_job',
        'tenants', 'tenant_discovery_jobs',
        ['discovered_by_job_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add unique constraint for external_id per application
    op.create_unique_constraint(
        'uq_tenant_app_external_id',
        'tenants',
        ['application_id', 'external_id']
    )


def downgrade() -> None:
    # Remove unique constraint
    op.drop_constraint('uq_tenant_app_external_id', 'tenants', type_='unique')
    
    # Remove foreign key
    op.drop_constraint('fk_tenant_discovery_job', 'tenants', type_='foreignkey')
    
    # Remove columns from tenants
    op.drop_column('tenants', 'onboarding_status')
    op.drop_column('tenants', 'discovered_by_job_id')
    op.drop_column('tenants', 'discovered_at')
    op.drop_column('tenants', 'external_metadata')
    op.drop_column('tenants', 'external_id')
    
    # Drop tables
    op.drop_table('tenant_discovery_jobs')
    op.drop_table('application_connectors')
    
    # Remove columns from connector_templates
    op.drop_column('connector_templates', 'supports_tenant_discovery')
    op.drop_column('connector_templates', 'scope')

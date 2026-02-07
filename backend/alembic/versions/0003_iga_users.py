"""
Add IGA Users Table

Creates table for platform users (super_admin and app_admin)

Revision ID: 0003_iga_users
Revises: 0002_application_connectors
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '0003_iga_users'
down_revision = '0002_application_connectors'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create iga_users table
    op.create_table(
        'iga_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='app_admin'),
        sa.Column('application_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('applications.id', ondelete='CASCADE'),
                  nullable=True, index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('iga_users')

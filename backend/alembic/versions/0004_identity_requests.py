"""Identity requests support

Revision ID: 0004_identity_reqs
Revises: 0003_iga_users
Create Date: 2026-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_identity_reqs'
down_revision: Union[str, None] = '0003_iga_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add request_type column
    op.add_column('access_requests', sa.Column('request_type', sa.String(length=50), server_default='ROLE_ACCESS', nullable=False))
    
    # 2. Make columns nullable to support identity creation requests (where identity/role doesn't exist yet)
    op.alter_column('access_requests', 'role_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.alter_column('access_requests', 'requester_identity_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.alter_column('access_requests', 'target_identity_id',
               existing_type=sa.UUID(),
               nullable=True)


def downgrade() -> None:
    # Revert changes
    op.alter_column('access_requests', 'target_identity_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.alter_column('access_requests', 'requester_identity_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.alter_column('access_requests', 'role_id',
               existing_type=sa.UUID(),
               nullable=False)
    
    op.drop_column('access_requests', 'request_type')

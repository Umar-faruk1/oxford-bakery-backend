"""add role to users

Revision ID: add_role_to_users
Revises: 
Create Date: 2024-03-19 16:54:33.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_role_to_users'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add role column with default value 'user'
    op.add_column('users', sa.Column('role', sa.String(50), nullable=False, server_default='user'))


def downgrade() -> None:
    # Remove role column
    op.drop_column('users', 'role') 
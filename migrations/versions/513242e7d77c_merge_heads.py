"""merge heads

Revision ID: 513242e7d77c
Revises: 3fb08e558bd8, add_role_to_users
Create Date: 2025-03-05 19:16:10.596668

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '513242e7d77c'
down_revision = ('3fb08e558bd8', 'add_role_to_users')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 
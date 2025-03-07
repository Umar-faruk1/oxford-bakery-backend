from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add role column with default value 'user'
    op.add_column('users', sa.Column('role', sa.String(50), nullable=False, server_default='user'))

def downgrade():
    # Remove role column
    op.drop_column('users', 'role') 
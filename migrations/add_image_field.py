from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_image_field'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add image column to users table
    op.add_column('users', sa.Column('image', sa.String(), nullable=True))

def downgrade():
    # Remove image column from users table
    op.drop_column('users', 'image') 
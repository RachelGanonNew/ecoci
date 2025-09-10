"""Add api_key to users

Revision ID: add_api_key_to_users
Revises: 
Create Date: 2025-09-10 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_api_key_to_users'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add api_key column to users table
    op.add_column('users', 
        sa.Column('api_key', sa.String(length=64), unique=True, index=True, nullable=True)
    )

def downgrade():
    # Drop the api_key column
    op.drop_column('users', 'api_key')

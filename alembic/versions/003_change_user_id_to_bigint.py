"""Change user_id to BIGINT

Revision ID: 003_change_user_id_to_bigint
Revises: 002_add_users
Create Date: 2024-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_change_user_id_to_bigint'
down_revision = '002_add_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change user_id column type to BIGINT in all tables
    # PostgreSQL requires explicit cast when changing integer types
    
    # Change payments.user_id
    op.execute("""
        ALTER TABLE payments 
        ALTER COLUMN user_id TYPE BIGINT USING user_id::BIGINT;
    """)
    
    # Change users.user_id
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN user_id TYPE BIGINT USING user_id::BIGINT;
    """)
    
    # Change user_requests.user_id
    op.execute("""
        ALTER TABLE user_requests 
        ALTER COLUMN user_id TYPE BIGINT USING user_id::BIGINT;
    """)


def downgrade() -> None:
    # Change back to INTEGER (may fail if values exceed INTEGER range)
    op.execute("""
        ALTER TABLE payments 
        ALTER COLUMN user_id TYPE INTEGER USING user_id::INTEGER;
    """)
    
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN user_id TYPE INTEGER USING user_id::INTEGER;
    """)
    
    op.execute("""
        ALTER TABLE user_requests 
        ALTER COLUMN user_id TYPE INTEGER USING user_id::INTEGER;
    """)


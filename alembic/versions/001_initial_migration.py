"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type
    paymentstatus_enum = sa.Enum('pending', 'succeeded', 'canceled', name='paymentstatus')
    paymentstatus_enum.create(op.get_bind(), checkfirst=True)
    
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', paymentstatus_enum, nullable=False),
        sa.Column('yookassa_payment_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)
    op.create_index(op.f('ix_payments_phone_number'), 'payments', ['phone_number'], unique=False)
    op.create_index(op.f('ix_payments_yookassa_payment_id'), 'payments', ['yookassa_payment_id'], unique=True)
    
    # Create user_requests table
    op.create_table(
        'user_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('calculated_date', sa.Date(), nullable=True),
        sa.Column('cycle_number', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_requests_id'), 'user_requests', ['id'], unique=False)
    op.create_index(op.f('ix_user_requests_user_id'), 'user_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_requests_phone_number'), 'user_requests', ['phone_number'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_requests_phone_number'), table_name='user_requests')
    op.drop_index(op.f('ix_user_requests_user_id'), table_name='user_requests')
    op.drop_index(op.f('ix_user_requests_id'), table_name='user_requests')
    op.drop_table('user_requests')
    op.drop_index(op.f('ix_payments_yookassa_payment_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_phone_number'), table_name='payments')
    op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
    sa.Enum(name='paymentstatus').drop(op.get_bind(), checkfirst=True)


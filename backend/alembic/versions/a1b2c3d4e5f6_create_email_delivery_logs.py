"""
Phase 20 Alembic Migration: create email_delivery_logs table

Revision ID: a1b2c3d4e5f6
Revises: c1a2b3c4d5e6
Create Date: 2026-09-20 15:41:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'email_delivery_logs',
        sa.Column('id', sa.String(length=50), primary_key=True, index=True, nullable=False),
        sa.Column('circular_id', sa.String(length=50), nullable=False, index=True),
        sa.Column('circular_ref', sa.String(length=50), nullable=True),
        sa.Column('recipient_email', sa.String(length=255), nullable=False, index=True),
        sa.Column('recipient_name', sa.String(length=150), nullable=True),
        sa.Column('recipient_user_id', sa.String(length=50), nullable=True, index=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING', index=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        'ix_email_delivery_logs_circular_status',
        'email_delivery_logs',
        ['circular_id', 'status'],
    )


def downgrade() -> None:
    op.drop_index('ix_email_delivery_logs_circular_status', table_name='email_delivery_logs')
    op.drop_table('email_delivery_logs')

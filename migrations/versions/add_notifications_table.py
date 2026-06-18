"""add notifications table

Revision ID: add_notifications_table
Revises: 
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_notifications_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('type', sa.String(length=64), nullable=False),
        sa.Column('module', sa.String(length=64), nullable=True),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('priority', sa.String(length=16), nullable=False),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('related_type', sa.String(length=64), nullable=True),
        sa.Column('related_id', sa.String(length=64), nullable=True),
        sa.Column('route', sa.String(length=256), nullable=True),
        sa.Column('is_read', sa.Boolean, nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('company_id', sa.String(length=36), nullable=True),
        sa.Column('circle_id', sa.String(length=36), nullable=True),
    )
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])


def downgrade():
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_is_read', table_name='notifications')
    op.drop_table('notifications')

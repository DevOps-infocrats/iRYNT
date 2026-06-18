"""Add approval tables

Revision ID: 0001_add_approvals
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_add_approvals'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create approval_requests table
    op.create_table(
        'approval_requests',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('approval_type', sa.String(50), nullable=False),
        sa.Column('module_name', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('request_title', sa.String(255), nullable=False),
        sa.Column('request_description', sa.Text(), nullable=True),
        sa.Column('requested_by_id', sa.String(36), nullable=False),
        sa.Column('assigned_approver_id', sa.String(36), nullable=True),
        sa.Column('hierarchy_scope', sa.String(100), nullable=True),
        sa.Column('company_id', sa.String(36), nullable=True),
        sa.Column('circle_id', sa.String(36), nullable=True),
        sa.Column('client_id', sa.String(36), nullable=True),
        sa.Column('project_id', sa.String(36), nullable=True),
        sa.Column('subzone_id', sa.String(36), nullable=True),
        sa.Column('frt_id', sa.String(36), nullable=True),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('approval_status', sa.String(20), nullable=False),
        sa.Column('sla_due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['requested_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_approver_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_approval_requests_approval_type', 'approval_requests', ['approval_type'], unique=False)
    op.create_index('idx_approval_requests_approval_status', 'approval_requests', ['approval_status'], unique=False)
    op.create_index('idx_approval_requests_assigned_approver', 'approval_requests', ['assigned_approver_id'], unique=False)
    op.create_index('idx_approval_requests_requested_by', 'approval_requests', ['requested_by_id'], unique=False)
    op.create_index('idx_approval_requests_company_id', 'approval_requests', ['company_id'], unique=False)
    op.create_index('idx_approval_requests_circle_id', 'approval_requests', ['circle_id'], unique=False)
    op.create_index('idx_approval_requests_client_id', 'approval_requests', ['client_id'], unique=False)
    op.create_index('idx_approval_requests_project_id', 'approval_requests', ['project_id'], unique=False)
    op.create_index('idx_approval_requests_subzone_id', 'approval_requests', ['subzone_id'], unique=False)
    op.create_index('idx_approval_requests_sla_due_at', 'approval_requests', ['sla_due_at'], unique=False)

    # Create approval_workflows table
    op.create_table(
        'approval_workflows',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('approval_type', sa.String(50), nullable=False),
        sa.Column('approval_level', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.String(36), nullable=False),
        sa.Column('escalation_after_minutes', sa.Integer(), nullable=False),
        sa.Column('auto_escalate', sa.Boolean(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('approval_type', 'approval_level', name='uix_approval_type_level')
    )
    op.create_index('idx_approval_workflows_approval_type', 'approval_workflows', ['approval_type'], unique=False)
    op.create_index('idx_approval_workflows_role_id', 'approval_workflows', ['role_id'], unique=False)

    # Create approval_histories table
    op.create_table(
        'approval_histories',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('approval_request_id', sa.String(36), nullable=False),
        sa.Column('action_taken', sa.String(50), nullable=False),
        sa.Column('action_by_id', sa.String(36), nullable=True),
        sa.Column('previous_status', sa.String(20), nullable=True),
        sa.Column('new_status', sa.String(20), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('action_time', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['approval_request_id'], ['approval_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['action_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_approval_histories_approval_request_id', 'approval_histories', ['approval_request_id'], unique=False)
    op.create_index('idx_approval_histories_action_by', 'approval_histories', ['action_by_id'], unique=False)
    op.create_index('idx_approval_histories_action_time', 'approval_histories', ['action_time'], unique=False)

    # Create approval_comments table
    op.create_table(
        'approval_comments',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('approval_request_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['approval_request_id'], ['approval_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_approval_comments_approval_request_id', 'approval_comments', ['approval_request_id'], unique=False)
    op.create_index('idx_approval_comments_user_id', 'approval_comments', ['user_id'], unique=False)
    op.create_index('idx_approval_comments_created_at', 'approval_comments', ['created_at'], unique=False)


def downgrade():
    op.drop_table('approval_comments')
    op.drop_table('approval_histories')
    op.drop_table('approval_workflows')
    op.drop_table('approval_requests')

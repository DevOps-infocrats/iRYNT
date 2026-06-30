"""Add attendance MIS/KAM approval workflow fields

Revision ID: d4e5f6a7b8c9
Revises: 9a1b2c3d4e5f
Create Date: 2026-06-30 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4e5f6a7b8c9'
down_revision = '9a1b2c3d4e5f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('driver_attendance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('approval_status', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('seatbelt_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('selfie_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('dashboard_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('odometer_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('helmet_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('safety_shoes_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('safety_jacket_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('id_card_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('mis_verified_by', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('mis_verified_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('mis_remarks', sa.String(length=512), nullable=True))
        batch_op.add_column(sa.Column('kam_verified_by', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('kam_verified_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('kam_remarks', sa.String(length=512), nullable=True))
        batch_op.create_index('idx_driver_attendance_approval_status', ['approval_status'], unique=False)
        batch_op.create_foreign_key(
            'fk_driver_attendance_mis_verified_by',
            'users',
            ['mis_verified_by'],
            ['id'],
            ondelete='SET NULL',
        )
        batch_op.create_foreign_key(
            'fk_driver_attendance_kam_verified_by',
            'users',
            ['kam_verified_by'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade():
    with op.batch_alter_table('driver_attendance', schema=None) as batch_op:
        batch_op.drop_constraint('fk_driver_attendance_kam_verified_by', type_='foreignkey')
        batch_op.drop_constraint('fk_driver_attendance_mis_verified_by', type_='foreignkey')
        batch_op.drop_index('idx_driver_attendance_approval_status')
        batch_op.drop_column('kam_remarks')
        batch_op.drop_column('kam_verified_at')
        batch_op.drop_column('kam_verified_by')
        batch_op.drop_column('mis_remarks')
        batch_op.drop_column('mis_verified_at')
        batch_op.drop_column('mis_verified_by')
        batch_op.drop_column('id_card_verified')
        batch_op.drop_column('safety_jacket_verified')
        batch_op.drop_column('safety_shoes_verified')
        batch_op.drop_column('helmet_verified')
        batch_op.drop_column('odometer_verified')
        batch_op.drop_column('dashboard_verified')
        batch_op.drop_column('selfie_verified')
        batch_op.drop_column('seatbelt_verified')
        batch_op.drop_column('approval_status')

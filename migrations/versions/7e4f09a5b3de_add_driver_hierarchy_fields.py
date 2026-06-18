"""Add missing driver profile hierarchy fields

Revision ID: 7e4f09a5b3de
Revises: 7d4c606df3f5
Create Date: 2026-06-12 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7e4f09a5b3de'
down_revision = '7d4c606df3f5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('driver_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('circle_id', sa.String(length=36), nullable=True))
        batch_op.create_index(batch_op.f('ix_driver_profiles_circle_id'), ['circle_id'], unique=False)
        batch_op.create_foreign_key(None, 'circles', ['circle_id'], ['id'], ondelete='SET NULL')

        batch_op.add_column(sa.Column('project_id', sa.String(length=36), nullable=True))
        batch_op.create_index(batch_op.f('ix_driver_profiles_project_id'), ['project_id'], unique=False)
        batch_op.create_foreign_key(None, 'projects', ['project_id'], ['id'], ondelete='SET NULL')

        batch_op.add_column(sa.Column('subzone_id', sa.String(length=36), nullable=True))
        batch_op.create_index(batch_op.f('ix_driver_profiles_subzone_id'), ['subzone_id'], unique=False)
        batch_op.create_foreign_key(None, 'subzones', ['subzone_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('driver_profiles', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_driver_profiles_subzone_id'))
        batch_op.drop_column('subzone_id')

        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_driver_profiles_project_id'))
        batch_op.drop_column('project_id')

        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_driver_profiles_circle_id'))
        batch_op.drop_column('circle_id')

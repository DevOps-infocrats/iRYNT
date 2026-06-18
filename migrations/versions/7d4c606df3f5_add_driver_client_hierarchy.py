"""Add client_id to driver_profiles for hierarchy support

Revision ID: 7d4c606df3f5
Revises: 6c1caed95851
Create Date: 2026-06-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7d4c606df3f5'
down_revision = '6c1caed95851'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('driver_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('client_id', sa.String(length=36), nullable=True))
        batch_op.create_index(batch_op.f('ix_driver_profiles_client_id'), ['client_id'], unique=False)
        batch_op.create_foreign_key(None, 'clients', ['client_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('driver_profiles', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_driver_profiles_client_id'))
        batch_op.drop_column('client_id')

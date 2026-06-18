"""Add attendance geo verification fields

Revision ID: 9a1b2c3d4e5f
Revises: 7e4f09a5b3de
Create Date: 2026-06-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a1b2c3d4e5f'
down_revision = '7e4f09a5b3de'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('driver_attendance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('checkin_latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('checkin_longitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('checkout_latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('checkout_longitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('location_accuracy', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('geo_verified', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('geo_status', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('geo_distance_meters', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('driver_attendance', schema=None) as batch_op:
        batch_op.drop_column('geo_distance_meters')
        batch_op.drop_column('geo_status')
        batch_op.drop_column('geo_verified')
        batch_op.drop_column('location_accuracy')
        batch_op.drop_column('checkout_longitude')
        batch_op.drop_column('checkout_latitude')
        batch_op.drop_column('checkin_longitude')
        batch_op.drop_column('checkin_latitude')

"""Remove license and compliance verification columns

Revision ID: 8f2a1b3c4d5e
Revises: 7e4f09a5b3de
Create Date: 2026-06-12 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f2a1b3c4d5e'
down_revision = '7e4f09a5b3de'
branch_labels = None
depends_on = None


def upgrade():
    # Drop verification-related columns safely
    with op.batch_alter_table('driver_licenses', schema=None) as batch_op:
        # Only drop if exists; Alembic batch_op will error if missing during execution,
        # but the migration is written to remove these known columns.
        batch_op.drop_column('verification_status')

    with op.batch_alter_table('driver_profiles', schema=None) as batch_op:
        batch_op.drop_column('license_status')
        batch_op.drop_column('compliance_status')


def downgrade():
    # Recreate the dropped columns with previous types and defaults
    with op.batch_alter_table('driver_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('compliance_status', sa.String(length=30), nullable=True, server_default=sa.text("'Pending'")))
        batch_op.add_column(sa.Column('license_status', sa.String(length=30), nullable=True, server_default=sa.text("'Pending'")))
        # remove server_default if desired after data migration

    with op.batch_alter_table('driver_licenses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('verification_status', sa.String(length=30), nullable=True, server_default=sa.text("'Pending'")))
        # remove server_default if desired after data migration

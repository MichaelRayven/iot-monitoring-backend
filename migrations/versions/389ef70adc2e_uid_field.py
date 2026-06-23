"""uid_field

Revision ID: 389ef70adc2e
Revises: 17bab55bb08d
Create Date: 2026-06-01 00:00:00.000000

Replaces separate dev_eui and mac_address columns with a single uid column.
For existing vega rows: uid = dev_eui.
Beacons didn't exist before this migration, so no backfill needed for mac_address.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '389ef70adc2e'
down_revision: Union[str, Sequence[str], None] = '17bab55bb08d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add uid as nullable first so we can backfill
    op.add_column(
        'floor_devices',
        sa.Column('uid', sa.String(length=64), nullable=True),
    )

    # 2. Backfill: existing rows are all vega devices, uid = dev_eui
    op.execute("UPDATE floor_devices SET uid = dev_eui WHERE uid IS NULL")

    # 3. Make uid non-nullable and unique
    op.alter_column('floor_devices', 'uid', nullable=False)
    op.create_index(op.f('ix_floor_devices_uid'), 'floor_devices', ['uid'], unique=True)

    # 4. Drop the old separate columns and their indexes
    op.drop_index(op.f('ix_floor_devices_dev_eui'), table_name='floor_devices')
    op.drop_column('floor_devices', 'dev_eui')

    op.drop_index(op.f('ix_floor_devices_mac_address'), table_name='floor_devices')
    op.drop_column('floor_devices', 'mac_address')


def downgrade() -> None:
    # Restore dev_eui and mac_address columns
    op.add_column(
        'floor_devices',
        sa.Column('dev_eui', sa.String(length=16), nullable=True),
    )
    op.add_column(
        'floor_devices',
        sa.Column('mac_address', sa.String(length=17), nullable=True),
    )

    # Backfill based on device_kind
    op.execute(
        "UPDATE floor_devices SET dev_eui = uid WHERE device_kind = 'vega'"
    )
    op.execute(
        "UPDATE floor_devices SET mac_address = uid WHERE device_kind = 'beacon'"
    )

    # Recreate indexes
    op.create_index(
        op.f('ix_floor_devices_dev_eui'), 'floor_devices', ['dev_eui'], unique=True
    )
    op.create_index(
        op.f('ix_floor_devices_mac_address'), 'floor_devices', ['mac_address'], unique=True
    )

    # Drop uid
    op.drop_index(op.f('ix_floor_devices_uid'), table_name='floor_devices')
    op.drop_column('floor_devices', 'uid')

"""beacon_support

Revision ID: 17bab55bb08d
Revises: fd9e4c018580, 9ebb4c34ae2e
Create Date: 2026-06-01 00:00:00.000000

Merges:
- fd9e4c018580 (building_model)
- 9ebb4c34ae2e (device_type_required) — superseded; device_type is made nullable here
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '17bab55bb08d'
down_revision: Union[str, Sequence[str], None] = ('fd9e4c018580', '9ebb4c34ae2e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add device_kind column with default 'vega' (existing rows are all vega devices)
    op.add_column(
        'floor_devices',
        sa.Column('device_kind', sa.String(length=16), nullable=False, server_default='vega'),
    )
    # Remove the server_default after backfill so it's enforced by app logic
    op.alter_column('floor_devices', 'device_kind', server_default=None)

    # Add mac_address column for beacons (nullable, unique)
    op.add_column(
        'floor_devices',
        sa.Column('mac_address', sa.String(length=17), nullable=True),
    )
    op.create_index(
        op.f('ix_floor_devices_mac_address'),
        'floor_devices',
        ['mac_address'],
        unique=True,
    )

    # Make dev_eui nullable (beacons don't have one)
    op.alter_column(
        'floor_devices',
        'dev_eui',
        existing_type=sa.String(length=16),
        nullable=True,
    )

    # Make device_type nullable (beacons don't have one)
    op.alter_column(
        'floor_devices',
        'device_type',
        existing_type=sa.String(length=64),
        nullable=True,
    )

    # Add name column if it doesn't already exist
    # (name was already present in the model; this is a no-op for existing schemas)


def downgrade() -> None:
    # Restore device_type to non-nullable (will fail if any NULL rows exist)
    op.alter_column(
        'floor_devices',
        'device_type',
        existing_type=sa.String(length=64),
        nullable=False,
    )

    # Restore dev_eui to non-nullable (will fail if any beacon rows exist)
    op.alter_column(
        'floor_devices',
        'dev_eui',
        existing_type=sa.String(length=16),
        nullable=False,
    )

    # Drop mac_address index and column
    op.drop_index(op.f('ix_floor_devices_mac_address'), table_name='floor_devices')
    op.drop_column('floor_devices', 'mac_address')

    # Drop device_kind column
    op.drop_column('floor_devices', 'device_kind')

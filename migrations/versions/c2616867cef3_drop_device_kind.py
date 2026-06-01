"""drop_device_kind

Revision ID: c2616867cef3
Revises: abce9f520f4e
Create Date: 2026-06-01 00:00:00.000000

device_type == "Beacon" is now the sole differentiator.
device_kind column is redundant and is dropped.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c2616867cef3'
down_revision: Union[str, Sequence[str], None] = 'abce9f520f4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('floor_devices', 'device_kind')


def downgrade() -> None:
    op.add_column(
        'floor_devices',
        sa.Column('device_kind', sa.String(length=16), nullable=True),
    )
    # Backfill from device_type
    op.execute("UPDATE floor_devices SET device_kind = 'beacon' WHERE device_type = 'Beacon'")
    op.execute("UPDATE floor_devices SET device_kind = 'vega' WHERE device_kind IS NULL")
    op.alter_column('floor_devices', 'device_kind', nullable=False)

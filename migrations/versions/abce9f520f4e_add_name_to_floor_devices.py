"""add_name_to_floor_devices

Revision ID: abce9f520f4e
Revises: 389ef70adc2e
Create Date: 2026-06-01 00:00:00.000000

The name column was in the ORM model but was never included in any migration.
For existing vega rows we backfill name from uid (the dev_eui) as a placeholder;
the real display name is always fetched live from Vega at query time.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'abce9f520f4e'
down_revision: Union[str, Sequence[str], None] = '389ef70adc2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable first so we can backfill before enforcing NOT NULL
    op.add_column(
        'floor_devices',
        sa.Column('name', sa.String(), nullable=True),
    )
    # Backfill: use uid as a placeholder name for all existing rows
    op.execute("UPDATE floor_devices SET name = uid WHERE name IS NULL")
    # Now enforce NOT NULL
    op.alter_column('floor_devices', 'name', nullable=False)


def downgrade() -> None:
    op.drop_column('floor_devices', 'name')

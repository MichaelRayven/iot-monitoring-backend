from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.models.floor import Floor
from app.models.floor_devices import FloorDevice
from app.models.building import Building
from app.schemas.floor import FloorCreate, FloorUpdate
from app.schemas.floor_device import FloorDeviceCreate, FloorDeviceUpdate


class FloorService:
    """Service layer for floor business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_floor(
        self, floor_id: int, include_devices: bool = False
    ) -> Floor | None:
        """Get a single floor by ID"""

        stmt = select(Floor).where(Floor.id == floor_id)

        if include_devices:
            stmt = stmt.options(selectinload(Floor.devices))

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_floors_by_building(
        self,
        building_id: int,
        skip: int = 0,
        limit: int = 100,
        include_devices: bool = False,
    ) -> list[Floor]:
        """Get all floors for a specific building with pagination"""

        stmt = (
            select(Floor)
            .where(Floor.building_id == building_id)
            .offset(skip)
            .limit(limit)
            .order_by(Floor.id)
        )

        if include_devices:
            stmt = stmt.options(selectinload(Floor.devices))

        result = await self.db.execute(stmt)
        floors = list(result.scalars().all())

        return floors

    async def create_floor(self, floor_data: FloorCreate) -> Floor:
        """Create a new floor"""

        try:
            building = await self.db.get(Building, floor_data.building_id)
            if not building:
                raise ValueError(f"Building with id {floor_data.building_id} not found")

            data = floor_data.model_dump()
            stmt = insert(Floor).values(**data).returning(Floor)

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.scalar_one()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def update_floor(
        self, floor_id: int, floor_data: FloorUpdate
    ) -> Floor | None:
        """Update an existing floor"""
        try:
            floor = await self.get_floor(floor_id)
            if not floor:
                return None

            # Verify building exists if building_id is being updated
            if floor_data.building_id is not None:
                building = await self.db.get(Building, floor_data.building_id)
                if not building:
                    raise ValueError(
                        f"Building with id {floor_data.building_id} not found"
                    )

            data = floor_data.model_dump(exclude_unset=True)
            stmt = (
                update(Floor)
                .where(Floor.id == floor_id)
                .values(**data)
                .returning(Floor)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def delete_floor(self, floor_id: int) -> bool:
        """Delete a floor (cascade will delete associated devices)"""

        try:
            floor = await self.get_floor(floor_id)

            if not floor:
                return False

            stmt = delete(Floor).where(Floor.id == floor_id)
            await self.db.execute(stmt)
            await self.db.commit()

            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def get_floor_devices(
        self,
        floor_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[FloorDevice]:
        """Get all devices for a specific floor"""

        # Verify floor exists
        floor = await self.get_floor(floor_id)
        if not floor:
            raise ValueError(f"Floor with id {floor_id} not found")

        stmt = select(FloorDevice).where(FloorDevice.floor_id == floor_id)

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit).order_by(FloorDevice.id)
        result = await self.db.execute(stmt)
        devices = list(result.scalars().all())

        return devices

    async def add_device_to_floor(
        self, floor_id: int, device_data: FloorDeviceCreate
    ) -> FloorDevice:
        """Add a device to a floor"""

        try:
            # Verify floor exists
            floor = await self.get_floor(floor_id)
            if not floor:
                raise ValueError(f"Floor with id {floor_id} not found")

            # Check unique constraint
            existing_device = await self.db.execute(
                select(FloorDevice).where(FloorDevice.dev_eui == device_data.dev_eui)
            )
            if existing_device.scalar_one_or_none():
                raise ValueError(
                    f"Device with dev_eui {device_data.dev_eui} already exists"
                )

            data = device_data.model_dump()
            stmt = insert(FloorDevice).values(**data).returning(FloorDevice)

            # Create device
            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.scalar_one()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def get_floor_device(self, device_id: int) -> FloorDevice | None:
        """Get a specific device on a floor"""

        result = await self.db.execute(
            select(FloorDevice).where(FloorDevice.id == device_id)
        )
        return result.scalar_one_or_none()

    async def update_floor_device(
        self, device_id: int, device_data: FloorDeviceUpdate
    ) -> FloorDevice | None:
        """Update a device on a floor"""

        try:
            # Verify device exists
            device = await self.get_floor_device(device_id)
            if not device:
                return None

            # Verify floor exists
            if device_data.floor_id is not None:
                floor = await self.get_floor(floor_id=device_data.floor_id)
                if not floor:
                    raise ValueError(f"Floor with id {device_data.floor_id} not found")

            # Update device data
            data = device_data.model_dump(exclude_unset=True)
            stmt = (
                update(FloorDevice)
                .where(FloorDevice.id == device_id)
                .values(**data)
                .returning(FloorDevice)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def delete_floor_device(self, device_id: int) -> bool:
        """Delete a floor device"""

        try:
            device = await self.get_floor_device(device_id)

            if not device:
                return False

            stmt = delete(FloorDevice).where(FloorDevice.id == device_id)
            await self.db.execute(stmt)
            await self.db.commit()

            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

from typing import Optional, List


from sqlalchemy import select, update, insert, delete


from sqlalchemy.ext.asyncio import AsyncSession


from sqlalchemy.orm import selectinload


from app.models.building import Building


from app.schemas.building import BuildingCreate, BuildingUpdate


from sqlalchemy.exc import SQLAlchemyError


class BuildingService:
    def __init__(self, db: AsyncSession):

        self.db = db

    async def get_building(
        self, building_id: int, include_floors: bool = False
    ) -> Optional[Building]:
        """Get a single building by ID"""

        stmt = select(Building).where(Building.id == building_id)

        if include_floors:
            stmt = stmt.options(selectinload(Building.floors))

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_buildings(
        self, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[Building]:
        """Get multiple buildings with pagination and search"""

        stmt = select(Building)

        if search:
            stmt = stmt.where(
                Building.name.ilike(f"%{search}%")
                | Building.address.ilike(f"%{search}%")
            )

        stmt = stmt.offset(skip).limit(limit).order_by(Building.id)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_building(self, building_data: BuildingCreate) -> Building:
        """Create a new building"""

        try:
            data = building_data.model_dump()
            stmt = insert(Building).values(**data).returning(Building)

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.scalar_one()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def update_building(
        self, building_id: int, building_data: BuildingUpdate
    ) -> Optional[Building]:
        """Update an existing building"""
        try:
            building = await self.db.get(Building, building_id)
            if not building:
                return None

            data = building_data.model_dump(exclude_unset=True)
            stmt = (
                update(Building)
                .where(Building.id == building_id)
                .values(**data)
                .returning(Building)
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def delete_building(self, building_id: int) -> bool:
        """Delete a building"""
        try:
            building = await self.get_building(building_id)

            if not building:
                return False

            stmt = delete(Building).where(Building.id == building_id)
            await self.db.execute(stmt)
            await self.db.commit()

            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

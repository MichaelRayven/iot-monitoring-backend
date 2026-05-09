from app.schemas.pagination import PaginationParams
from app.core.deps import BuildingServiceDep
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.building import (
    BuildingCreate,
    BuildingUpdate,
    BuildingResponse,
)

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.post(
    "/",
    response_model=BuildingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new building",
)
async def create_building(service: BuildingServiceDep, building_data: BuildingCreate):
    building = await service.create_building(building_data)
    return building


@router.get(
    "/",
    response_model=List[BuildingResponse],
    summary="Get all buildings with pagination",
)
async def get_buildings(
    service: BuildingServiceDep, pagination: PaginationParams = Depends()
):
    buildings = await service.get_buildings(
        skip=pagination.skip, limit=pagination.limit, search=pagination.search
    )
    return buildings


@router.get(
    "/{building_id}",
    response_model=BuildingResponse,
    summary="Get a specific building by ID",
)
async def get_building(service: BuildingServiceDep, building_id: int):
    building = await service.get_building(building_id)

    if not building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building with ID {building_id} not found",
        )

    return building


@router.put(
    "/{building_id}", response_model=BuildingResponse, summary="Update a building"
)
async def update_building(
    service: BuildingServiceDep, building_id: int, building_data: BuildingUpdate
):
    building = await service.update_building(building_id, building_data)

    if not building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building with ID {building_id} not found",
        )

    return building


@router.delete(
    "/{building_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a building",
)
async def delete_building(service: BuildingServiceDep, building_id: int):
    deleted = await service.delete_building(building_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building with ID {building_id} not found",
        )

    return None

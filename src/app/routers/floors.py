from app.core.deps import AsyncSessionDep, S3StorageDep
from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.floor import Floor
from app.models.floor_devices import FloorDevice
from app.schemas.floor import (
    FloorCreate,
    FloorDeviceCreate,
    FloorDevicePositionUpdate,
    FloorRead,
    FloorUpdate,
)

router = APIRouter(prefix="/floors", tags=["floors"])


@router.post("", response_model=FloorRead)
async def create_floor(payload: FloorCreate, db: AsyncSessionDep):
    floor = Floor(**payload.model_dump())
    db.add(floor)
    await db.commit()
    await db.refresh(floor)
    return floor


@router.get("", response_model=list[FloorRead])
async def list_floors(db: AsyncSessionDep):
    result = await db.execute(select(Floor).options(selectinload(Floor.devices)))
    return result.scalars().all()


@router.get("/{floor_id}", response_model=FloorRead)
async def get_floor(floor_id: int, db: AsyncSessionDep, s3: S3StorageDep):
    result = await db.execute(
        select(Floor).where(Floor.id == floor_id).options(selectinload(Floor.devices))
    )
    floor = result.scalar_one_or_none()

    if floor is None:
        raise HTTPException(status_code=404, detail="Floor not found")

    response = FloorRead.model_validate(floor)
    s3_key = floor.floorplan_s3_key
    if s3_key is not None:
        response.floorplan_url = await s3.get_presigned_url(s3_key)

    return response


@router.patch("/{floor_id}", response_model=FloorRead)
async def update_floor(
    db: AsyncSessionDep,
    floor_id: int,
    payload: FloorUpdate,
):
    floor = await db.get(Floor, floor_id)

    if floor is None:
        raise HTTPException(status_code=404, detail="Floor not found")

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(floor, key, value)

    await db.commit()
    await db.refresh(floor)
    return floor


@router.delete("/{floor_id}")
async def delete_floor(floor_id: int, db: AsyncSessionDep):
    floor = await db.get(Floor, floor_id)

    if floor is None:
        raise HTTPException(status_code=404, detail="Floor not found")

    await db.delete(floor)
    await db.commit()

    return {"status": "ok"}


@router.post("/{floor_id}/floorplan", response_model=FloorRead)
async def upload_floorplan(
    db: AsyncSessionDep,
    s3: S3StorageDep,
    floor_id: int,
    file: UploadFile = File(...),
):
    floor = await db.get(Floor, floor_id)

    if floor is None:
        raise HTTPException(status_code=404, detail="Floor not found")

    key = await s3.upload_floorplan(file)

    floor.floorplan_s3_key = key

    await db.commit()
    await db.refresh(floor)

    return floor


@router.post("/{floor_id}/devices")
async def add_device_to_floor(
    floor_id: int,
    payload: FloorDeviceCreate,
    db: AsyncSessionDep,
):
    floor = await db.get(Floor, floor_id)

    if floor is None:
        raise HTTPException(status_code=404, detail="Floor not found")

    if payload.is_stationary and (payload.x is None or payload.y is None):
        raise HTTPException(
            status_code=422,
            detail="Stationary device must have x and y coordinates",
        )

    floor_device = FloorDevice(
        floor_id=floor_id,
        **payload.model_dump(),
    )

    db.add(floor_device)
    await db.commit()
    await db.refresh(floor_device)

    return floor_device


@router.patch("/{floor_id}/devices/{floor_device_id}/position")
async def update_device_position(
    floor_id: int,
    floor_device_id: int,
    payload: FloorDevicePositionUpdate,
    db: AsyncSessionDep,
):
    result = await db.execute(
        select(FloorDevice).where(
            FloorDevice.id == floor_device_id,
            FloorDevice.floor_id == floor_id,
        )
    )
    floor_device = result.scalar_one_or_none()

    if floor_device is None:
        raise HTTPException(status_code=404, detail="Floor device not found")

    floor_device.x = payload.x
    floor_device.y = payload.y
    floor_device.is_stationary = True

    await db.commit()
    await db.refresh(floor_device)

    return floor_device


@router.delete("/{floor_id}/devices/{floor_device_id}")
async def remove_device_from_floor(
    floor_id: int,
    floor_device_id: int,
    db: AsyncSessionDep,
):
    result = await db.execute(
        select(FloorDevice).where(
            FloorDevice.id == floor_device_id,
            FloorDevice.floor_id == floor_id,
        )
    )
    floor_device = result.scalar_one_or_none()

    if floor_device is None:
        raise HTTPException(status_code=404, detail="Floor device not found")

    await db.delete(floor_device)
    await db.commit()

    return {"status": "ok"}

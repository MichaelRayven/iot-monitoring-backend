from app.schemas.floorplan import FloorplanCreate, FloorplanResponse
from app.core.deps import S3StorageDep
from fastapi import APIRouter

router = APIRouter(prefix="/floorplan", tags=["floors"])


@router.post("/upload", response_model=FloorplanResponse)
async def generate_upload_url(s3_service: S3StorageDep, payload: FloorplanCreate):
    response = s3_service.generate_upload_url(
        file_name=payload.file_name, file_type=payload.file_type
    )

    public_url = s3_service.generate_download_url(response.key)

    return FloorplanResponse(
        upload_url=response.upload_url, key=response.key, public_url=public_url
    )

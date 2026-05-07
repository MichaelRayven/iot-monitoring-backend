from pydantic import BaseModel, Field


class FloorplanCreate(BaseModel):
    file_name: str
    file_type: str


class FloorplanResponse(BaseModel):
    upload_url: str = Field(..., description="Presigned upload url")
    public_url: str = Field(..., description="Presigned download url for the image")
    key: str = Field(..., description="S3 key for the floorplan image")

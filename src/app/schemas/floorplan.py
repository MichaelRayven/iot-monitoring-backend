from pydantic import BaseModel


class FloorplanCreate(BaseModel):
    file_name: str
    file_type: str


class FloorplanResponse(BaseModel):
    upload_url: str
    public_url: str
    key: str

from pydantic import BaseModel


class UploadMeta(BaseModel):
    upload_url: str
    key: str
    file_name: str
    file_type: str
    expires_in: int

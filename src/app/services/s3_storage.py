import uuid
from pathlib import Path

import boto3
from fastapi import UploadFile

from app.core.settings import settings


class S3Storage:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
        )

    async def upload_floorplan(self, file: UploadFile) -> str:
        ext = Path(file.filename or "floorplan.png").suffix or ".png"
        key = f"floorplans/{uuid.uuid4()}{ext}"

        content = await file.read()

        self.client.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=content,
            ContentType=file.content_type or "application/octet-stream",
        )

        return key

    async def get_presigned_url(self, key: str) -> str:
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": key},
            ExpiresIn=60 * 60 * 24 * 7,
        )
        return url

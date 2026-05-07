from app.schemas.s3_storage import UploadMeta
import uuid
from pathlib import Path

import boto3
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

    def generate_download_url(self, key: str, expires_in: int = 24 * 3600) -> str:
        """
        Generate a presigned URL for downloading a file from S3.
        """
        url = self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": settings.s3_bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url

    def generate_upload_url(
        self, file_name: str, file_type: str, expires_in: int = 3600
    ) -> UploadMeta:
        """
        Generate a presigned URL for uploading a file directly to S3.
        """
        # Generate a unique key for the file
        ext = Path(file_name).suffix or ""
        key = f"uploads/{uuid.uuid4()}{ext}"

        # Generate presigned URL for PUT operation
        upload_url = self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.s3_bucket,
                "Key": key,
                "ContentType": file_type,
            },
            ExpiresIn=expires_in,
            HttpMethod="PUT",
        )

        return UploadMeta(
            upload_url=upload_url,
            key=key,
            file_name=file_name,
            file_type=file_type,
            expires_in=expires_in,
        )

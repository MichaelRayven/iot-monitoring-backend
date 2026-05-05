from functools import lru_cache
from app.services.s3_storage import S3Storage
from app.core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import Depends, Request
from app.services.vega_client import VegaClient


def get_vega_service(request: Request) -> VegaClient:
    return request.app.state.vega_client


@lru_cache
def get_s3_service() -> S3Storage:
    return S3Storage()


VegaClientDep = Annotated[VegaClient, Depends(get_vega_service)]
AsyncSessionDep = Annotated[AsyncSession, Depends(get_db)]
S3StorageDep = Annotated[S3Storage, Depends(get_s3_service)]

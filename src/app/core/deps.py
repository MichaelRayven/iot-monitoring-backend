from app.services.floor_service import FloorService
from app.services.building_service import BuildingService
from functools import lru_cache
from app.services.s3_storage import S3Storage
from app.core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import Depends, Request
from app.services.vega_client import VegaClient



from app.services.payload_decoder_service import PayloadDecoderService
from app.services.decoders.smart_wb0101 import SmartWB0101Decoder
from app.services.decoders.smart_ms0101 import SmartMS0101Decoder
from app.services.decoders.smart_badge import SmartBadgeDecoder

@lru_cache
def get_payload_decoder_service() -> PayloadDecoderService:
    service = PayloadDecoderService()
    service.register_strategy("Smart-WB0101", SmartWB0101Decoder())
    service.register_strategy("Smart-MS0101", SmartMS0101Decoder())
    service.register_strategy("Smart Badge", SmartBadgeDecoder())
    return service

def get_vega_service(request: Request) -> VegaClient:
    return request.app.state.vega_client


@lru_cache
def get_s3_service() -> S3Storage:
    return S3Storage()


def get_building_service(db: AsyncSession = Depends(get_db)) -> BuildingService:
    return BuildingService(db)


def get_floor_service(db: AsyncSession = Depends(get_db)) -> FloorService:
    return FloorService(db)


VegaClientDep = Annotated[VegaClient, Depends(get_vega_service)]
AsyncSessionDep = Annotated[AsyncSession, Depends(get_db)]
S3StorageDep = Annotated[S3Storage, Depends(get_s3_service)]
BuildingServiceDep = Annotated[BuildingService, Depends(get_building_service)]
FloorServiceDep = Annotated[FloorService, Depends(get_floor_service)]
PayloadDecoderServiceDep = Annotated[PayloadDecoderService, Depends(get_payload_decoder_service)]

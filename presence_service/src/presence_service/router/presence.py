from fastapi import APIRouter, Depends, status

from presence_service.schemas.presence import (
    AddConnectionRequest,
    DisconnectRequest,
    HeartbeatRequest,
    PresenceStatusesRequest,
    PresenceStatusesResponse,
)
from presence_service.service.presence import PresenceService, get_presence_service


router = APIRouter(
    prefix="/presence",
    tags=["Presence"],
)


@router.post(
    "/connections",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_connection(
    request: AddConnectionRequest,
    service: PresenceService = Depends(get_presence_service),
) -> None:
    return await service.add_connection(request=request)


@router.delete(
    "/disconnect",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def disconnect(
    request: DisconnectRequest,
    service: PresenceService = Depends(get_presence_service),
) -> None:
    return await service.disconnect(request=request)

@router.post(
    "/heartbeat",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def heartbeat(
    request: HeartbeatRequest,
    service: PresenceService = Depends(get_presence_service),
) -> None:
    return await service.heartbeat(request=request)


@router.post(
    "/statuses",
    response_model=PresenceStatusesResponse,
)
async def get_statuses(
    request: PresenceStatusesRequest,
    service: PresenceService = Depends(get_presence_service),
) -> PresenceStatusesResponse:
    return await service.get_statuses(request=request)

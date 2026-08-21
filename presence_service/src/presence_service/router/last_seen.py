from fastapi import APIRouter, Depends

from presence_service.schemas.last_seen import (
    LastSeenRequest,
    LastSeenResponse,
)
from presence_service.service.last_seen import LastSeenService, get_last_seen_service


router = APIRouter(
    prefix="/last-seen",
    tags=["Last Seen"],
)


@router.post(
    "",
    response_model=LastSeenResponse,
)
async def get_last_seen(
    request: LastSeenRequest,
    service: LastSeenService = Depends(get_last_seen_service),
) -> LastSeenResponse:
    return await service.get_last_seen(request=request)

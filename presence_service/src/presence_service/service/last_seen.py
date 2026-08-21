from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from presence_service.db.postgres.db import get_db_session
from presence_service.repository.last_seen import LastSeenRepository
from presence_service.schemas.last_seen import (
    LastSeenRequest,
    LastSeenResponse,
    LastSeenItem,
)


class LastSeenService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = LastSeenRepository(session)

    async def get_last_seen(
        self,
        request: LastSeenRequest,
    ) -> LastSeenResponse:
        ordered_user_ids = sorted(request.user_ids, key=str)
        last_seen_by_user_id = await self._repository.get_last_seen_bulk(
            ordered_user_ids
        )

        return LastSeenResponse(
            last_seen=[
                LastSeenItem(
                    user_id=user_id,
                    last_seen=last_seen_by_user_id.get(user_id),
                )
                for user_id in ordered_user_ids
            ]
        )


def get_last_seen_service(
    session: AsyncSession = Depends(get_db_session),
) -> LastSeenService:
    return LastSeenService(session=session)

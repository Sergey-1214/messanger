
from fastapi import Depends

from presence_service.core.settings import settings
from presence_service.repository.presence import (
    PresenceRepository,
    get_presence_repository,
)
from presence_service.schemas.presence import (
    AddConnectionRequest,
    DisconnectRequest,
)


class PresenceService:
    def __init__(self, repository: PresenceRepository):
        self._repository = repository

    async def add_connection(
        self,
        request: AddConnectionRequest,
    ) -> None:
        result = await self._repository.add_connection(
            user_id=str(request.user_id),
            connection_id=str(request.connection_id),
            ttl_seconds=settings.presence_connection_ttl_seconds,
        )

        if result.status_changed:
            #отправляемв rabbitmq событие
            pass

        return

    async def disconnect(
        self,
        request: DisconnectRequest,
    ) -> None:
        status_changed = await self._repository.disconnect(
            user_id=str(request.user_id),
            connection_id=str(request.connection_id),
        )

        if status_changed:
            #отправляемв rabbitmq событие
            pass

        return 
        


def get_presence_service(
    repository: PresenceRepository = Depends(get_presence_repository),
) -> PresenceService:
    return PresenceService(repository=repository)


from fastapi import Depends

from presence_service.broker.rabbitmq.names import PresenceRoutingKey
from presence_service.broker.rabbitmq.producer import RabbitMQProducer, get_presence_events_producer
from presence_service.core.settings import settings
from presence_service.dto.events.status_events import StatusOfflineEvent, StatusOnlineEvent
from presence_service.exception.presence import ConnectionNotFoundException
from presence_service.repository.presence import (
    PresenceRepository,
    get_presence_repository,
)
from presence_service.schemas.presence import (
    AddConnectionRequest,
    DisconnectRequest,
    HeartbeatRequest,
)


class PresenceService:
    def __init__(self,
        repository: PresenceRepository,
        producer: RabbitMQProducer,
    ):
        self._repository = repository
        self._producer = producer

    async def add_connection(
        self,
        request: AddConnectionRequest,
    ) -> None:
        result = await self._repository.add_connection(
            user_id=str(request.user_id),
            connection_id=request.connection_id,
            ttl_seconds=settings.presence_connection_ttl_seconds,
        )

        if result.status_changed:
            event = StatusOnlineEvent(user_id=request.user_id)
            await self._producer.publish(
                event=event,
                routing_key=PresenceRoutingKey.STATUS_ONLINE,
            )

        return

    async def disconnect(
        self,
        request: DisconnectRequest,
    ) -> None:
        status_changed = await self._repository.disconnect(
            user_id=str(request.user_id),
            connection_id=request.connection_id,
        )

        if status_changed:
            event = StatusOfflineEvent(user_id=request.user_id)
            await self._producer.publish(
                event=event,
                routing_key=PresenceRoutingKey.STATUS_OFFLINE,
            )

        return

    async def heartbeat(
        self,
        request: HeartbeatRequest,
    ) -> None:
        result = await self._repository.heartbeat(
            user_id=str(request.user_id),
            connection_id=request.connection_id,
            ttl_seconds=settings.presence_connection_ttl_seconds,
        )

        match result:
            case result.OK:
                return
            case result.CONNECTION_NOT_FOUND:
                raise ConnectionNotFoundException(detail="Connection not found")


def get_presence_service(
    repository: PresenceRepository = Depends(get_presence_repository),
    producer: RabbitMQProducer = Depends(get_presence_events_producer),
) -> PresenceService:
    return PresenceService(
        repository=repository,
        producer=producer,
    )

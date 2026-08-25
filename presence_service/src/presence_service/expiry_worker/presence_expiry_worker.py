import asyncio
import logging

from redis import RedisError

from presence_service.broker.rabbitmq.names import PresenceRoutingKey
from presence_service.broker.rabbitmq.producer import RabbitMQProducer
from presence_service.dto.events.status_events import StatusOfflineEvent
from presence_service.repository.presence import PresenceRepository

logger = logging.getLogger(__name__)


class PresenceExpiryWorker:
    def __init__(
        self,
        repository: PresenceRepository,
        producer: RabbitMQProducer,
        batch_size: int = 100,
        poll_interval: float = 1,
    ) -> None:
        self._repository = repository
        self._producer = producer
        self._batch_size = batch_size
        self._poll_interval = poll_interval

    async def run(self) -> None:
        while True:
            try:
                offline_entries = (
                    await self._repository.expire_connections(
                        batch_size=self._batch_size,
                    )
                )

                for user_id, occurred_at, version in offline_entries:
                    event = StatusOfflineEvent(
                        user_id=user_id,
                        occurred_at=occurred_at,
                        version=version,
                    )
                    await self._producer.publish(
                        event=event,
                        routing_key=PresenceRoutingKey.STATUS_OFFLINE,
                    )

                if len(offline_entries) < self._batch_size:
                    await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                raise
            except RedisError as e:
                logger.exception("Redis error in presence worker: %s", str(e))
                await asyncio.sleep(self._poll_interval)
            except Exception as e:
                logger.exception("Unexpected presence worker error: %s", str(e))
                await asyncio.sleep(self._poll_interval)


def get_presence_expiry_worker(
    repository: PresenceRepository,
    producer: RabbitMQProducer,
    batch_size: int = 100,
    poll_interval: float = 1,
) -> PresenceExpiryWorker:
    return PresenceExpiryWorker(
        repository=repository,
        producer=producer,
        batch_size=batch_size,
        poll_interval=poll_interval,
    )

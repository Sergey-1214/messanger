import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker

from message_service.broker.rabbitmq.producer import RabbitMQProducer
from message_service.repository.outbox import OutboxRepository


logger = logging.getLogger(__name__)


class OutboxPublisher:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        producer: RabbitMQProducer,
        *,
        poll_interval_seconds: float = 1.0,
        batch_size: int = 100,
        retry_base_seconds: float = 1.0,
        retry_max_seconds: float = 60.0,
    ):
        self._session_factory = session_factory
        self._producer = producer
        self._poll_interval_seconds = poll_interval_seconds
        self._batch_size = batch_size
        self._retry_base_seconds = retry_base_seconds
        self._retry_max_seconds = retry_max_seconds
        self._stop_event = asyncio.Event()

    def stop(self) -> None:
        self._stop_event.set()

    async def publish_next(self) -> bool:
        async with self._session_factory() as session:
            async with session.begin():
                repository = OutboxRepository(session)
                event = await repository.get_next_pending_for_update()
                if event is None:
                    return False

                try:
                    await self._producer.publish_raw(
                        payload=event.payload,
                        event_id=event.id,
                        event_type=event.event_type,
                        correlation_id=event.correlation_id,
                        routing_key=event.routing_key,
                    )
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    repository.mark_failed(
                        event,
                        error,
                        retry_base_seconds=self._retry_base_seconds,
                        retry_max_seconds=self._retry_max_seconds,
                    )
                    logger.warning(
                        "Could not publish outbox event %s (attempt %s): %s",
                        event.id,
                        event.attempts,
                        error,
                    )
                else:
                    repository.mark_published(event)
                    logger.debug("Published outbox event %s", event.id)

                return True

    async def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                for _ in range(self._batch_size):
                    if self._stop_event.is_set():
                        return
                    if not await self.publish_next():
                        break
                else:
                    continue
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Outbox publisher iteration failed")

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._poll_interval_seconds,
                )
            except TimeoutError:
                pass

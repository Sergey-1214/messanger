
import logging

from aio_pika.abc import AbstractIncomingMessage
from pydantic import ValidationError

from realtime_gateway.broker.rabbitmq.event_dispatcher import EventDispatcher


logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(self, dispatcher: EventDispatcher) -> None:
        self._dispatcher = dispatcher

    async def process_message(
        self,
        message: AbstractIncomingMessage,
    ) -> None:
        try:
            await self._dispatcher.dispatch(message)
        except (ValidationError, ValueError) as error:
            logger.warning("Rejecting invalid RabbitMQ event: %s", error)
            await message.reject(requeue=False)
        except Exception:
            logger.exception("RabbitMQ event processing failed; requeueing")
            await message.nack(requeue=True)
        else:
            await message.ack()

def get_rabbit_mq(dispatcher: EventDispatcher):
    return RabbitMQConsumer(dispatcher=dispatcher)

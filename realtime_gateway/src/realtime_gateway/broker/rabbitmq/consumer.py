
from aio_pika.abc import AbstractIncomingMessage

from realtime_gateway.broker.rabbitmq.event_dispatcher import EventDispatcher
from realtime_gateway.dto.events.message_created import MessageCreatedEvent

class RabbitMQConsumer:
    def __init__(self, dispatcher: EventDispatcher) -> None:
        self._dispatcher = dispatcher

    async def process_message(
        self,
        message: AbstractIncomingMessage,
    ) -> None:
        async with message.process(requeue=False):
            await self._dispatcher.dispatch(message)

def get_rabbit_mq(dispatcher: EventDispatcher):
    return RabbitMQConsumer(dispatcher=dispatcher)
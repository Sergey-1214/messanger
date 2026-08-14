

from aio_pika import ExchangeType
from aio_pika.abc import AbstractRobustChannel, AbstractRobustExchange

from realtime_gateway.broker.rabbitmq.names import CHAT_EVENTS_EXCHANGE


async def declare_chat_event_exchange(channel: AbstractRobustChannel) -> AbstractRobustExchange:
    return await channel.declare_exchange(
        name=CHAT_EVENTS_EXCHANGE,
        type=ExchangeType.TOPIC,
        durable=True,
        timeout=5,
    )

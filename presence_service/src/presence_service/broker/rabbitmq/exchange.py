from aio_pika import ExchangeType
from aio_pika.abc import AbstractRobustChannel, AbstractRobustExchange

from presence_service.broker.rabbitmq.names import PRESENCE_EVENTS_EXCHANGE



async def declare_presence_events_exchange(
    channel: AbstractRobustChannel,
) -> AbstractRobustExchange:
    return await channel.declare_exchange(
        name=PRESENCE_EVENTS_EXCHANGE,
        type=ExchangeType.TOPIC,
        durable=True,
        timeout=5.0,
    )



import aio_pika
from aio_pika.abc import AbstractRobustExchange
from fastapi import Request
from pydantic import BaseModel


class RabbitMQProducer:
    def __init__(self, exchange: AbstractRobustExchange):
        self._exchange = exchange

    async def publish(self, event: BaseModel, *, routing_key: str) -> None:
        body = event.model_dump_json().encode("utf-8")

        message = aio_pika.Message(
            body=body,
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=str(event.event_id),
            type=event.event_type,
            correlation_id=(
                str(event.correlation_id)
                if event.correlation_id is not None
                else None
            )
        )

        await self._exchange.publish(
            message=message, 
            routing_key=routing_key, 
            mandatory=True,
            timeout=5.0,
        )

def get_rabbitmq_producer(exchange: AbstractRobustExchange) -> RabbitMQProducer:
    return RabbitMQProducer(exchange=exchange)

def get_presence_events_producer(
    request: Request,
) -> RabbitMQProducer:
    return request.app.state.presence_events_producer

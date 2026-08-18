

import json
from typing import Any
from uuid import UUID

import aio_pika
from aio_pika.abc import AbstractRobustExchange
from pydantic import BaseModel


class RabbitMQProducer:
    def __init__(self, exchange: AbstractRobustExchange):
        self._exchange = exchange

    async def publish(self, event: BaseModel, *, routing_key: str) -> None:
        await self.publish_raw(
            payload=event.model_dump(mode="json"),
            event_id=event.event_id,
            event_type=event.event_type,
            correlation_id=event.correlation_id,
            routing_key=routing_key,
        )

    async def publish_raw(
        self,
        payload: dict[str, Any],
        *,
        event_id: UUID,
        event_type: str,
        correlation_id: UUID | None,
        routing_key: str,
    ) -> None:
        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        message = aio_pika.Message(
            body=body,
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=str(event_id),
            type=event_type,
            correlation_id=(
                str(correlation_id)
                if correlation_id is not None
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

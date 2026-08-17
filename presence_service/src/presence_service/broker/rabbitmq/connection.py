

import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection


class RabbitMqConnection:
    def __init__(self, base_url: str):
        self._base_url = base_url
        self._connection: AbstractRobustConnection | None = None 

    async def connect(self) -> None:
        if self._connection is not None:
            raise RuntimeError(
                "RabbitMQ connection is already initialized"
            )

        self._connection = await aio_pika.connect_robust(
            self._base_url,
            timeout=10,
            client_properties={
                "connection_name": "presence-service"
            }
        )

    async def create_channel(self) -> AbstractRobustChannel:
        if self._connection is None:
            raise RuntimeError(
                "RabbitMQ connection is not initialized"
            )
        return await self._connection.channel(publisher_confirms=True, on_return_raises=True)

    async def close(self) -> None:
        if self._connection is None:
            return None
        
        await self._connection.close()
        self._connection = None 
    

def get_rabbitmq_connection(base_url: str) -> RabbitMqConnection:
    return RabbitMqConnection(base_url=base_url)

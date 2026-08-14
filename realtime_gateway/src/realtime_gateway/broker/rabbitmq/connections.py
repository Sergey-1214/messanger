

from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection

from realtime_gateway.exception.broker_exceptions import RabbitMQException


class RabbitMQConnection:
    def __init__(self, url: str):
        self._url = url
        self._connection: AbstractRobustConnection | None = None

    async def connect(self) -> None:
        if self._connection is not None:
            raise RabbitMQException(detail="Connection already exsist")

        self._connection = await connect_robust(
            url=self._url, 
            timeout=10,
            client_properties={
                "connection_name":"realtime-gateway-consumer",
            }
        )

    async def create_channel(self) -> AbstractRobustChannel:
        if self._connection is None:
            raise RabbitMQException(detail="Connection not initialized")
        
        channel = await self._connection.channel(publisher_confirms=True, on_return_raises=True)
        await channel.set_qos(prefetch_count=50)
        return channel

    async def close(self) -> None:
        if self._connection is None:
            return 

        connection = self._connection
        self._connection = None
        await connection.close()

def get_rabbitmq_connection(url: str):
    return RabbitMQConnection(url=url)
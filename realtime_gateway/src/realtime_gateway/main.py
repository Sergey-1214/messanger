from contextlib import AsyncExitStack, asynccontextmanager
from fastapi import FastAPI

from realtime_gateway.api.websocket import router as websocket_router
from realtime_gateway.broker.rabbitmq.connections import get_rabbitmq_connection
from realtime_gateway.broker.rabbitmq.consumer import RabbitMQConsumer
from realtime_gateway.broker.rabbitmq.event_dispatcher import EventDispatcher
from realtime_gateway.broker.rabbitmq.exchange import (
    declare_chat_event_exchange,
    declare_presence_event_exchange,
)
from realtime_gateway.broker.rabbitmq.queue import (
    declare_chat_event_queue,
    declare_presence_event_queue,
)
from realtime_gateway.clients.message_service import MessageServiceClient
from realtime_gateway.clients.presence_service import PresenceServiceClient
from realtime_gateway.connections.manager import ConnectionManager
from realtime_gateway.core.logging import setup_logging
from realtime_gateway.core.settings import settings
from realtime_gateway.handlers.client_events import ClientEventHandler
from realtime_gateway.handlers.message_events import MessageEventsHandler
from realtime_gateway.handlers.presence_events import PresenceEventsHandler


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        connections = ConnectionManager()
        message_service_client = MessageServiceClient(
            base_url=settings.MESSAGE_SERVICE_URL,
        )
        stack.push_async_callback(message_service_client.close)
        presence_service_client = PresenceServiceClient(
            base_url=settings.PRESENCE_SERVICE_URL,
        )
        stack.push_async_callback(presence_service_client.close)
        broker_connection = get_rabbitmq_connection(settings.rabbitmq_url)
        await broker_connection.connect()
        stack.push_async_callback(broker_connection.close)
        channel = await broker_connection.create_channel()
        exchange = await declare_chat_event_exchange(channel=channel)
        queue = await declare_chat_event_queue(channel=channel, exchange=exchange)
        presence_exchange = await declare_presence_event_exchange(
            channel=channel
        )
        presence_queue = await declare_presence_event_queue(
            channel=channel,
            exchange=presence_exchange,
        )
        message_event_handler = MessageEventsHandler(connections=connections)
        presence_event_handler = PresenceEventsHandler(connections=connections)
        dispatcher = EventDispatcher(
            message_handler=message_event_handler,
            presence_handler=presence_event_handler,
        )
        consumer = RabbitMQConsumer(dispatcher=dispatcher)
        consumer_tag = await queue.consume(
            callback=consumer.process_message,
        )
        stack.push_async_callback(
            queue.cancel,
            consumer_tag,
        )
        presence_consumer_tag = await presence_queue.consume(
            callback=consumer.process_message,
        )
        stack.push_async_callback(
            presence_queue.cancel,
            presence_consumer_tag,
        )

        app.state.connections = connections
        app.state.presence_service_client = presence_service_client
        app.state.client_event_handler = ClientEventHandler(
            message_service_client=message_service_client,
            connections=connections,
        )

        yield


app = FastAPI(lifespan=lifespan)
app.include_router(websocket_router)

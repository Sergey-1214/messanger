from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from realtime_gateway.api.websocket import router as websocket_router
from realtime_gateway.clients.message_service import MessageServiceClient
from realtime_gateway.connections.manager import ConnectionManager
from realtime_gateway.core.logging import setup_logging
from realtime_gateway.core.settings import settings
from realtime_gateway.handlers.client_events import ClientEventHandler


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    connections = ConnectionManager()
    message_service_client = MessageServiceClient(
        base_url=settings.MESSAGE_SERVICE_URL,
    )

    app.state.connections = connections
    app.state.client_event_handler = ClientEventHandler(
        message_service_client=message_service_client,
        connections=connections,
    )

    try:
        yield
    finally:
        await message_service_client.close()


app = FastAPI(lifespan=lifespan)
app.include_router(websocket_router)

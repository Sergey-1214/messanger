from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI


from message_service.broker.rabbitmq.connection import get_rabbitmq_connection
from message_service.broker.rabbitmq.exchanges import declare_chat_events_exchange
from message_service.broker.rabbitmq.producer import get_rabbitmq_producer
from message_service.core.settings import settings
from message_service.db.db import Base, engine
from message_service.exception.chat import BadRequestException, ChatNotFoundException, ForbiddenException, UnauthorizedException
from message_service.exception.handler import bad_request_exception_exception, forbidden_exception_exception, unauthorized_exception, chat_not_found_handler, message_not_found_handler
from message_service.exception.message import MessageNotFoundException
from message_service.router.chat import router as chat_router
from message_service.router.messages import router as messages_router
from message_service.core.logging import setup_logging


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        stack.push_async_callback(engine.dispose)

        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        broker_connection = get_rabbitmq_connection(settings.rabbitmq_url)
        await broker_connection.connect()
        stack.push_async_callback(broker_connection.close)
        channel = await broker_connection.create_channel()
        chat_events_exchange = await declare_chat_events_exchange(channel=channel)
        chat_events_producer = get_rabbitmq_producer(chat_events_exchange)
        app.state.chat_events_producer = chat_events_producer
        yield 
        

app = FastAPI(
    lifespan=lifespan,
)

app.include_router(chat_router)
app.include_router(messages_router)

app.add_exception_handler(UnauthorizedException, unauthorized_exception)
app.add_exception_handler(BadRequestException, bad_request_exception_exception)
app.add_exception_handler(ForbiddenException, forbidden_exception_exception)
app.add_exception_handler(ChatNotFoundException, chat_not_found_handler)
app.add_exception_handler(MessageNotFoundException, message_not_found_handler)

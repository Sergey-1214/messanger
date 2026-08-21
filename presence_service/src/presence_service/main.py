import asyncio
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from presence_service.broker.rabbitmq.connection import get_rabbitmq_connection

from presence_service.broker.rabbitmq.exchange import declare_presence_events_exchange
from presence_service.broker.rabbitmq.producer import get_rabbitmq_producer
from presence_service.core.logging import setup_logging
from presence_service.core.settings import settings
from presence_service.db.postgres.db import async_session_maker, create_all
from presence_service.db.redis import create_redis_client
from presence_service.exception.handler import connection_not_found_handler
from presence_service.exception.presence import ConnectionNotFoundException
from presence_service.expiry_worker.last_seen_consumer import get_last_seen_consumer
from presence_service.expiry_worker.presence_expiry_worker import (
    get_presence_expiry_worker,
)
from presence_service.repository.lua_scripts import PresenceRedisScripts
from presence_service.repository.presence import PresenceRepository
from presence_service.router.last_seen import router as last_seen_router
from presence_service.router.presence import router as presence_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        redis = create_redis_client()
        stack.push_async_callback(redis.aclose)
        await redis.ping()
        app.state.redis = redis
        broker_connection = get_rabbitmq_connection(settings.rabbitmq_url)
        await broker_connection.connect()
        stack.push_async_callback(broker_connection.close)
        channel = await broker_connection.create_channel()
        presence_events_exchange = await declare_presence_events_exchange(channel=channel)
        rabbitmq_producer = get_rabbitmq_producer(presence_events_exchange)
        app.state.presence_events_producer = rabbitmq_producer
        scripts = PresenceRedisScripts(redis)
        repository = PresenceRepository(redis, scripts)
        presence_expiry_worker = get_presence_expiry_worker(
            repository=repository,
            producer=rabbitmq_producer,
        )
        worker_task = asyncio.create_task(presence_expiry_worker.run())

        await create_all()

        last_seen_consumer = get_last_seen_consumer(
            redis,
            async_session_maker,
            settings.last_seen_consumer_name,
        )
        last_seen_consumer_task = asyncio.create_task(last_seen_consumer.run())

        try:
            yield
        finally:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass

            last_seen_consumer_task.cancel()
            try:
                await last_seen_consumer_task
            except asyncio.CancelledError:
                pass


app = FastAPI(lifespan=lifespan)
app.include_router(presence_router)
app.include_router(last_seen_router)


app.add_exception_handler(ConnectionNotFoundException, connection_not_found_handler)

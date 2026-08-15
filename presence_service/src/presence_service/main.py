from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from presence_service.db.redis import create_redis_client
from presence_service.router.presence import router as presence_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        redis = create_redis_client()
        stack.push_async_callback(redis.aclose())
        await redis.ping()
        app.state.redis = redis
        yield



app = FastAPI(lifespan=lifespan)
app.include_router(presence_router)

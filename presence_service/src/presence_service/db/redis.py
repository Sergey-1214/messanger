from fastapi import Request
from redis.asyncio import Redis

from presence_service.core.settings import settings

def create_redis_client() -> Redis:
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=settings.redis_max_connections,
    )


def get_redis(request: Request) -> Redis:
    return request.app.state.redis

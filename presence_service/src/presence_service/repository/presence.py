from time import time
from uuid import UUID

from fastapi import Depends
from redis.asyncio import Redis

from presence_service.db.redis import get_redis
from presence_service.dto.presence import AddConnectionResult


class PresenceRepository:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def add_connection(
        self,
        user_id: str,
        connection_id: str,
        ttl_seconds: int,
    ) -> AddConnectionResult:
        user_key = f"presence:user:{user_id}:connections"
        connection_key = f"presence:connection:{connection_id}"

        now = int(time())
        expires_at = now + ttl_seconds

        async with self._redis.pipeline() as pipe:
            pipe.zremrangebyscore(
                user_key,
                "-inf",
                now,
            )

            pipe.set(
                connection_key,
                str(user_id),
                ex=ttl_seconds,
            )

            pipe.zadd(
                user_key,
                {
                    str(connection_id): expires_at,
                },
            )

            pipe.zcard(user_key)
            _, _, added, count = await pipe.execute()

        status_changed = (count == 1 and added == 1)
            
        return AddConnectionResult(
            status_changed=status_changed,
            active_connections=count,
        )

    async def disconnect(
        self,
        user_id: str,
        connection_id: str,
    ) -> bool:
        user_key = f"presence:user:{user_id}:connections"
        connection_key = f"presence:connection:{connection_id}"

        now = int(time())
        
        async with self._redis.pipeline() as pipe:
            pipe.zremrangebyscore(
                user_key,
                "-inf",
                now,
            )
            pipe.delete(connection_key)

            pipe.zrem(
                user_key,
                connection_id,
            )

            pipe.zcard(user_key)

            removed_ttl, _, removed, count = await pipe.execute()

        status_changed = bool(removed_ttl or removed) and count == 0

        return status_changed


def get_presence_repository(
    redis: Redis = Depends(get_redis),
) -> PresenceRepository:
    return PresenceRepository(redis=redis)

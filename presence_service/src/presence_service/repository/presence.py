from time import time

from fastapi import Depends
from redis.asyncio import Redis

from presence_service.db.redis import get_redis
from presence_service.dto.presence import AddConnectionResult, HeartbeatResult
from presence_service.repository.lua_scripts import PresenceRedisScripts, get_presence_scripts


class PresenceRepository:
    def __init__(self, redis: Redis, scripts: PresenceRedisScripts) -> None:
        self._redis = redis
        self._scripts = scripts

    async def add_connection(
        self,
        user_id: str,
        connection_id: str,
        ttl_seconds: int,
    ) -> AddConnectionResult:
        user_key = f"presence:user:{user_id}:connections"

        now = int(time())
        expires_at = now + ttl_seconds

        async with self._redis.pipeline() as pipe:
            pipe.zremrangebyscore(
                user_key,
                "-inf",
                now,
            )

            pipe.zadd(
                user_key,
                {
                    str(connection_id): expires_at,
                },
            )

            pipe.zcard(user_key)
            _, added, count = await pipe.execute()

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

        now = int(time())
        
        async with self._redis.pipeline() as pipe:
            pipe.zremrangebyscore(
                user_key,
                "-inf",
                now,
            )

            pipe.zrem(
                user_key,
                connection_id,
            )

            pipe.zcard(user_key)

            removed_expired, removed, count = await pipe.execute()

        status_changed = bool(removed_expired or removed) and count == 0

        return status_changed

    async def heartbeat(
        self, 
        user_id: str,
        connection_id: str,
        ttl_seconds: int,
    ) -> HeartbeatResult:
        result = await self._scripts.heartbeat(
            user_id=user_id,
            connection_id=connection_id,
            ttl_seconds=ttl_seconds,
        )

        return HeartbeatResult(result)

def get_presence_repository(
    redis: Redis = Depends(get_redis),
    scripts: PresenceRedisScripts = Depends(get_presence_scripts),
) -> PresenceRepository:
    return PresenceRepository(redis=redis, scripts=scripts)

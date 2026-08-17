from fastapi import Depends
from redis.asyncio import Redis

from presence_service.db.redis import get_redis
from presence_service.dto.presence import AddConnectionResult, HeartbeatResult
from presence_service.repository.lua_scripts import (
    PRESENCE_USERS_NEXT_EXPIRY_KEY,
    PresenceRedisScripts,
    get_presence_scripts,
)


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
        status_changed, active_connections = (
            await self._scripts.add_connection(
                user_id=user_id,
                connection_id=connection_id,
                ttl_seconds=ttl_seconds,
            )
        )

        return AddConnectionResult(
            status_changed=status_changed,
            active_connections=active_connections,
        )

    async def disconnect(
        self,
        user_id: str,
        connection_id: str,
    ) -> bool:
        return await self._scripts.disconnect(
            user_id=user_id,
            connection_id=connection_id,
        )

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

    async def get_statuses(
        self,
        user_ids: list[str],
    ) -> dict[str, bool]:
        if not user_ids:
            return {}

        redis_seconds, _ = await self._redis.time()
        now = int(redis_seconds)

        async with self._redis.pipeline(transaction=False) as pipeline:
            for user_id in user_ids:
                pipeline.zcount(
                    f"presence:user:{user_id}:connections",
                    f"({now}",
                    "+inf",
                )

            active_connection_counts = await pipeline.execute()

        return {
            user_id: int(active_connection_count) > 0
            for user_id, active_connection_count in zip(
                user_ids,
                active_connection_counts,
                strict=True,
            )
        }

    async def expire_connections(
        self,
        batch_size: int = 100,
    ) -> list[str]:
        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero")

        redis_seconds, _ = await self._redis.time()
        now = int(redis_seconds)
        due_user_ids = await self._redis.zrange(
            PRESENCE_USERS_NEXT_EXPIRY_KEY,
            "-inf",
            now,
            byscore=True,
            offset=0,
            num=batch_size,
        )

        offline_user_ids: list[str] = []

        for raw_user_id in due_user_ids:
            user_id = (
                raw_user_id.decode("utf-8")
                if isinstance(raw_user_id, bytes)
                else str(raw_user_id)
            )

            became_offline = await self._scripts.expire_connections(
                user_id=user_id,
            )

            if became_offline:
                offline_user_ids.append(user_id)

        return offline_user_ids


def get_presence_repository(
    redis: Redis = Depends(get_redis),
    scripts: PresenceRedisScripts = Depends(get_presence_scripts),
) -> PresenceRepository:
    return PresenceRepository(redis=redis, scripts=scripts)

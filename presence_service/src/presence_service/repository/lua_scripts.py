from collections.abc import Mapping
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from fastapi import Depends
from redis.asyncio import Redis

from presence_service.db.redis import get_redis


PRESENCE_USERS_NEXT_EXPIRY_KEY = "presence:users:next-expiry"
PRESENCE_LAST_SEEN_STREAM_KEY = "presence:last-seen"
PRESENCE_LAST_SEEN_HASH_KEY = "presence:users:last-seen"


def redis_time_to_datetime(
    seconds: str | int,
    microseconds: str | int,
) -> datetime:
    return datetime.fromtimestamp(
        int(seconds) + int(microseconds) / 1_000_000,
        tz=timezone.utc,
    )


class ScriptName(StrEnum):
    ADD_CONNECTION = "add_connection"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    EXPIRE_CONNECTIONS = "expire_connections"


_ADD_CONNECTION_SCRIPT = """
local redis_time = redis.call("TIME")
local now = tonumber(redis_time[1])
local expires_at = now + tonumber(ARGV[2])

redis.call(
    "ZREMRANGEBYSCORE",
    KEYS[1],
    "-inf",
    now
)

local added = redis.call(
    "ZADD",
    KEYS[1],
    expires_at,
    ARGV[1]
)

local connection_count = redis.call("ZCARD", KEYS[1])
local min_expiry = redis.call(
    "ZRANGE",
    KEYS[1],
    0,
    0,
    "WITHSCORES"
)

redis.call(
    "ZADD",
    KEYS[2],
    min_expiry[2],
    ARGV[3]
)

local status_changed = 0

if connection_count == 1 and added == 1 then
    status_changed = 1
end

return {status_changed, connection_count}
"""


_DISCONNECT_SCRIPT = """
local redis_time = redis.call("TIME")
local now = tonumber(redis_time[1])

local removed_expired = redis.call(
    "ZREMRANGEBYSCORE",
    KEYS[1],
    "-inf",
    now
)

local removed = redis.call(
    "ZREM",
    KEYS[1],
    ARGV[1]
)

local connection_count = redis.call("ZCARD", KEYS[1])
local min_expiry = redis.call(
    "ZRANGE",
    KEYS[1],
    0,
    0,
    "WITHSCORES"
)

if #min_expiry > 0 then
    redis.call(
        "ZADD",
        KEYS[2],
        min_expiry[2],
        ARGV[2]
    )
else
    redis.call("ZREM", KEYS[2], ARGV[2])
end

if (removed_expired > 0 or removed > 0) and connection_count == 0 then
    redis.call(
        "XADD",
        KEYS[3],
        "*",
        "user_id",
        ARGV[2],
        "last_seen_seconds",
        redis_time[1],
        "last_seen_microseconds",
        redis_time[2]
    )
    redis.call(
        "HSET",
        KEYS[4],
        ARGV[2],
        redis_time[1] .. "." .. redis_time[2]
    )
    return {1, redis_time[1], redis_time[2]}
end

return {0, redis_time[1], redis_time[2]}
"""


_HEARTBEAT_SCRIPT = """
local redis_time = redis.call("TIME")
local now = tonumber(redis_time[1])
local expires_at = now + tonumber(ARGV[2])

local current_expiry = redis.call(
    "ZSCORE",
    KEYS[1],
    ARGV[1]
)

if not current_expiry then
    return 0
end

if tonumber(current_expiry) <= now then
    return 0
end

redis.call("ZADD", KEYS[1], expires_at, ARGV[1])

local min_expiry = redis.call(
    "ZRANGE",
    KEYS[1],
    0,
    0,
    "WITHSCORES"
)

redis.call(
    "ZADD",
    KEYS[2],
    min_expiry[2],
    ARGV[3]
)

return 1
"""

_EXPIRE_CONNECTIONS_SCRIPT = """
local redis_time = redis.call("TIME")
local now = tonumber(redis_time[1])

local indexed_expiry = redis.call(
    "ZSCORE",
    KEYS[1],
    ARGV[1]
)

if not indexed_expiry then
    return {0, redis_time[1], redis_time[2]}
end

if tonumber(indexed_expiry) > now then
    return {0, redis_time[1], redis_time[2]}
end

redis.call(
    "ZREMRANGEBYSCORE",
    KEYS[2],
    "-inf",
    now
)

local next_connection = redis.call(
    "ZRANGE",
    KEYS[2],
    0,
    0,
    "WITHSCORES"
)

if #next_connection > 0 then
    redis.call(
        "ZADD",
        KEYS[1],
        next_connection[2],
        ARGV[1]
    )

    return {0, redis_time[1], redis_time[2]}
end

redis.call(
    "ZREM",
    KEYS[1],
    ARGV[1]
)

redis.call(
    "XADD",
    KEYS[3],
    "*",
    "user_id",
    ARGV[1],
    "last_seen_seconds",
    redis_time[1],
    "last_seen_microseconds",
    redis_time[2]
)

redis.call(
    "HSET",
    KEYS[4],
    ARGV[1],
    redis_time[1] .. "." .. redis_time[2]
)

return {1, redis_time[1], redis_time[2]}
"""


_SCRIPT_SOURCES: dict[ScriptName, str] = {
    ScriptName.ADD_CONNECTION: _ADD_CONNECTION_SCRIPT,
    ScriptName.DISCONNECT: _DISCONNECT_SCRIPT,
    ScriptName.HEARTBEAT: _HEARTBEAT_SCRIPT,
    ScriptName.EXPIRE_CONNECTIONS: _EXPIRE_CONNECTIONS_SCRIPT,
}


class PresenceRedisScripts:
    def __init__(
        self,
        redis: Redis,
        script_sources: Mapping[ScriptName, str] | None = None,
    ) -> None:
        sources = (
            _SCRIPT_SOURCES
            if script_sources is None
            else script_sources
        )

        self._scripts = {
            name: redis.register_script(source)
            for name, source in sources.items()
        }

    async def _execute(
        self,
        name: ScriptName,
        *,
        keys: list[str],
        args: list[str | int],
    ) -> Any:
        script = self._scripts[name]
        return await script(keys=keys, args=args)

    async def add_connection(
        self,
        user_id: str,
        connection_id: str,
        ttl_seconds: int,
    ) -> tuple[bool, int]:
        user_key = (
            f"presence:user:{user_id}:connections"
        )

        status_changed, active_connections = await self._execute(
            ScriptName.ADD_CONNECTION,
            keys=[
                user_key,
                PRESENCE_USERS_NEXT_EXPIRY_KEY,
            ],
            args=[
                connection_id,
                ttl_seconds,
                user_id,
            ],
        )

        return status_changed == 1, int(active_connections)

    async def disconnect(
        self,
        user_id: str,
        connection_id: str,
    ) -> tuple[bool, datetime | None]:
        user_key = (
            f"presence:user:{user_id}:connections"
        )

        result = await self._execute(
            ScriptName.DISCONNECT,
            keys=[
                user_key,
                PRESENCE_USERS_NEXT_EXPIRY_KEY,
                PRESENCE_LAST_SEEN_STREAM_KEY,
                PRESENCE_LAST_SEEN_HASH_KEY,
            ],
            args=[
                connection_id,
                user_id,
            ],
        )

        status_changed = result[0] == 1
        occurred_at = (
            redis_time_to_datetime(result[1], result[2])
            if status_changed
            else None
        )

        return status_changed, occurred_at

    async def heartbeat(
        self,
        user_id: str,
        connection_id: str,
        ttl_seconds: int,
    ) -> bool:
        user_key = (
            f"presence:user:{user_id}:connections"
        )

        result = await self._execute(
            ScriptName.HEARTBEAT,
            keys=[
                user_key,
                PRESENCE_USERS_NEXT_EXPIRY_KEY,
            ],
            args=[
                connection_id,
                ttl_seconds,
                user_id,
            ],
        )

        return result == 1

    async def expire_connections(
        self,
        user_id: str,
    ) -> tuple[bool, datetime | None]:
        user_key = (
            f"presence:user:{user_id}:connections"
        )

        result = await self._execute(
            ScriptName.EXPIRE_CONNECTIONS,
            keys=[
                PRESENCE_USERS_NEXT_EXPIRY_KEY,
                user_key,
                PRESENCE_LAST_SEEN_STREAM_KEY,
                PRESENCE_LAST_SEEN_HASH_KEY,
            ],
            args=[
                user_id,
            ],
        )

        status_changed = result[0] == 1
        occurred_at = (
            redis_time_to_datetime(result[1], result[2])
            if status_changed
            else None
        )

        return status_changed, occurred_at


def get_presence_scripts(
    redis: Redis = Depends(get_redis),
) -> PresenceRedisScripts:
    return PresenceRedisScripts(redis=redis)

from time import time

from fastapi import Depends
from redis.asyncio import Redis

from presence_service.db.redis import get_redis


_HEARTBEAT_SCRIPT = """
local current_expiry = redis.call(
    "ZSCORE",
    KEYS[1],
    ARGV[1]
)

if not current_expiry then
    return 0
end

if tonumber(current_expiry) <= tonumber(ARGV[2]) then
    return 0
end

redis.call("ZADD", KEYS[1], ARGV[3], ARGV[1])

return 1
"""


class PresenceRedisScripts:
    def __init__(self, redis: Redis) -> None:
        self._heartbeat = redis.register_script(
            _HEARTBEAT_SCRIPT
        )

    async def heartbeat(
        self,
        user_id: str,
        connection_id: str,
        ttl_seconds: int,
    ) -> bool:
        user_key = (
            f"presence:user:{user_id}:connections"
        )

        now = int(time())
        expires_at = now + ttl_seconds

        result = await self._heartbeat(
            keys=[
                user_key,
            ],
            args=[
                connection_id,
                now,
                expires_at,
            ],
        )

        return result == 1


def get_presence_scripts(
    redis: Redis = Depends(get_redis),
) -> PresenceRedisScripts:
    return PresenceRedisScripts(redis=redis)

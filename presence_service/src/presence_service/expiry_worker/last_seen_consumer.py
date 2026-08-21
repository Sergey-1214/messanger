import asyncio
import logging
from collections.abc import Mapping
from datetime import datetime, timezone
from uuid import UUID

from redis import RedisError
from redis.asyncio import Redis
from redis.exceptions import ResponseError
from sqlalchemy.ext.asyncio import AsyncSession

from presence_service.repository.lua_scripts import (
    PRESENCE_LAST_SEEN_STREAM_KEY,
)
from presence_service.repository.last_seen import LastSeenRepository

logger = logging.getLogger(__name__)

LAST_SEEN_CONSUMER_GROUP = "presence-last-seen-writer"


class LastSeenStreamConsumer:
    def __init__(
        self,
        redis: Redis,
        session_factory,
        consumer_name: str,
        block_ms: int = 3_000,
        batch_size: int = 100,
    ) -> None:
        self._redis = redis
        self._session_factory = session_factory
        self._consumer_name = consumer_name
        self._block_ms = block_ms
        self._batch_size = batch_size

    async def _ensure_group(self) -> None:
        try:
            await self._redis.xgroup_create(
                name=PRESENCE_LAST_SEEN_STREAM_KEY,
                groupname=LAST_SEEN_CONSUMER_GROUP,
                id="0-0",
                mkstream=True,
            )
        except ResponseError as error:
            if "BUSYGROUP" not in str(error):
                raise

    async def _handle_last_seen(self, fields: Mapping[str, str]) -> tuple[UUID, datetime]:
        user_id = UUID(fields["user_id"])
        seconds = int(fields["last_seen_seconds"])
        microseconds = int(fields["last_seen_microseconds"])
        
        timestamp = datetime.fromtimestamp(
            seconds + microseconds / 1_000_000,
            tz=timezone.utc
        )
        
        return user_id, timestamp

    async def _process_messages(self, entries) -> None:
        if not entries:
            return

        parsed_entries = []
        message_ids = []
        
        for message_id, fields in entries:
            try:
                user_id, timestamp = await self._handle_last_seen(fields)
                parsed_entries.append((user_id, timestamp))
                message_ids.append(message_id)
            except (KeyError, ValueError) as e:
                logger.error(
                    "Failed to parse last_seen message %s: %s",
                    message_id,
                    e,
                    exc_info=True
                )
                message_ids.append(message_id)

        if parsed_entries:
            try:
                async with self._session_factory() as session:
                    repository = LastSeenRepository(session)
                    await repository.batch_upsert_last_seen(parsed_entries)
                    logger.info(
                        "Successfully wrote %d last_seen records to database",
                        len(parsed_entries)
                    )
            except Exception as e:
                logger.error(
                    "Failed to write last_seen to database: %s",
                    e,
                    exc_info=True
                )
                
                return

        for message_id in message_ids:
            await self._redis.xack(
                PRESENCE_LAST_SEEN_STREAM_KEY,
                LAST_SEEN_CONSUMER_GROUP,
                message_id,
            )

    async def run(self) -> None:
        await self._ensure_group()

        pending_cursor = "0-0"

        while True:
            try:
                pending_cursor, pending_entries, _ = await self._redis.xautoclaim(
                    name=PRESENCE_LAST_SEEN_STREAM_KEY,
                    groupname=LAST_SEEN_CONSUMER_GROUP,
                    consumername=self._consumer_name,
                    min_idle_time=30_000,
                    start_id=pending_cursor,
                    count=self._batch_size,
                )
                await self._process_messages(pending_entries)

               
                messages = await self._redis.xreadgroup(
                    groupname=LAST_SEEN_CONSUMER_GROUP,
                    consumername=self._consumer_name,
                    streams={PRESENCE_LAST_SEEN_STREAM_KEY: ">"},
                    count=self._batch_size,
                    block=self._block_ms,
                )

                for _, entries in messages:
                    await self._process_messages(entries)
            except asyncio.CancelledError:
                raise
            except ResponseError as error:
                if "NOGROUP" in str(error):
                    logger.warning(
                        "Consumer group %s is missing, recreating it",
                        LAST_SEEN_CONSUMER_GROUP,
                    )
                    try:
                        await self._ensure_group()
                    except RedisError:
                        logger.exception("Failed to recreate consumer group")
                else:
                    logger.exception("Redis response error in last_seen consumer")
                await asyncio.sleep(1)
            except RedisError:
                logger.exception("Redis error in last_seen consumer")
                await asyncio.sleep(1)
            except Exception:
                logger.exception("Unexpected last_seen consumer error")
                await asyncio.sleep(1)


def get_last_seen_consumer(
    redis: Redis,
    session_factory,
    consumer_name: str,
) -> LastSeenStreamConsumer:
    return LastSeenStreamConsumer(
        redis=redis,
        session_factory=session_factory,
        consumer_name=consumer_name,
    )


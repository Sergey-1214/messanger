import asyncio
from collections import defaultdict
import logging
from uuid import UUID, uuid4

from fastapi import WebSocket, WebSocketDisconnect

from realtime_gateway.dto.connection import ManagedConnection

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[
            UUID,
            dict[str, ManagedConnection],
        ] = defaultdict(dict)
        self._presence_subscribers: dict[
            UUID,
            set[tuple[UUID, str]],
        ] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: UUID, websocket: WebSocket) -> str:
        await websocket.accept()
        connection_id = str(uuid4())

        async with self._lock:
            self._connections[user_id][connection_id] = (
                ManagedConnection(websocket=websocket)
            )

        return connection_id

    async def disconnect(self, user_id: UUID, connection_id: str) -> None:
        async with self._lock:
            user_connections = self._connections.get(user_id)
            if user_connections is None:
                return

            connection = user_connections.pop(connection_id, None)
            if connection is None:
                return

            subscriber = (user_id, connection_id)
            for subject_id in connection.presence_subscriptions:
                subscribers = self._presence_subscribers.get(subject_id)
                if subscribers is None:
                    continue
                subscribers.discard(subscriber)
                if not subscribers:
                    self._presence_subscribers.pop(subject_id, None)

            if not user_connections:
                self._connections.pop(user_id, None)

    async def send_to_connection(
        self,
        user_id: UUID,
        connection_id: str,
        event: dict,
    ) -> bool:
        async with self._lock:
            connection = self._connections.get(user_id, {}).get(connection_id)

        if connection is None:
            return False
        
        try:
            async with connection.send_lock:
                async with asyncio.timeout(5):
                    await connection.websocket.send_json(event)

            return True
        except (
            WebSocketDisconnect,
            RuntimeError,
            OSError,
            TimeoutError,
        ):
            logger.warning(
                "Failed to send WebSocket event: "
                "user_id=%s connection_id=%s",
                user_id,
                connection_id,
            )

            await self.disconnect(
                user_id=user_id,
                connection_id=connection_id,
            )
            return False

    async def send_to_user(
        self,
        user_id: UUID,
        event: dict,
    ) -> int:
        async with self._lock:
            connection_ids = tuple(
                self._connections.get(user_id, {})
            )

        results = await asyncio.gather(
            *(
                self.send_to_connection(
                    user_id=user_id,
                    connection_id=connection_id,
                    event=event,
                )
                for connection_id in connection_ids
            )
        )

        return sum(results)

    async def add_presence_subscriptions(
        self,
        user_id: UUID,
        connection_id: str,
        subject_ids: set[UUID],
    ) -> bool:
        async with self._lock:
            connection = self._connections.get(user_id, {}).get(connection_id)
            if connection is None:
                return False

            new_subject_ids = subject_ids - connection.presence_subscriptions
            connection.presence_subscriptions.update(new_subject_ids)
            subscriber = (user_id, connection_id)
            for subject_id in new_subject_ids:
                self._presence_subscribers[subject_id].add(subscriber)
            return True

    async def remove_presence_subscriptions(
        self,
        user_id: UUID,
        connection_id: str,
        subject_ids: set[UUID],
    ) -> bool:
        async with self._lock:
            connection = self._connections.get(user_id, {}).get(connection_id)
            if connection is None:
                return False

            removed_subject_ids = (
                subject_ids & connection.presence_subscriptions
            )
            connection.presence_subscriptions.difference_update(
                removed_subject_ids
            )
            subscriber = (user_id, connection_id)
            for subject_id in removed_subject_ids:
                subscribers = self._presence_subscribers.get(subject_id)
                if subscribers is None:
                    continue
                subscribers.discard(subscriber)
                if not subscribers:
                    self._presence_subscribers.pop(subject_id, None)
            return True

    async def send_to_presence_subscribers(
        self,
        subject_id: UUID,
        event: dict,
    ) -> int:
        async with self._lock:
            subscribers = tuple(self._presence_subscribers.get(subject_id, ()))

        results = await asyncio.gather(
            *(
                self.send_to_connection(
                    user_id=user_id,
                    connection_id=connection_id,
                    event=event,
                )
                for user_id, connection_id in subscribers
            )
        )
        return sum(results)

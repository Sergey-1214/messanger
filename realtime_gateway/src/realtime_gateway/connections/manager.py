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

            user_connections.pop(connection_id, None)
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

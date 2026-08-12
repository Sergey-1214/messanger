import asyncio
from collections import defaultdict
from uuid import UUID, uuid4

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[UUID, dict[str, WebSocket]] = defaultdict(dict)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: UUID, websocket: WebSocket) -> str:
        await websocket.accept()
        connection_id = str(uuid4())

        async with self._lock:
            self._connections[user_id][connection_id] = websocket

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
            websocket = self._connections.get(user_id, {}).get(connection_id)

        if websocket is None:
            return False

        await websocket.send_json(event)
        return True

import asyncio
from dataclasses import dataclass, field
from uuid import UUID

from fastapi import WebSocket


@dataclass(slots=True)
class ManagedConnection:
    websocket: WebSocket
    presence_subscriptions: set[UUID] = field(default_factory=set)
    send_lock: asyncio.Lock = field(
        default_factory=asyncio.Lock,
    )

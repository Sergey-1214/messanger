import asyncio
from dataclasses import dataclass, field

from fastapi import WebSocket


@dataclass(slots=True)
class ManagedConnection:
    websocket: WebSocket
    send_lock: asyncio.Lock = field(
        default_factory=asyncio.Lock,
    )
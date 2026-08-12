from typing import Annotated
from uuid import UUID

from fastapi import Depends, WebSocket, WebSocketException

from realtime_gateway.connections.manager import ConnectionManager
from realtime_gateway.core.security import decode_access_token
from realtime_gateway.core.settings import settings
from realtime_gateway.handlers.client_events import ClientEventHandler


def get_connections(websocket: WebSocket) -> ConnectionManager:
    return websocket.app.state.connections


def get_client_event_handler(websocket: WebSocket) -> ClientEventHandler:
    return websocket.app.state.client_event_handler


def get_current_user_id(websocket: WebSocket) -> UUID:
    authorization = websocket.headers.get("Authorization")
    token: str | None = None

    if authorization:
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() == "bearer" and credentials:
            token = credentials

    token = (
        token
        or websocket.cookies.get("access_token")
    )
    if token is None:
        raise WebSocketException(code=4401, reason="Authentication required")

    if token.lower().startswith("bearer "):
        token = token[7:]

    user_id = decode_access_token(token, settings.SECRET_KEY)
    if user_id is None:
        raise WebSocketException(code=4401, reason="Invalid or expired token")

    return user_id


ConnectionsDep = Annotated[ConnectionManager, Depends(get_connections)]
ClientEventHandlerDep = Annotated[
    ClientEventHandler,
    Depends(get_client_event_handler),
]
CurrentUserIdDep = Annotated[UUID, Depends(get_current_user_id)]

import asyncio
import logging
from contextlib import suppress
from json import JSONDecodeError
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from realtime_gateway.api.dependencies import (
    ClientEventHandlerDep,
    ConnectionsDep,
    CurrentUserIdDep,
    PresenceServiceClientDep,
)
from realtime_gateway.clients.presence_service import (
    PresenceServiceClient,
    PresenceServiceError,
)
from realtime_gateway.core.settings import settings
from realtime_gateway.handlers.client_events import ClientEventError


logger = logging.getLogger(__name__)
router = APIRouter()


async def _heartbeat_presence(
    presence_client: PresenceServiceClient,
    user_id: UUID,
    connection_id: str,
) -> None:
    while True:
        await asyncio.sleep(settings.PRESENCE_HEARTBEAT_INTERVAL_SECONDS)
        try:
            await presence_client.heartbeat(user_id, connection_id)
        except PresenceServiceError as error:
            logger.warning(
                "Presence heartbeat failed: user_id=%s connection_id=%s: %s",
                user_id,
                connection_id,
                error,
            )
            if error.status_code == 404:
                try:
                    await presence_client.add_connection(user_id, connection_id)
                except PresenceServiceError:
                    logger.exception(
                        "Failed to restore presence lease: user_id=%s "
                        "connection_id=%s",
                        user_id,
                        connection_id,
                    )


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: CurrentUserIdDep,
    connections: ConnectionsDep,
    client_event_handler: ClientEventHandlerDep,
    presence_client: PresenceServiceClientDep,
) -> None:
    connection_id: str | None = None
    heartbeat_task: asyncio.Task[None] | None = None

    try:
        connection_id = await connections.connect(
            user_id=user_id,
            websocket=websocket,
        )
        try:
            await presence_client.add_connection(user_id, connection_id)
        except PresenceServiceError:
            logger.exception(
                "Failed to register presence: user_id=%s connection_id=%s",
                user_id,
                connection_id,
            )
        heartbeat_task = asyncio.create_task(
            _heartbeat_presence(presence_client, user_id, connection_id)
        )

        while True:
            try:
                raw_event = await websocket.receive_json()
            except (JSONDecodeError, ValueError):
                await websocket.send_json(
                    {
                        "type": "error",
                        "request_id": None,
                        "payload": {
                            "code": "invalid_json",
                            "message": "A valid JSON event is required",
                        },
                    }
                )
                continue

            try:
                await client_event_handler.handle(
                    user_id=user_id,
                    connection_id=connection_id,
                    raw_event=raw_event,
                )
            except ClientEventError as error:
                await websocket.send_json(
                    {
                        "type": "error",
                        "request_id": (
                            str(error.request_id)
                            if error.request_id is not None
                            else None
                        ),
                        "payload": {
                            "code": error.code,
                            "message": error.message,
                        },
                    }
                )
    except WebSocketDisconnect:
        logger.info(
            "WebSocket disconnected: user_id=%s connection_id=%s",
            user_id,
            connection_id,
        )
    except Exception:
        logger.exception(
            "Unhandled WebSocket error: user_id=%s connection_id=%s",
            user_id,
            connection_id,
        )
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011, reason="Internal server error")
    finally:
        if heartbeat_task is not None:
            heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat_task
        if connection_id is not None:
            await connections.disconnect(
                user_id=user_id,
                connection_id=connection_id,
            )
            try:
                await presence_client.disconnect(user_id, connection_id)
            except PresenceServiceError:
                logger.warning(
                    "Failed to unregister presence: user_id=%s connection_id=%s",
                    user_id,
                    connection_id,
                )

import logging
from json import JSONDecodeError

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from realtime_gateway.api.dependencies import (
    ClientEventHandlerDep,
    ConnectionsDep,
    CurrentUserIdDep,
)
from realtime_gateway.handlers.client_events import ClientEventError


logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: CurrentUserIdDep,
    connections: ConnectionsDep,
    client_event_handler: ClientEventHandlerDep,
) -> None:
    connection_id: str | None = None

    try:
        connection_id = await connections.connect(
            user_id=user_id,
            websocket=websocket,
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
        if connection_id is not None:
            await connections.disconnect(
                user_id=user_id,
                connection_id=connection_id,
            )

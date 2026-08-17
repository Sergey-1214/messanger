from typing import Any
from uuid import UUID

from pydantic import ValidationError

from realtime_gateway.clients.message_service import (
    MessageServiceClient,
    MessageServiceError,
)
from realtime_gateway.connections.manager import ConnectionManager
from realtime_gateway.schemas.websocket import (
    ClientEvent,
    CreateMessagePayload,
    PresenceSubscriptionPayload,
    ServerEvent,
)


class ClientEventError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        request_id: UUID | str | None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.request_id = request_id


class ClientEventHandler:
    def __init__(
        self,
        message_service_client: MessageServiceClient,
        connections: ConnectionManager,
    ) -> None:
        self.message_service_client = message_service_client
        self.connections = connections

    async def handle(
        self,
        user_id: UUID,
        connection_id: str,
        raw_event: Any,
    ) -> None:
        request_id = (
            raw_event.get("request_id")
            if isinstance(raw_event, dict)
            else None
        )
        try:
            event = ClientEvent.model_validate(raw_event)
        except ValidationError as error:
            raise ClientEventError(
                code="invalid_event",
                message="Invalid client event",
                request_id=request_id,
            ) from error

        if event.type == "message.create":
            await self._handle_create_message(user_id, connection_id, event)
            return

        if event.type in {"presence.subscribe", "presence.unsubscribe"}:
            await self._handle_presence_subscription(
                user_id,
                connection_id,
                event,
            )
            return

        raise ClientEventError(
            code="unsupported_event",
            message=f"Unsupported event type: {event.type}",
            request_id=event.request_id,
        )

    async def _handle_create_message(
        self,
        user_id: UUID,
        connection_id: str,
        event: ClientEvent,
    ) -> None:
        try:
            payload = CreateMessagePayload.model_validate(event.payload)
        except ValidationError as error:
            raise ClientEventError(
                code="invalid_payload",
                message="Invalid message.create payload",
                request_id=event.request_id,
            ) from error

        try:
            message = await self.message_service_client.create_message(
                user_id=user_id,
                chat_id=payload.chat_id,
                content=payload.content,
                request_id=event.request_id,
            )
        except MessageServiceError as error:
            raise ClientEventError(
                code=error.code,
                message=error.message,
                request_id=event.request_id,
            ) from error

        accepted_event = ServerEvent(
            type="message.create.accepted",
            request_id=event.request_id,
            payload={"message": message.model_dump(mode="json")},
        )
        await self.connections.send_to_connection(
            user_id=user_id,
            connection_id=connection_id,
            event=accepted_event.model_dump(mode="json"),
        )

    async def _handle_presence_subscription(
        self,
        user_id: UUID,
        connection_id: str,
        event: ClientEvent,
    ) -> None:
        try:
            payload = PresenceSubscriptionPayload.model_validate(event.payload)
        except ValidationError as error:
            raise ClientEventError(
                code="invalid_payload",
                message=f"Invalid {event.type} payload",
                request_id=event.request_id,
            ) from error

        if event.type == "presence.subscribe":
            updated = await self.connections.add_presence_subscriptions(
                user_id=user_id,
                connection_id=connection_id,
                subject_ids=payload.user_ids,
            )
        else:
            updated = await self.connections.remove_presence_subscriptions(
                user_id=user_id,
                connection_id=connection_id,
                subject_ids=payload.user_ids,
            )

        if not updated:
            raise ClientEventError(
                code="connection_not_found",
                message="WebSocket connection is no longer active",
                request_id=event.request_id,
            )

        accepted_event = ServerEvent(
            type=f"{event.type}.accepted",
            request_id=event.request_id,
            payload={
                "user_ids": sorted(str(item) for item in payload.user_ids),
            },
        )
        await self.connections.send_to_connection(
            user_id=user_id,
            connection_id=connection_id,
            event=accepted_event.model_dump(mode="json"),
        )

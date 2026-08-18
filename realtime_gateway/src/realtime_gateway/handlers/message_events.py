import asyncio

from realtime_gateway.connections.manager import ConnectionManager
from realtime_gateway.dto.events.message_created import MessageCreatedEvent, MessageDeletedEvent, MessageUpdatedEvent
from realtime_gateway.schemas.websocket import ServerEvent

class MessageEventsHandler:
    def __init__(self, connections: ConnectionManager):
        self._connections: ConnectionManager  = connections

    async def handle_message_created(self, event: MessageCreatedEvent):
        websocket_event = ServerEvent(
            type="message.created",
            request_id=event.correlation_id,
            payload={
                "message": event.message.model_dump(mode="json"),
            },
        ).model_dump(mode="json")

        await asyncio.gather(
            *(
                self._connections.send_to_user(
                    user_id=participant_id,
                    event=websocket_event,
                )
                for participant_id in set(event.chat_participants)
            )
        )

    async def handle_message_updated(self, event: MessageUpdatedEvent):
        websocket_event = ServerEvent(
            type="message.updated",
            request_id=event.correlation_id,
            payload={
                "message": event.message.model_dump(mode="json"),
            },
        ).model_dump(mode="json")

        await asyncio.gather(
            *(
                self._connections.send_to_user(
                    user_id=participant_id,
                    event=websocket_event,
                )
                for participant_id in set(event.chat_participants)
            )
        )

    async def handle_message_deleted(self, event: MessageDeletedEvent):
        websocket_event = ServerEvent(
            type="message.deleted",
            request_id=event.correlation_id,
            payload={
                "message": event.message.model_dump(mode="json"),
            },
        ).model_dump(mode="json")

        await asyncio.gather(
            *(
                self._connections.send_to_user(
                    user_id=participant_id,
                    event=websocket_event,
                )
                for participant_id in set(event.chat_participants)
            )
        )
    

    
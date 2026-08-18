from realtime_gateway.connections.manager import ConnectionManager
from realtime_gateway.dto.events.presence_status import PresenceStatusEvent
from realtime_gateway.schemas.websocket import ServerEvent


class PresenceEventsHandler:
    def __init__(self, connections: ConnectionManager) -> None:
        self._connections = connections

    async def handle_status_changed(self, event: PresenceStatusEvent) -> None:
        status = event.event_type.rsplit(".", maxsplit=1)[-1]
        websocket_event = ServerEvent(
            type="presence.status.changed",
            request_id=event.correlation_id,
            payload={
                "user_id": event.user_id,
                "status": status,
                "occurred_at": event.occurred_at,
            },
        ).model_dump(mode="json")

        await self._connections.send_to_presence_subscribers(
            subject_id=event.user_id,
            event=websocket_event,
        )

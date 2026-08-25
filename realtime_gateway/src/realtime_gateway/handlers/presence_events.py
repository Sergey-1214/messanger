from uuid import UUID

from realtime_gateway.connections.manager import ConnectionManager
from realtime_gateway.dto.events.presence_status import PresenceStatusEvent
from realtime_gateway.schemas.websocket import ServerEvent


class PresenceEventsHandler:
    def __init__(self, connections: ConnectionManager) -> None:
        self._connections = connections
        self._last_versions: dict[UUID, int] = {}

    async def handle_status_changed(self, event: PresenceStatusEvent) -> None:
        last_version = self._last_versions.get(event.user_id, -1)
        if event.version <= last_version:
            return

        self._last_versions[event.user_id] = event.version

        is_offline = event.event_type.rsplit(".", maxsplit=1)[-1] == "offline"

        websocket_event = ServerEvent(
            type="presence.status.changed",
            request_id=event.correlation_id,
            payload={
                "user_id": event.user_id,
                "status": "offline" if is_offline else "online",
                "occurred_at": event.occurred_at,
                "version": event.version,
                "last_seen": event.occurred_at if is_offline else None,
            },
        ).model_dump(mode="json")

        await self._connections.send_to_presence_subscribers(
            subject_id=event.user_id,
            event=websocket_event,
        )

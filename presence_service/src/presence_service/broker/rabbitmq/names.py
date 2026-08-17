
from enum import StrEnum


PRESENCE_EVENTS_EXCHANGE = "presence.events"

class PresenceRoutingKey(StrEnum):
    STATUS_ONLINE = "presence.status.online"
    STATUS_OFFLINE = "presence.status.offline"
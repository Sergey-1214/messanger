


from enum import StrEnum


CHAT_EVENTS_EXCHANGE = "chat.events"
PRESENCE_EVENTS_EXCHANGE = "presence.events"


class ChatRoutingKey(StrEnum):
    CREATE_MESSAGE = "chat.message.created"
    UPDATE_MESSAGE = "chat.message.updated"
    DELETE_MESSAGE = "chat.message.deleted"


class PresenceRoutingKey(StrEnum):
    STATUS_ONLINE = "presence.status.online"
    STATUS_OFFLINE = "presence.status.offline"

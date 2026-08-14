


from enum import StrEnum


CHAT_EVENTS_EXCHANGE = "chat.events"


class ChatRoutingKey(StrEnum):
    CREATE_MESSAGE = "chat.message.created"
    UPDATE_MESSAGE = "chat.message.updated"
    DELETE_MESSAGE = "chat.message.deleted"
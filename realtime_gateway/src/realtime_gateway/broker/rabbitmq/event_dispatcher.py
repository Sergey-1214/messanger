

from aio_pika.abc import AbstractIncomingMessage

from realtime_gateway.broker.rabbitmq.names import (
    ChatRoutingKey,
    PresenceRoutingKey,
)
from realtime_gateway.dto.events.message_created import MessageCreatedEvent, MessageDeletedEvent, MessageUpdatedEvent
from realtime_gateway.dto.events.presence_status import PresenceStatusEvent
from realtime_gateway.handlers.message_events import MessageEventsHandler
from realtime_gateway.handlers.presence_events import PresenceEventsHandler


class EventDispatcher:
    def __init__(
        self,
        message_handler: MessageEventsHandler,
        presence_handler: PresenceEventsHandler,
    ) -> None:
        self._routes = {
            ChatRoutingKey.CREATE_MESSAGE: (
                MessageCreatedEvent,
                message_handler.handle_message_created,
            ),
            ChatRoutingKey.UPDATE_MESSAGE: (
                MessageUpdatedEvent,
                message_handler.handle_message_updated,
            ),
            ChatRoutingKey.DELETE_MESSAGE: (
                MessageDeletedEvent,
                message_handler.handle_message_deleted,
            ),
            PresenceRoutingKey.STATUS_ONLINE: (
                PresenceStatusEvent,
                presence_handler.handle_status_changed,
            ),
            PresenceRoutingKey.STATUS_OFFLINE: (
                PresenceStatusEvent,
                presence_handler.handle_status_changed,
            ),
        }

    async def dispatch(self, message: AbstractIncomingMessage):
        event_type = message.type

        if event_type is None:
            raise ValueError("AMQP message type is missing")

        route = self._routes.get(event_type)
        if route is None:
            raise ValueError(f"Unsupported event type: {event_type}")

        event_model, handler = route
        event = event_model.model_validate_json(message.body)

        if event.event_type != event_type:
            raise ValueError("AMQP type and body event_type do not match")

        await handler(event=event)

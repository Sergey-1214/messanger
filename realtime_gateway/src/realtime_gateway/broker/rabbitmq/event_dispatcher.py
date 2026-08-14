

from aio_pika.abc import AbstractIncomingMessage

from realtime_gateway.broker.rabbitmq.names import ChatRoutingKey
from realtime_gateway.dto.events.message_created import MessageCreatedEvent
from realtime_gateway.handlers.message_events import MessageEventsHandler


class EventDispatcher:
    def __init__(self, handler: MessageEventsHandler):
        self._routes = {
            ChatRoutingKey.CREATE_MESSAGE: (
                MessageCreatedEvent,
                handler.handle_message_created,
            )
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
        
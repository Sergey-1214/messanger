



from aio_pika.abc import AbstractRobustChannel, AbstractRobustExchange, AbstractRobustQueue



async def declare_chat_event_queue(
    channel: AbstractRobustChannel, 
    exchange: AbstractRobustExchange,
) -> AbstractRobustQueue:
    queue = await channel.declare_queue(
        name=None,
        durable=False, 
        exclusive=True,
        timeout=10
    )

    await queue.bind(
        exchange=exchange,
        routing_key="chat.message.*"
    )

    return queue


    
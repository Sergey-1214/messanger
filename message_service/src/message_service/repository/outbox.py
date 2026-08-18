from datetime import datetime, timedelta, timezone

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from message_service.db.db import get_session
from message_service.models.models import OutboxEvent


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        event: BaseModel,
        *,
        routing_key: str,
    ) -> OutboxEvent:
        outbox_event = OutboxEvent(
            id=event.event_id,
            event_type=event.event_type,
            routing_key=routing_key,
            payload=event.model_dump(mode="json"),
            correlation_id=event.correlation_id,
            occurred_at=event.occurred_at,
        )
        self.session.add(outbox_event)
        await self.session.flush()
        return outbox_event

    async def get_next_pending_for_update(self) -> OutboxEvent | None:
        stmt = (
            select(OutboxEvent)
            .where(
                OutboxEvent.published_at.is_(None),
                OutboxEvent.next_attempt_at <= func.now(),
            )
            .order_by(OutboxEvent.created_at, OutboxEvent.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def mark_published(event: OutboxEvent) -> None:
        event.published_at = datetime.now(timezone.utc)
        event.last_error = None

    @staticmethod
    def mark_failed(
        event: OutboxEvent,
        error: Exception,
        *,
        retry_base_seconds: float,
        retry_max_seconds: float,
    ) -> None:
        delay_seconds = min(
            retry_base_seconds * (2 ** min(event.attempts, 16)),
            retry_max_seconds,
        )
        event.attempts += 1
        event.next_attempt_at = datetime.now(timezone.utc) + timedelta(
            seconds=delay_seconds,
        )
        event.last_error = str(error)[:4000]


async def get_outbox_repository(
    session: AsyncSession = Depends(get_session),
) -> OutboxRepository:
    return OutboxRepository(session=session)

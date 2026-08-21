from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from presence_service.models.last_seen import LastSeen


class LastSeenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_last_seen(
        self,
        user_id: UUID,
        last_seen: datetime,
    ) -> None:
        stmt = insert(LastSeen).values(
            user_id=user_id,
            last_seen=last_seen,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_={
                'last_seen': func.greatest(
                    LastSeen.last_seen,
                    stmt.excluded.last_seen,
                )
            }
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def batch_upsert_last_seen(
        self,
        entries: list[tuple[UUID, datetime]],
    ) -> None:
        if not entries:
            return

        stmt = insert(LastSeen)
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_={
                'last_seen': func.greatest(
                    LastSeen.last_seen,
                    stmt.excluded.last_seen,
                )
            }
        )
        
        values = [
            {'user_id': user_id, 'last_seen': last_seen}
            for user_id, last_seen in entries
        ]
        
        await self._session.execute(stmt, values)
        await self._session.commit()

    async def get_last_seen(self, user_id: UUID) -> Optional[datetime]:
        stmt = select(LastSeen.last_seen).where(LastSeen.user_id == user_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return row

    async def get_last_seen_bulk(
        self,
        user_ids: list[UUID],
    ) -> dict[UUID, datetime]:
        if not user_ids:
            return {}

        stmt = select(LastSeen).where(LastSeen.user_id.in_(user_ids))
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        
        return {
            row.user_id: row.last_seen
            for row in rows
        }

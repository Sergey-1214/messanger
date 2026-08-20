from uuid import UUID

from fastapi import Depends
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.db.db import get_db_session
from user_service.models.settings import Settings
from user_service.models.user import User
from user_service.repository.user import UserRepository



class SettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def init_settings(self, user_id: UUID):
        settings = Settings(user_id=user_id)

        self.session.add(settings)
        await self.session.flush()
        await self.session.refresh(settings)

        return settings

    async def get_user_settings(self, user_id: UUID):
        stmt = select(Settings).join(User).where(User.id == user_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_settings(
        self, 
        user_id: UUID, 
        changes: dict,
    ) -> Settings | None:
        stmt = update(Settings)\
                .values(**changes)\
                .where(Settings.user_id == user_id)\
                .returning(Settings)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def clear_settings(self, user_id: UUID):
        stmt = update(Settings)\
                .where(Settings.user_id == user_id)\
                .values(
                    language=text("DEFAULT"),
                    notification_enabled=text("DEFAULT"),
                    last_seen_visibility=text("DEFAULT"),
                    profile_photo_visibility=text("DEFAULT"),
                ).returning(Settings)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()


def get_settings_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SettingsRepository:
    return SettingsRepository(session=session)
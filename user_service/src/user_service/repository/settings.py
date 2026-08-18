from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.db.db import get_db_session
from user_service.models.settings import Settings
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


def get_settings_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SettingsRepository:
    return SettingsRepository(session=session)
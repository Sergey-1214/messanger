
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.db.db import get_db_session
from user_service.exceptions.user import NoSettingsChangesException, UserNotFoundException
from user_service.repository.settings import SettingsRepository, get_settings_repository
from user_service.schemas.settings import Settings, SettingsUpdateRequest


class SettingsService:
    def __init__(self, 
        session: AsyncSession,
        settings_repository: SettingsRepository,
    ):
        self.session = session
        self.settings_repository = settings_repository

    async def get_settings(self, user_id: UUID) -> Settings:
        settings = await self.settings_repository.get_user_settings(user_id=user_id)

        if not settings:
            raise UserNotFoundException(detail="User and his settings not found")

        return settings

    async def update_settings(self, user_id: UUID, request: SettingsUpdateRequest) -> Settings:
        changes = request.model_dump(exclude_unset=True)
        if not changes:
            raise NoSettingsChangesException()

        settings = await self.settings_repository.update_settings(
            user_id=user_id,
            changes=changes,
        )

        if not settings:
            raise UserNotFoundException(detail="User and his settings not found")

        await self.session.commit()
        return settings


    async def clear_settings(self, user_id: UUID) -> None:
        settings = await self.settings_repository.clear_settings(user_id=user_id)

        if not settings:
            raise UserNotFoundException(detail="User and his settings not found")

        await self.session.commit()


def get_settings_service(
    session: AsyncSession = Depends(get_db_session),
    settings_repository: SettingsRepository = Depends(get_settings_repository),
) -> SettingsService:
    return SettingsService(
        session=session,
        settings_repository=settings_repository,
    )


import logging
from uuid import UUID

from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.db.db import get_db_session
from user_service.exceptions.user import UserAlreadyExistException, UserNotFoundException
from user_service.repository.settings import SettingsRepository, get_settings_repository
from user_service.repository.user import UserRepository, get_user_repository
from user_service.schemas.user import CreateUserRequest, User

logger = logging.getLogger(__name__)

class UserService:
    def __init__(
        self, 
        session: AsyncSession, 
        user_repository: UserRepository,
        settings_repository: SettingsRepository,
    ):
        self.session = session
        self.user_repository = user_repository
        self.settings_repository = settings_repository

    async def create_user(self, request: CreateUserRequest) -> User:
        try:
            user = await self.user_repository.create_user(
                username=request.username, 
                email=request.email, 
                description=request.description,
                first_name=request.first_name,
                second_name=request.second_name,
            )
        except IntegrityError as exc:
            await self.session.rollback()
            raise UserAlreadyExistException(detail="User already exist") from exc

        await self.settings_repository.init_settings(user_id=user.id)

        await self.session.commit()
        return User.model_validate(user)

    async def get_user_by_id(self, user_id: UUID) -> User:
        user = await self.user_repository.get_user_by_id(id=user_id)
        if user is None:
            raise UserNotFoundException(detail="User not found")

        return User.model_validate(user)

    async def get_user_by_username(self, username: str) -> User:
        user = await self.user_repository.get_user_by_username(username=username)
        if user is None:
            raise UserNotFoundException(detail="User not found")

        return User.model_validate(user)
    

def get_user_service(
    session: AsyncSession = Depends(get_db_session),
    user_repository: UserRepository = Depends(get_user_repository),
    settings_repository: SettingsRepository = Depends(get_settings_repository)
) -> UserService:
    return UserService(
        session=session,
        user_repository=user_repository,
        settings_repository=settings_repository,
    )
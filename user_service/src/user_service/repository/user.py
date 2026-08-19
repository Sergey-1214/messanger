from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.db.db import get_db_session
from user_service.models.user import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, username: str, email: str, description: str | None) -> User:
        user = User(username=username, email=email, description=description)

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        return user


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session=session)
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.db.db import get_db_session
from user_service.models.user import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(
        self, 
        username: str, 
        email: str, 
        description: str | None, 
        first_name: str | None,
        second_name: str | None,
    ) -> User:
        user = User(
            username=username,
            email=email, 
            description=description,
            first_name=first_name,
            second_name=second_name,
        )

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def get_user_by_id(self, id: UUID) -> User | None:
        stmt = select(User).where(User.id == id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()



def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session=session)
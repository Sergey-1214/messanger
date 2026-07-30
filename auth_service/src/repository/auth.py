

from datetime import datetime
from typing import Any, AsyncGenerator
import uuid

from fastapi import Depends
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db_session
from src.models.auth import RefreshTokens, User


class AuthRepository:
    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        self.session = session

    async def register(self, username: str, email: str, hashed_password: str) -> User:
        user = User(username=username, email=email, password_hash=hashed_password)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        return user


    async def get_user_by_id(self, id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    

    async def save_refresh_token(self, user_id: uuid.UUID, 
                                 refresh_token_hash: str, expires_at: datetime, **kwargs) -> RefreshTokens:
        refresh_token = RefreshTokens(
            user_id=user_id, 
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )

        self.session.add(refresh_token)
        await self.session.flush()
        await self.session.refresh(refresh_token)

        return refresh_token
    
    async def get_refresh_token(self, refresh_token_hash: str) -> RefreshTokens | None:
        stmt = select(RefreshTokens)\
                .where(
                    RefreshTokens.refresh_token_hash == refresh_token_hash,
                    RefreshTokens.revoked_at.is_(None),
                    RefreshTokens.expires_at > func.now(),
                )
        
        
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()
    
    async def revoked_refresh_token(self, refresh_token_hash: str) -> None:
        stmt = update(RefreshTokens)\
                .where(RefreshTokens.refresh_token_hash == refresh_token_hash)\
                .values(revoked_at=func.now())

        await self.session.execute(stmt)

    async def users_batch(self, users_ids: set[uuid.UUID]) -> list[User]:
        stmt = select(User)\
                .where(User.id.in_(users_ids))

        result = await self.session.execute(stmt)

        return result.scalars().all()


async def get_auth_repository(
        session: AsyncSession = Depends(get_db_session)
) -> AsyncGenerator[AuthRepository, None]:
    yield AuthRepository(session=session)

    


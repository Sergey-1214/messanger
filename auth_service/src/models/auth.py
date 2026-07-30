from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base

class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]

    created_at: Mapped[datetime] = mapped_column(default=func.now())

    refresh_tokens: Mapped[list["RefreshTokens"]] = relationship(
        back_populates="user",
    )

class RefreshTokens(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    refresh_token_hash: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    revoked_at: Mapped[Optional[datetime]]
    expires_at: Mapped[datetime]
    user_agent: Mapped[Optional[str]]
    ip_address: Mapped[Optional[str]]
    
    user: Mapped["User"] = relationship(
        back_populates="refresh_tokens"
    )

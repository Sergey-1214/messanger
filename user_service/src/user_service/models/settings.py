

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from user_service.db.db import Base

if TYPE_CHECKING:
    from user_service.models.user import User


class Settings(Base):
    __tablename__ = "settings"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    language: Mapped[str] = mapped_column(String(35), nullable=False, default="en", server_default="en")
    notification_enabled: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    last_seen_visibility: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    profile_photo_visibility: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), 
            nullable=False,
            server_default=func.now(),
        )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(
        back_populates="settings"
    )
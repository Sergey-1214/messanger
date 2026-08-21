from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from presence_service.db.postgres.db import Base


class LastSeen(Base):
    __tablename__ = "last_seen"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, index=True
    )
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
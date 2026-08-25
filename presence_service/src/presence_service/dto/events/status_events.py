


from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class StatusOnlineEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: Literal["presence.status.online"] = (
        "presence.status.online"
    )
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    user_id: UUID
    version: int

    correlation_id: UUID = Field(default_factory=uuid4)


class StatusOfflineEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: Literal["presence.status.offline"] = (
        "presence.status.offline"
    )
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    user_id: UUID
    version: int

    correlation_id: UUID = Field(default_factory=uuid4)
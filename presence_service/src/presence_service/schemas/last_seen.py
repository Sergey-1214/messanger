from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LastSeenRequest(BaseModel):
    user_ids: set[UUID] = Field(min_length=1, max_length=500)


class LastSeenItem(BaseModel):
    user_id: UUID
    last_seen: datetime | None = None


class LastSeenResponse(BaseModel):
    last_seen: list[LastSeenItem]

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class PresenceStatusEvent(BaseModel):
    event_id: UUID
    event_type: Literal[
        "presence.status.online",
        "presence.status.offline",
    ]
    occurred_at: datetime
    user_id: UUID
    correlation_id: UUID

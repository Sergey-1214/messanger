

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SettingsUpdateRequest(BaseModel):
    language: str = Field("en", min_length=1, max_length=35)
    notification_enabled: bool | None = None
    last_seen_visibility: bool | None = None
    profile_photo_visibility: bool | None = None

class Settings(BaseModel):
    user_id: UUID
    language: str = Field(..., min_length=1, max_length=35)
    notification_enabled: bool
    last_seen_visibility: bool
    profile_photo_visibility: bool 

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

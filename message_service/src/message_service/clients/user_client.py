

import logging
from uuid import UUID

import httpx

from message_service.core.settings import settings
from message_service.domain.user import User

logger = logging.getLogger(__name__)

class UserClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get_users_by_ids(self, user_ids: set[UUID]) -> list[User]:
        if not user_ids:
            return []

        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                f"{self.base_url}/auth/users/batch",
                json={"user_ids": sorted(str(user_id) for user_id in user_ids)},
            )
            response.raise_for_status()
            data = response.json()

        users_data = data["users"] if isinstance(data, dict) else data
        return [User.from_json(user) for user in users_data]

    async def get_user_by_id(self, user_id: UUID) -> User:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                f"{self.base_url}/auth/users/{user_id}"
            )
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, dict):
            raise ValueError("Auth service returned an invalid user response")

        user_data = data.get("user", data)
        if not isinstance(user_data, dict):
            raise ValueError("Auth service returned an invalid user response")
        logger.info(f"user: {user_data}")
        return User.from_json(user_data)

def get_user_client() -> UserClient:
    return UserClient(base_url=settings.auth_service_url.rstrip("/"))



from uuid import UUID

import httpx

from message_service.domain.user import User


class UserClient:
    async def get_users_by_ids(user_ids: set[UUID]) -> list[User]:
        async with httpx.AsyncClient(timeout=5) as client:
            data = await client.get("http://...")
            data = data.json()

            users = []
            for user in data["users"]:
                users.append(User.from_json(user))

            return users


def get_user_client():
    return UserClient()
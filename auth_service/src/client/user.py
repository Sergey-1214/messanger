from typing import Any
from uuid import UUID

import httpx


class UserClientError(Exception):
    pass


class UserClientResponseError(UserClientError):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"User service returned status code {status_code}")
        self.status_code = status_code


class UserClientConnectionError(UserClientError):
    pass


class UserClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def create_user(
        self,
        *,
        user_id: UUID,
        username: str,
        email: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
        ) as client:
            try:
                response = await client.post(
                    "/user/",
                    json={
                        "id": str(user_id),
                        "username": username,
                        "email": email,
                    },
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise UserClientResponseError(
                    status_code=exc.response.status_code,
                ) from exc
            except httpx.RequestError as exc:
                raise UserClientConnectionError(
                    "Could not connect to user service",
                ) from exc

            return response.json()


def get_user_client() -> UserClient:
    return UserClient(base_url="http://user_service:8000", timeout=5.0)

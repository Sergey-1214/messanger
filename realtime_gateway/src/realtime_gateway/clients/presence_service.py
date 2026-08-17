from uuid import UUID

import httpx


class PresenceServiceError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class PresenceServiceClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )

    async def add_connection(self, user_id: UUID, connection_id: str) -> None:
        await self._request(
            "POST",
            "/presence/connections",
            user_id=user_id,
            connection_id=connection_id,
        )

    async def heartbeat(self, user_id: UUID, connection_id: str) -> None:
        await self._request(
            "POST",
            "/presence/heartbeat",
            user_id=user_id,
            connection_id=connection_id,
        )

    async def disconnect(self, user_id: UUID, connection_id: str) -> None:
        await self._request(
            "DELETE",
            "/presence/disconnect",
            user_id=user_id,
            connection_id=connection_id,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        user_id: UUID,
        connection_id: str,
    ) -> None:
        try:
            response = await self._client.request(
                method,
                path,
                json={
                    "user_id": str(user_id),
                    "connection_id": connection_id,
                },
            )
        except httpx.RequestError as error:
            raise PresenceServiceError("Presence service is unavailable") from error

        if response.is_error:
            raise PresenceServiceError(
                f"Presence service returned HTTP {response.status_code}",
                status_code=response.status_code,
            )

    async def close(self) -> None:
        await self._client.aclose()

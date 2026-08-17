

from fastapi import Request, status
from fastapi.responses import JSONResponse

from presence_service.exception.presence import ConnectionNotFoundException


async def connection_not_found_handler(
    request: Request,
    exc: ConnectionNotFoundException,   
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": exc.detail,
        }
    )

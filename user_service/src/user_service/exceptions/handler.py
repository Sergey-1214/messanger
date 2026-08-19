

from fastapi import Request
from fastapi.responses import JSONResponse

from user_service.exceptions.user import UserAlreadyExistException


async def user_already_exist_handler(
    request: Request,
    exc: UserAlreadyExistException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
        },
    )
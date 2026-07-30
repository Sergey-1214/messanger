

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.exceptions.auth import UnauthorizedException, UserAlreadyExistsException, UserNotFoundException


async def user_already_exsists_handler(
    request: Request,
    exc: UserAlreadyExistsException,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "User already exists",
            "code": "user_already_exists"
        }
    )

async def user_not_found_handler(
        request: Request,
        exc: UserNotFoundException,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": "User not fount",
            "code": "user_not_found"
        }
    )

async def unauthorized_handler(
    request: Request,
    exc: UnauthorizedException
):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": "User unauthorized",
            "code": "unauthorized"
        }
    )
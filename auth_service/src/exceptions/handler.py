

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.exceptions.auth import BadRequestException, UnauthorizedException, UserAlreadyExistsException, UserNotFoundException


async def user_already_exsists_handler(
    request: Request,
    exc: UserAlreadyExistsException,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": exc.detail,
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
            "detail": exc.detail,
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
            "detail": exc.detail,
            "code": "unauthorized"
        }
    )

async def bad_request_handler(
        request: Request,
        exc: BadRequestException
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": exc.detail,
            "code": "bad_request"
        }
    )

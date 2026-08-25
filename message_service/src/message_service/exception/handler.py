

from fastapi import Request, status
from fastapi.responses import JSONResponse

from message_service.exception.chat import BadRequestException, ChatAlreadyExistException, ChatNotFoundException, ForbiddenException, UnauthorizedException
from message_service.exception.message import MessageNotFoundException


async def unauthorized_exception(
    request: Request,
    exc: UnauthorizedException,
):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail},
    )

async def chat_not_found_handler(
        request: Request,
        exc: ChatNotFoundException,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail},
    )


async def message_not_found_handler(
    request: Request,
    exc: MessageNotFoundException,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail},
    )

async def bad_request_exception_exception(
    request: Request,
    exc: BadRequestException,
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


async def forbidden_exception_exception(
    request: Request,
    exc: ForbiddenException,
):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.detail},
    )


async def chat_already_exist_exception(
    request: Request,
    exc: ChatAlreadyExistException,
):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.detail}
    )


from fastapi import Request
from fastapi.responses import JSONResponse

from user_service.exceptions.user import NoSettingsChangesException, UserAlreadyExistException, UserNotFoundException


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


async def user_not_found_handler(
    request: Request,
    exc: UserNotFoundException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
        },
    )


async def no_settings_changes_handler(
    request: Request,
    exc: NoSettingsChangesException,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": "No changes provided for update"},
    )
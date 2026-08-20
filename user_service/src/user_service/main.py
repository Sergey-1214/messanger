

from contextlib import asynccontextmanager

from fastapi import FastAPI

from user_service.exceptions.handler import no_settings_changes_handler, user_already_exist_handler, user_not_found_handler
from user_service.exceptions.user import NoSettingsChangesException, UserAlreadyExistException, UserNotFoundException
from user_service.handler.user import router as user_router
from user_service.handler.settings import router as settings_router
from user_service.db.db import Base, dispose_db_engine, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await dispose_db_engine()


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(settings_router)

app.add_exception_handler(UserAlreadyExistException, user_already_exist_handler)
app.add_exception_handler(UserNotFoundException, user_not_found_handler)
app.add_exception_handler(NoSettingsChangesException, no_settings_changes_handler)
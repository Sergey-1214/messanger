

from contextlib import asynccontextmanager

from fastapi import FastAPI

from user_service.exceptions.handler import user_already_exist_handler, user_not_found_handler
from user_service.exceptions.user import UserAlreadyExistException, UserNotFoundException
from user_service.handler.user import router as user_router
from user_service.db.db import Base, dispose_db_engine, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await dispose_db_engine()


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)

app.add_exception_handler(UserAlreadyExistException, user_already_exist_handler)
app.add_exception_handler(UserNotFoundException, user_not_found_handler)
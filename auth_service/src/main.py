from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db.database import engine
from src.handler.auth import auth_router
from src.core.logging import setup_logging
from src.db.database import Base, dispose_db_engine
from src.exceptions.auth import AppException
from src.exceptions.handler import app_exception_handler

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await dispose_db_engine()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.add_exception_handler(AppException, app_exception_handler)

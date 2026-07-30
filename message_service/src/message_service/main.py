from contextlib import asynccontextmanager

from fastapi import FastAPI


from message_service.db.db import Base, engine
from message_service.exception.chat import BadRequestException, ForbiddenException, UnauthorizedException
from message_service.exception.handler import bad_request_exception_exception, forbidden_exception_exception, unauthorized_exception
from message_service.router.chat import router as chat_router

@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield 
    await engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    swagger_ui_parameters={
        "requestInterceptor": lambda req: {
            **req,
            "headers": {
                **req.get("headers", {}),
                "X-Custom-Header": "my-static-value"
            }
        }
    }
)

app.include_router(chat_router)

app.add_exception_handler(UnauthorizedException, unauthorized_exception)
app.add_exception_handler(BadRequestException, bad_request_exception_exception)
app.add_exception_handler(ForbiddenException, forbidden_exception_exception)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from message_service.core.settings import settings


engine = create_async_engine(
    settings.database_url, 
    pool_size=10,
    pool_pre_ping=True,
)

Session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with Session() as session:
        yield session 


class Base(DeclarativeBase):
    pass
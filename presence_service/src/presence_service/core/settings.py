import socket

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = Field(default=50, ge=1)
    presence_connection_ttl_seconds: int = Field(default=60, ge=1)
    rabbitmq_url: str = "amqp://app:app-password@localhost:5672/"
    database_url: str = "postgresql+asyncpg://app:app-password@localhost:5432/presence"
    last_seen_consumer_name: str = Field(
        default_factory=lambda: f"presence-service-{socket.gethostname()}",
        min_length=1,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    auth_service_url: str = "http://auth_service:8000"
    rabbitmq_url: str = "amqp://app:app-password@localhost:5672/"
    outbox_poll_interval_seconds: float = Field(default=1.0, gt=0)
    outbox_batch_size: int = Field(default=100, gt=0)
    outbox_retry_base_seconds: float = Field(default=1.0, gt=0)
    outbox_retry_max_seconds: float = Field(default=60.0, gt=0)

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

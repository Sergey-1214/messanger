from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str
    MESSAGE_SERVICE_URL: str = "http://localhost:8001"
    rabbitmq_url: str = "amqp://app:app-password@localhost:5672/"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

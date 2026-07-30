from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    auth_service_url: str = "http://auth_service:8000"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

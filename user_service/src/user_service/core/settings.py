from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",         
        env_file_encoding="utf-8" 
    )

settings = Settings()
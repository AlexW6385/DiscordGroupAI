import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    app_name: str = "discord_group_ai"
    debug: bool = False

    # Discord Data
    discord_bot_token: str = ""
    discord_client_id: str = ""

    # LLM Auth
    openai_api_key: str = ""

    # Database & Cache
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/discord_bot"
    redis_url: str = "redis://localhost:6379/0"

    # Behavior Settings
    default_proactive_mode: bool = True
    default_message_cooldown: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

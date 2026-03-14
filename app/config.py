from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """唯一配置源：从 .env 或环境变量加载，所有模块统一 from app.config import settings。"""

    # App
    app_name: str = Field(default="discord_group_ai", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")

    # Discord
    discord_bot_token: str = Field(alias="DISCORD_BOT_TOKEN")
    discord_client_id: str = Field(alias="DISCORD_CLIENT_ID")

    # LLM
    openai_api_key: str = Field(alias="OPENAI_API_KEY")

    # Database & Redis
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    # Bot 行为（仅根据阈值决定是否回复）
    response_threshold: float = Field(default=0.5, alias="RESPONSE_THRESHOLD")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True
    )

settings = Settings()

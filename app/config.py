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

    # Bot：是否回复的阈值（priority >= 此值才回复）
    response_threshold: float = Field(default=0.5, alias="RESPONSE_THRESHOLD")

    # 决策模型（是否回复、打分、语气等）
    decision_model: str = Field(default="gpt-4o-mini", alias="DECISION_MODEL")
    decision_temperature: float = Field(default=0.2, alias="DECISION_TEMPERATURE")
    decision_context_messages: int = Field(default=15, alias="DECISION_CONTEXT_MESSAGES")

    # 生成模型（回复内容）
    generation_model: str = Field(default="gpt-4o", alias="GENERATION_MODEL")
    generation_temperature: float = Field(default=0.7, alias="GENERATION_TEMPERATURE")
    generation_context_messages: int = Field(default=30, alias="GENERATION_CONTEXT_MESSAGES")
    generation_min_tokens: int = Field(default=32, alias="GENERATION_MIN_TOKENS")

    # 上下文（Redis 里每个频道保留的条数、过期秒数）
    context_max_history: int = Field(default=40, alias="CONTEXT_MAX_HISTORY")
    context_ttl_seconds: int = Field(default=86400, alias="CONTEXT_TTL_SECONDS")

    # 提示词文件（可选，为空则用代码内默认）
    # 决策提示词内可用占位: {schema} {conversation_log}
    # 生成提示词内可用占位: {conversation_log} {max_words} {tone}
    decision_prompt_file: str = Field(default="", alias="DECISION_PROMPT_FILE")
    generation_prompt_file: str = Field(default="", alias="GENERATION_PROMPT_FILE")

    # 日志目录（所有 logger 只写此目录下文件）
    log_dir: str = Field(default="logs", alias="LOG_DIR")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True
    )

settings = Settings()

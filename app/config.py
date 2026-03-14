from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    全局配置：从 .env 加载。Discord 相关可为空（多 role 时每个 role 在 roles/<role>/config.yaml 里配）。
    """

    # App
    app_name: str = Field(default="discord_group_ai", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")

    # 启用的 role 列表，逗号分隔，如 aggressive,creative。非空时只启动这些 role 的 bot，且每个 role 需有 roles/<name>/config.yaml
    enabled_roles: str = Field(default="", alias="ENABLED_ROLES")

    # LLM
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

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

    # 日志目录（所有 logger 只写此目录下文件）
    log_dir: str = Field(default="logs", alias="LOG_DIR")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()

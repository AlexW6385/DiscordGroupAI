"""
Per-role config: each role has its own folder under roles/<role_name>/.
- roles/<role_name>/config.yaml
- roles/<role_name>/decision.txt
- roles/<role_name>/generation.txt

Config merges with global settings defaults (e.g. decision_model, generation_model).
"""
import os
import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)

# 项目根目录（与 main.py 同层）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROLES_ROOT = PROJECT_ROOT / "app" / "roles"


class RoleConfig(BaseModel):
    """Single role's config. Discord + prompts + threshold; LLM 等未配置则用全局默认。"""
    role_name: str = Field(description="Role id, e.g. aggressive, creative")
    discord_bot_token: str = Field(description="Discord bot token for this role")
    discord_client_id: str = Field(description="Discord application client ID for this role")

    response_threshold: float = Field(default=0.5, description="priority >= this to reply")
    decision_prompt_file: str = Field(default="", description="Path to decision prompt; empty = code default")
    generation_prompt_file: str = Field(default="", description="Path to generation prompt; empty = code default")

    decision_model: str | None = Field(default=None, description="Override global decision model")
    decision_temperature: float | None = Field(default=None, description="Override global decision temperature")
    decision_context_messages: int | None = Field(default=None, description="Override global decision context count")

    generation_model: str | None = Field(default=None, description="Override global generation model")
    generation_temperature: float | None = Field(default=None, description="Override global generation temperature")
    generation_context_messages: int | None = Field(default=None, description="Override global generation context count")
    generation_min_tokens: int | None = Field(default=None, description="Override global generation min tokens")

    def get_decision_model(self) -> str:
        return self.decision_model or getattr(settings, "decision_model", "gpt-4o-mini")

    def get_decision_temperature(self) -> float:
        return self.decision_temperature if self.decision_temperature is not None else getattr(settings, "decision_temperature", 0.2)

    def get_decision_context_messages(self) -> int:
        return self.decision_context_messages if self.decision_context_messages is not None else getattr(settings, "decision_context_messages", 15)

    def get_generation_model(self) -> str:
        return self.generation_model or getattr(settings, "generation_model", "gpt-4o")

    def get_generation_temperature(self) -> float:
        return self.generation_temperature if self.generation_temperature is not None else getattr(settings, "generation_temperature", 0.7)

    def get_generation_context_messages(self) -> int:
        return self.generation_context_messages if self.generation_context_messages is not None else getattr(settings, "generation_context_messages", 30)

    def get_generation_min_tokens(self) -> int:
        return self.generation_min_tokens if self.generation_min_tokens is not None else getattr(settings, "generation_min_tokens", 32)


def _resolve_path(path_str: str, base_dir: Path | None = None) -> str:
    if not path_str:
        return ""
    p = Path(path_str)
    if not p.is_absolute():
        p = (base_dir or PROJECT_ROOT) / p
    return str(p)


def load_role_config(role_name: str) -> RoleConfig | None:
    """
    Load role config from roles/<role_name>/config.yaml.
    Paths in YAML are relative to that role folder unless absolute.
    Returns None if file missing or invalid.
    """
    role_dir = ROLES_ROOT / role_name
    path = role_dir / "config.yaml"
    if not path.is_file():
        logger.warning("Role config not found: %s", path)
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("Failed to load role config %s: %s", path, e)
        return None

    if not data:
        logger.warning("Empty role config: %s", path)
        return None

    data["role_name"] = role_name
    # 默认使用该 role 目录下的 decision.txt / generation.txt，除非 YAML 里显式覆盖
    if not data.get("decision_prompt_file"):
        data["decision_prompt_file"] = str(role_dir / "decision.txt")
    else:
        data["decision_prompt_file"] = _resolve_path(data["decision_prompt_file"], base_dir=role_dir)

    if not data.get("generation_prompt_file"):
        data["generation_prompt_file"] = str(role_dir / "generation.txt")
    else:
        data["generation_prompt_file"] = _resolve_path(data["generation_prompt_file"], base_dir=role_dir)

    try:
        return RoleConfig(**data)
    except Exception as e:
        logger.warning("Invalid role config %s: %s", path, e)
        return None


def get_enabled_role_configs() -> list[RoleConfig]:
    """
    Return list of RoleConfig for each role listed in settings.enabled_roles.
    Skips missing/invalid configs and logs.
    """
    enabled = getattr(settings, "enabled_roles", None) or []
    if isinstance(enabled, str):
        enabled = [s.strip() for s in enabled.split(",") if s.strip()]
    configs: list[RoleConfig] = []
    for name in enabled:
        cfg = load_role_config(name)
        if cfg:
            configs.append(cfg)
        else:
            logger.warning("Skipping role '%s': no valid config", name)
    return configs

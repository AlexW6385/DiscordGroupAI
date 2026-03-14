import json
import logging
import os
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field
from openai import AsyncOpenAI

from app.config import settings

if TYPE_CHECKING:
    from app.role_config import RoleConfig

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=settings.openai_api_key)

DEFAULT_DECISION_PROMPT = """You are the decision engine for a Discord group chat bot. For each turn you must output a priority score from 0.0 to 1.0.

Recent conversation (for context):
{conversation_log}

Scoring rules (use the full range; do NOT cluster at 0.7–0.8):
- 0.0–0.2: No need to reply (greetings to others, off-topic, meme-only, or replying would be noise).
- 0.3–0.4: Weak reason to reply (topic slightly relevant but bot not needed).
- 0.5–0.6: Optional (could add something useful but not necessary).
- 0.7–0.8: Good reason (direct question, or clearly relevant and valuable to chime in).
- 0.9–1.0: Strong reason (explicitly @ the bot, or urgent/clear request for the bot).

Use precise decimals (e.g. 0.25, 0.55, 0.72). Most messages should be in the 0.2–0.5 range; reserve 0.7+ only when the bot is clearly needed. Also set should_respond, mode, tone, max_words. Output JSON exactly matching this schema:
{schema}"""


def _load_decision_system_prompt(conversation_log: str, role_config: "RoleConfig | None" = None) -> str:
    schema = json.dumps(BotDecisionSchema.model_json_schema(), indent=2)
    prompt_file = (role_config.decision_prompt_file if role_config else "") or settings.decision_prompt_file
    if prompt_file and os.path.isfile(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read().strip().format(
                schema=schema,
                conversation_log=conversation_log
            )
    return DEFAULT_DECISION_PROMPT.format(schema=schema, conversation_log=conversation_log)

class BotDecisionSchema(BaseModel):
    should_respond: bool = Field(description="Whether the bot should respond to the current context.")
    priority: float = Field(description="Priority of responding, from 0.0 to 1.0.")
    mode: str = Field(description="Mode of response: 'reply', 'interject', 'ignore'")
    reason: str = Field(description="Internal reasoning for this decision.", default="")
    target_message_id: str | None = Field(default=None, description="The ID of the message to reply to, if applicable.")
    tone: str = Field(description="Tone to use for the response, e.g., 'helpful', 'concise', 'witty'.")
    max_words: int = Field(description="Suggested maximum word count for the response.", default=15)

async def decide_to_speak(
    context: list[dict], bot_id: int, role_config: "RoleConfig | None" = None
) -> BotDecisionSchema:
    """
    Uses a small/fast LLM to decide if the bot should speak.
    When role_config is provided, uses its prompt file and model params; else uses global settings.
    """
    n = role_config.get_decision_context_messages() if role_config else settings.decision_context_messages
    conversation_log = ""
    for msg in context[-n:]:
        user = msg.get("username")
        content = msg.get("content")
        is_bot = msg.get("is_bot", False)
        role_label = "[Bot]" if is_bot else "[Human]"
        conversation_log += f"{role_label} {user}: {content}\n"

    system_prompt = _load_decision_system_prompt(conversation_log, role_config)
    raw = ""

    try:
        model = role_config.get_decision_model() if role_config else settings.decision_model
        temp = role_config.get_decision_temperature() if role_config else settings.decision_temperature
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Recent conversation:\n{conversation_log}\n\nYour decision (JSON):"}
            ],
            response_format={"type": "json_object"},
            temperature=temp,
        )

        raw = (response.choices[0].message.content or "").strip()
        # 从可能带前后文的文本里抽出 JSON（模型有时会加 "Here is..." 等）
        if "```json" in raw:
            result_json = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            result_json = raw.split("```")[1].strip()
        else:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                result_json = raw[start : end + 1]
            else:
                result_json = raw

        data = json.loads(result_json)
        # 模型有时会包在 "properties" 里，需要解开
        if isinstance(data.get("properties"), dict):
            data = data["properties"]
        decision_result = BotDecisionSchema(**data)
        logger.info(
            "决策输入(共%d条): %s | 输出: priority=%.2f should_respond=%s reason=%s",
            len(context[-n:]),
            conversation_log.strip().replace("\n", " ")[:300],
            decision_result.priority,
            decision_result.should_respond,
            (decision_result.reason or "")[:80],
        )
        return decision_result
    except Exception as e:
        logger.warning("Error parsing decision JSON: %s | raw: %s", e, raw[:500] if raw else "(empty)")
        # Default to safe "no response" if it fails
        return BotDecisionSchema(
            should_respond=False,
            priority=0.0,
            mode="ignore",
            reason=f"Failed to parse LLM output: {e}",
            tone="neutral",
            max_words=0
        )

import os
import re
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

from app.config import settings

if TYPE_CHECKING:
    from app.role_config import RoleConfig

client = AsyncOpenAI(api_key=settings.openai_api_key)

DEFAULT_GENERATION_PROMPT = """You are a natural, socially aware member of a Discord group chat. You are joining the conversation.
Keep your response brief and casual. Target ~{max_words} words. Tone: {tone}.
Address participants by their usernames in the log. Be a peer, not an AI assistant.

Recent conversation (for context only; do not copy this format):
{conversation_log}

Output ONLY the plain reply text you would send. Do NOT include timestamps, your username, labels, or any prefix like "[date]" or "GroupChatAgent:". Just the message content only."""


def _load_generation_system_prompt(
    conversation_log: str, tone: str, max_words: int, role_config: "RoleConfig | None" = None
) -> str:
    prompt_file = (role_config.generation_prompt_file if role_config else "") or settings.generation_prompt_file
    if prompt_file and os.path.isfile(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read().strip().format(
                conversation_log=conversation_log,
                max_words=max_words,
                tone=tone,
            )
    return DEFAULT_GENERATION_PROMPT.format(
        conversation_log=conversation_log,
        max_words=max_words,
        tone=tone,
    )

async def generate_response(
    context: list[dict], tone: str, max_words: int, role_config: "RoleConfig | None" = None
) -> str:
    """
    Generates the actual response using the LLM. When role_config is provided, uses its prompt and model params.
    """
    n = role_config.get_generation_context_messages() if role_config else settings.generation_context_messages
    conversation_log = ""
    for msg in context[-n:]:
        user = msg.get("username")
        content = msg.get("content")
        conversation_log += f"[{msg.get('timestamp')}] {user}: {content}\n"

    system_prompt = _load_generation_system_prompt(conversation_log, tone, max_words, role_config)

    model = role_config.get_generation_model() if role_config else settings.generation_model
    temp = role_config.get_generation_temperature() if role_config else settings.generation_temperature
    min_tok = role_config.get_generation_min_tokens() if role_config else settings.generation_min_tokens
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}],
        temperature=temp,
        max_tokens=max(max_words * 2, min_tok),
    )

    text = response.choices[0].message.content.strip()
    # 去掉模型可能带上的 [时间] 用户名: 前缀，只保留纯回复
    prefix = re.match(r"^\[\d{4}[^\]]*\]\s*\S+:\s*", text)
    if prefix:
        text = text[prefix.end() :].strip()
    return text

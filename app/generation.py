import os
import re
from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)

DEFAULT_GENERATION_PROMPT = """You are a natural, socially aware member of a Discord group chat. You are joining the conversation.
Keep your response brief and casual. Target ~{max_words} words. Tone: {tone}.
Address participants by their usernames in the log. Be a peer, not an AI assistant.

Recent conversation (for context only; do not copy this format):
{conversation_log}

Output ONLY the plain reply text you would send. Do NOT include timestamps, your username, labels, or any prefix like "[date]" or "GroupChatAgent:". Just the message content only."""


def _load_generation_system_prompt(conversation_log: str, tone: str, max_words: int) -> str:
    if settings.generation_prompt_file and os.path.isfile(settings.generation_prompt_file):
        with open(settings.generation_prompt_file, "r", encoding="utf-8") as f:
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

async def generate_response(context: list[dict], tone: str, max_words: int) -> str:
    """
    Generates the actual response using the LLM based on the context and decision parameters.
    """
    n = settings.generation_context_messages
    conversation_log = ""
    for msg in context[-n:]:
        user = msg.get("username")
        content = msg.get("content")
        conversation_log += f"[{msg.get('timestamp')}] {user}: {content}\n"

    system_prompt = _load_generation_system_prompt(conversation_log, tone, max_words)

    response = await client.chat.completions.create(
        model=settings.generation_model,
        messages=[{"role": "system", "content": system_prompt}],
        temperature=settings.generation_temperature,
        max_tokens=max(max_words * 2, settings.generation_min_tokens),
    )

    text = response.choices[0].message.content.strip()
    # 去掉模型可能带上的 [时间] 用户名: 前缀，只保留纯回复
    prefix = re.match(r"^\[\d{4}[^\]]*\]\s*\S+:\s*", text)
    if prefix:
        text = text[prefix.end() :].strip()
    return text

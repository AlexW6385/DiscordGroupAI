from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)

async def generate_response(context: list[dict], tone: str, max_words: int) -> str:
    """
    Generates the actual response using the LLM based on the context and decision parameters.
    """
    conversation_log = ""
    for msg in context[-30:]: # Use up to last 30 messages for full context
        user = msg.get("username")
        content = msg.get("content")
        conversation_log += f"[{msg.get('timestamp')}] {user}: {content}\n"

    system_prompt = f"""You are a natural, socially aware member of a Discord group chat. 
You are joining the conversation.

Instructions:
- Keep your response brief and casual. 
- Target word count: ~{max_words} words.
- Tone: {tone}.
- If you are replying to someone, acknowledge their context but don't feel forced to use their name every time.
- Address the participants correctly based on their usernames in the log.
- Do NOT act like an AI assistant. Be a peer.

Here is the recent conversation:
{conversation_log}

Generate your response directly:"""

    response = await client.chat.completions.create(
        model="gpt-4o", # Better model for generation
        messages=[
            {"role": "system", "content": system_prompt}
        ],
        temperature=0.7,
        max_tokens=max_words * 2 # rough token estimation
    )

    return response.choices[0].message.content.strip()

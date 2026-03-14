import json
import logging
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=settings.openai_api_key)

class BotDecisionSchema(BaseModel):
    should_respond: bool = Field(description="Whether the bot should respond to the current context.")
    priority: float = Field(description="Priority of responding, from 0.0 to 1.0.")
    mode: str = Field(description="Mode of response: 'reply', 'interject', 'ignore'")
    reason: str = Field(description="Internal reasoning for this decision.", default="")
    target_message_id: str | None = Field(default=None, description="The ID of the message to reply to, if applicable.")
    tone: str = Field(description="Tone to use for the response, e.g., 'helpful', 'concise', 'witty'.")
    max_words: int = Field(description="Suggested maximum word count for the response.", default=50)

async def decide_to_speak(context: list[dict], bot_id: int) -> BotDecisionSchema:
    """
    Uses a small/fast LLM to decide if the bot should speak.
    """
    # Build a lightweight prompt of recent activity
    conversation_log = ""
    for msg in context[-15:]: # Only use the last 15 messages for decision to save tokens
        user = msg.get("username")
        content = msg.get("content")
        conversation_log += f"{user}: {content}\n"

    system_prompt = f"""You are the decision engine for an autonomous Discord group chat bot.
Your goal is to decide whether the bot should participate in the conversation.
You want to behave like a natural, slightly introverted group member:
- Don't respond to every single message.
- Score priority high (0.8-1.0) when: directly addressed/tagged, or a clear question to you, or your reply would add real value.
- Score priority medium (0.5-0.7) when: someone says hi/greeting to the group (you may say hi back), or the topic is interesting.
- Score priority low (0.0-0.4) only for: pure memes, off-topic spam, or when replying would be clearly redundant.
- If the last message is a simple greeting or "are you there" and you have not spoken recently, prefer replying (priority at least 0.5).
- Minimize token usage by keeping responses brief.

Review the recent conversation log and output your decision in JSON format EXACTLY matching the following JSON schema:
{json.dumps(BotDecisionSchema.model_json_schema(), indent=2)}
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini", # Fast model for decisions
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Recent Conversation:\n{conversation_log}\n\nDecision:"}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        result_json = response.choices[0].message.content.strip()
        
        # Safely extract JSON if the LLM output is wrapped in ```json ... ```
        if "```json" in result_json:
            result_json = result_json.split("```json")[1].split("```")[0].strip()
        elif "```" in result_json:
            result_json = result_json.split("```")[1].strip()

        data = json.loads(result_json)
        return BotDecisionSchema(**data)
    except Exception as e:
        logger.warning("Error parsing decision JSON: %s", e)
        # Default to safe "no response" if it fails
        return BotDecisionSchema(
            should_respond=False,
            priority=0.0,
            mode="ignore",
            reason=f"Failed to parse LLM output: {e}",
            tone="neutral",
            max_words=0
        )

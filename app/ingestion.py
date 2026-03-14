import re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import MessageRecord
from app.context import context_manager

def clean_message_content(content: str) -> str:
    """
    Strips extra whitespace or unnecessary discord syntax before processing.
    """
    content = content.replace('\u200b', '') # Remove zero-width spaces
    content = re.sub(r'<a?:.+?:\d+>', '', content) # Remove custom emojis but maybe keep the name if needed (simplified here)
    return content.strip()

async def ingest_message(
    session: AsyncSession,
    guild_id: int,
    channel_id: int,
    message_id: int,
    user_id: int,
    username: str,
    raw_content: str,
    is_bot: bool,
    created_at: datetime
):
    """
    Stores the message in the DB and updates the short-term Redis context.
    """
    cleaned_content = clean_message_content(raw_content)
    
    # 1. Save to database for long-term analytics/RAG
    msg_record = MessageRecord(
        message_id=message_id,
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
        username=username,
        raw_content=raw_content,
        cleaned_content=cleaned_content,
        is_bot=is_bot,
        created_at=created_at
    )
    session.add(msg_record)
    await session.commit()
    
    # 2. Add to Redis context
    await context_manager.add_message(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id,
        username=username,
        content=cleaned_content,
        is_bot=is_bot
    )
    
    return msg_record

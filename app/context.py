import json
from datetime import datetime
from app.redis_client import redis_client

class ContextManager:
    """Manages the short-term memory of a channel in Redis."""
    
    def __init__(self, max_history: int = 40):
        self.max_history = max_history

    def _get_key(self, channel_id: int) -> str:
        return f"channel_context:{channel_id}"

    async def add_message(
        self, 
        channel_id: int, 
        message_id: int, 
        user_id: int, 
        username: str, 
        content: str, 
        is_bot: bool
    ):
        """Append a message to the channel's recent context."""
        key = self._get_key(channel_id)
        msg_data = {
            "message_id": message_id,
            "user_id": user_id,
            "username": username,
            "content": content,
            "is_bot": is_bot,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # We use a Redis List for simplicity. RPUSH adds to end, LTRIM keeps it bounded.
        await redis_client.rpush(key, json.dumps(msg_data))
        await redis_client.ltrim(key, -self.max_history, -1)
        
        # Set expiration to 24 hours so inactive channels don't bloat Redis
        await redis_client.expire(key, 86400)

    async def get_context(self, channel_id: int) -> list[dict]:
        """Retrieve the recent messages for a channel."""
        key = self._get_key(channel_id)
        raw_msgs = await redis_client.lrange(key, 0, -1)
        return [json.loads(m) for m in raw_msgs]

    async def clear_context(self, channel_id: int):
        """Clear the context for a channel (e.g., admin command)."""
        key = self._get_key(channel_id)
        await redis_client.delete(key)

context_manager = ContextManager()

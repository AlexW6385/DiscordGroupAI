from redis.asyncio import Redis
from app.config import settings

# Create an async redis client
redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True
)

async def get_redis() -> Redis:
    """Dependency to get the redis connection"""
    return redis_client

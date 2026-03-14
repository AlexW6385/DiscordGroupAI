import asyncio
import logging
import os
import uvicorn
from app.config import settings
from app.discord_bot.bot import bot
from app.api.server import app as fastapi_app
from app.redis_client import redis_client

# 所有日志只写文件，控制台不输出（控制台仅由 bot 打印 内容|分数|回复）
log_dir = settings.log_dir
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "discord_bot.log")
_file_handler = logging.FileHandler(log_file, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().handlers.clear()
logging.getLogger().addHandler(_file_handler)

logger = logging.getLogger(__name__)

async def run_fastapi():
    """Run FastAPI app using Uvicorn."""
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    # Disable uvicorn signal handlers so they don't conflict with discord.py
    await server.serve()

async def run_discord_bot():
    """Run the Discord Bot."""
    # Ensure bot loads the admin cog
    await bot.load_extension("app.discord_bot.admin")
    
    # Sync slash commands with Discord
    @bot.event
    async def on_ready():
        await bot.tree.sync()
        logger.debug(f"Bot is ready! Logged in as {bot.user}")

    # Start the bot
    await bot.start(settings.discord_bot_token)

async def main():
    if not settings.discord_bot_token:
        logger.error("No DISCORD_BOT_TOKEN provided in environment / .env file.")
        return
        
    if not settings.openai_api_key:
        logger.warning("No OPENAI_API_KEY provided. Generation will fail.")
        
    logger.info("Starting Discord Group AI services...")
    logger.info(f"阈值={settings.response_threshold}")

    try:
        await redis_client.flushall()
        logger.debug("Redis cache flushed on startup.")
    except Exception as e:
        logger.warning(f"Failed to flush Redis cache: {e}")
    
    # Run both the Discord Bot and FastAPI server concurrently
    # The trick here is discord.py wants to own the event loop signals
    fastapi_task = asyncio.create_task(run_fastapi())
    try:
        await run_discord_bot()
    finally:
        fastapi_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")

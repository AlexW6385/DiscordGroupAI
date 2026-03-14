import asyncio
import logging
import os
import uvicorn
import argparse
from pathlib import Path

from app.config import settings
from app.discord_bot.bot import create_bot
from app.role_config import get_enabled_role_configs
from app.api.server import app as fastapi_app
from app.redis_client import redis_client

log_dir = getattr(settings, "log_dir", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "discord_bot.log")
_file_handler = logging.FileHandler(log_file, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().handlers.clear()
logging.getLogger().addHandler(_file_handler)

logger = logging.getLogger(__name__)


async def run_fastapi(port: int):
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def run_bot_with_config(role_config):
    bot = create_bot(role_config)
    # Check if admin extension exists before loading
    admin_path = Path(__file__).parent / "app" / "discord_bot" / "admin.py"
    if admin_path.exists():
        await bot.load_extension("app.discord_bot.admin")
    await bot.start(role_config.discord_bot_token)


def list_available_roles():
    roles_dir = Path(__file__).parent / "app" / "roles"
    if not roles_dir.exists():
        print("No roles directory found at app/roles")
        return
    roles = [d.name for d in roles_dir.iterdir() if d.is_dir() and (d / "config.yaml").exists()]
    if not roles:
        print("No valid roles found in app/roles")
    else:
        print("Available roles:")
        for role in roles:
            print(f"  - {role}")


async def main():
    parser = argparse.ArgumentParser(description="Discord Group AI Bot Runner")
    parser.add_argument("-r", "--roles", help="Comma-separated list of roles to enable (overrides .env)")
    parser.add_argument("-l", "--list-roles", action="store_true", help="List available roles and exit")
    parser.add_argument("-p", "--port", type=int, default=8000, help="API server port (default: 8000)")
    args = parser.parse_args()

    if args.list_roles:
        list_available_roles()
        return

    if args.roles:
        settings.enabled_roles = args.roles
        logger.info("Roles overridden by CLI: %s", args.roles)

    enabled = (getattr(settings, "enabled_roles", "") or "").strip()
    if not enabled:
        # If no roles specified, don't start any bot, just print available roles
        print("No roles enabled via ENABLED_ROLES or --roles.")
        list_available_roles()
        print("\nPlease specify roles to start, e.g., 'python main.py --roles expert'")
        return

    role_configs = get_enabled_role_configs()
    if not role_configs:
        logger.error("Enabled roles defined but no valid config found. (Roles: %s)", enabled)
        return

    logger.info("Starting %d role bot(s): %s", len(role_configs), [r.role_name for r in role_configs])

    if not getattr(settings, "openai_api_key", ""):
        logger.warning("No OPENAI_API_KEY provided. Generation will fail.")

    try:
        await redis_client.flushall()
        logger.debug("Redis cache flushed on startup.")
    except Exception as e:
        logger.warning("Failed to flush Redis cache: %s", e)

    fastapi_task = asyncio.create_task(run_fastapi(args.port))
    
    from app.utils.logging import log_collector
    log_collector.set_expected_roles(len(role_configs))
    
    bot_tasks = [asyncio.create_task(run_bot_with_config(rc)) for rc in role_configs]
    
    try:
        await asyncio.gather(fastapi_task, *bot_tasks)
    except (KeyboardInterrupt, asyncio.CancelledError):
        for t in bot_tasks:
            t.cancel()
        fastapi_task.cancel()
        logger.info("Shutting down gracefully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")

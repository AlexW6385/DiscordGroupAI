import discord
from discord.ext import commands
import logging

from app.config import settings
from app.context import context_manager
from app.decision import decide_to_speak
from app.generation import generate_response
from app.role_config import RoleConfig
from app.db.database import AsyncSessionLocal
from app.ingestion import ingest_message

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True


def create_bot(role_config: RoleConfig) -> commands.Bot:
    """
    Create a Discord bot instance for the given role config.
    The bot stores role_config so handlers can use its threshold and prompt settings.
    """
    bot = commands.Bot(command_prefix="/", intents=intents)
    bot.role_config = role_config

    @bot.event
    async def on_ready():
        await bot.tree.sync()
        logger.debug("Bot %s ready, logged in as %s", role_config.role_name, bot.user)

    @bot.event
    async def on_message(message: discord.Message):
        if message.author == bot.user:
            return

        async with AsyncSessionLocal() as session:
            await ingest_message(
                session=session,
                guild_id=message.guild.id if message.guild else 0,
                channel_id=message.channel.id,
                message_id=message.id,
                user_id=message.author.id,
                username=message.author.display_name,
                raw_content=message.content,
                is_bot=message.author.bot,
                created_at=message.created_at,
            )

        if message.author.bot:
            return

        await bot.process_commands(message)

        try:
            context = await context_manager.get_context(message.channel.id)
            decision = await decide_to_speak(context, bot.user.id, role_config=role_config)
            threshold = role_config.response_threshold
            will_reply = decision.should_respond and decision.priority >= threshold
            content_preview = (message.content or "").replace("\n", " ").strip()[:200]
            reply_text = ""

            if will_reply:
                async with message.channel.typing():
                    response_text = await generate_response(
                        context=context,
                        tone=decision.tone,
                        max_words=decision.max_words,
                        role_config=role_config,
                    )
                sent_msg = None
                if decision.mode == "reply" and decision.target_message_id:
                    try:
                        target_msg = await message.channel.fetch_message(int(decision.target_message_id))
                        sent_msg = await target_msg.reply(response_text)
                    except Exception:
                        sent_msg = await message.channel.send(response_text)
                else:
                    sent_msg = await message.channel.send(response_text)

                if sent_msg:
                    reply_text = response_text
                    async with AsyncSessionLocal() as session:
                        await ingest_message(
                            session=session,
                            guild_id=sent_msg.guild.id if sent_msg.guild else 0,
                            channel_id=sent_msg.channel.id,
                            message_id=sent_msg.id,
                            user_id=bot.user.id,
                            username=bot.user.display_name,
                            raw_content=response_text,
                            is_bot=True,
                            created_at=sent_msg.created_at,
                        )
            from app.utils.logging import log_collector
            await log_collector.collect(
                message_id=message.id,
                content=message.content,
                role_name=role_config.role_name,
                decision=decision,
                reply_text=reply_text,
                threshold=role_config.response_threshold,
                will_reply=will_reply
            )
        except Exception as e:
            logger.error("Error processing message logic: %s", e, exc_info=True)

    return bot


# 兼容：单 bot 时 main 会先 create_bot，不再使用此全局变量；若有代码直接 import bot 则需改为从 main 传入
bot: commands.Bot | None = None

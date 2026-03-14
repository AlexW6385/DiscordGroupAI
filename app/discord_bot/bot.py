import discord
from discord.ext import commands
import logging
from app.config import settings
from db.database import AsyncSessionLocal
from app.ingestion import ingest_message
from app.decision import decide_to_speak
from app.generation import generate_response
from app.context import context_manager

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    # Ignore messages sent by this bot
    if message.author == bot.user:
        return
        
    logger.info(f"Received message from {message.author.display_name}: {message.content}")

    # Ingest the message in the background
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
            created_at=message.created_at
        )

    # Don't respond to other bots either
    if message.author.bot:
        return
        
    # Process commands (if any)
    await bot.process_commands(message)

    try:
        # Context Decision flow:
        # 1. Get recent context
        context = await context_manager.get_context(message.channel.id)
        
        # 2. Decide if we should respond
        decision = await decide_to_speak(context, bot.user.id)
        logger.info(f"Decision for channel {message.channel.id}: should_respond={decision.should_respond}, priority={decision.priority}, mode={decision.mode}")
        
        if decision.should_respond and decision.priority > 0.5:
            # 3. Generate response
            async with message.channel.typing():
                response_text = await generate_response(
                    context=context,
                    tone=decision.tone,
                    max_words=decision.max_words
                )
                
                # Send message
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
                logger.info(f"Bot sent response to channel {message.channel.id}")
                # Ingest our own response so we have it in context for the next message
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
                        created_at=sent_msg.created_at
                    )
    except Exception as e:
        logger.error(f"Error processing message logic: {e}", exc_info=True)

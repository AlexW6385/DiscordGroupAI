import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="bot_status", description="Check the status of the bot")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Bot is observing {len(self.bot.guilds)} servers.", ephemeral=True)

    @app_commands.command(name="bot_enable", description="Enable the bot in this channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def enable(self, interaction: discord.Interaction):
        # In a real app, update ChannelSettings here
        await interaction.response.send_message("Bot enabled for this channel.", ephemeral=True)

    @app_commands.command(name="bot_disable", description="Disable the bot in this channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable(self, interaction: discord.Interaction):
        # In a real app, update ChannelSettings here
        await interaction.response.send_message("Bot disabled for this channel.", ephemeral=True)

    @app_commands.command(name="bot_persona", description="Set the persona for this server")
    @app_commands.checks.has_permissions(administrator=True)
    async def persona(self, interaction: discord.Interaction, persona: str):
        # Update GuildSettings persona
        await interaction.response.send_message(f"Bot persona updated to: {persona}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCommands(bot))

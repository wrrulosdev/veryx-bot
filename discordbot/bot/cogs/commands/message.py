import asyncio

import discord
from discord.ext import commands
from discord import app_commands
from ...utils import PermsCheck
from ezjsonpy import translate_message
from loguru import logger


class MessageCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='send_message', description='Send a message to a specified channel')
    @logger.catch
    async def send_message(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        """
        Send a message to a specified channel after waiting for a message.

        :param discord.Interaction interaction: The interaction object.
        :param discord.TextChannel channel: The channel to send the message to.
        """
        if not PermsCheck.is_admin(interaction):
            await interaction.response.send_message(
                translate_message('commands.noPerms'), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send(
            translate_message('commands.message.waitingForMessage'), ephemeral=True
        )

        try:
            message = await self.bot.wait_for(
                'message',
                check=lambda m: m.channel == channel and m.author == interaction.user,
                timeout=60.0
            )

        except asyncio.TimeoutError:
            # Timeout error message
            await interaction.followup.send(
                translate_message('commands.message.timeout'), ephemeral=True
            )
            return

        if message.content:
            await channel.send(message.content)

        if message.attachments:
            for attachment in message.attachments:
                await channel.send(file=await attachment.to_file())

        await interaction.followup.send(
            translate_message('commands.message.messageSent'), ephemeral=True
        )

        await message.delete()

    @send_message.error
    @logger.catch
    async def send_message_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """
        Error handler for the send_message command.
        :param interaction: The interaction object.
        :param error: The error that occurred.
        """
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message(
                translate_message('commands.noPerms'), ephemeral=True
            )
        elif isinstance(error, asyncio.TimeoutError):
            await interaction.response.send_message(
                translate_message('commands.message.timeout'), ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """
    Setup function for the message command.

    :param commands.Bot bot: The bot instance.
    """
    cog: MessageCommand = MessageCommand(bot)
    await bot.add_cog(cog)

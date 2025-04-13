from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from discordbot.constants.embeds import Embeds
from discordbot.utils.minecraft.server_status import ServerStatus
from rstatus.models import JavaServerResponse
from ...bot import DiscordBot


class ServerCommand(commands.Cog):
    def __init__(self, bot: DiscordBot) -> None:
        self.bot = bot

    @app_commands.command(name='server', description='View server info')
    async def server_command(self, interaction: discord.Interaction) -> None:
        """
        Show the server info
        :param interaction: Discord Interaction
        """
        await interaction.response.defer(ephemeral=True)
        server_data: Optional[JavaServerResponse] = ServerStatus().get()
        embed: discord.Embed = Embeds.server_embed(data=server_data)
        await interaction.followup.send(embed=embed)


async def setup(bot: DiscordBot):
    await bot.add_cog(ServerCommand(bot))
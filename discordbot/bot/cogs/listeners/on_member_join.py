from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands
from ezjsonpy import translate_message
from loguru import logger

from ....database.db import Database
from ....constants import ChannelConstants


class MemberJoinListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    @logger.catch
    async def on_member_join(self, member: discord.Member) -> None:
        """
        Event listener for when a new member joins the server.
        :param member: The member that joined the server.
        """
        await self.send_welcome_message(member)

    @logger.catch
    async def send_welcome_message(self, member: discord.Member) -> None:
        """
        Sends a welcome message to the specified member.
        :param member: The member to send the welcome message to.
        """
        Database().add_discord_user(discord_id=member.id, username=member.name, joined_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        welcome_channel: Optional[discord.TextChannel] = discord.utils.get(
            member.guild.text_channels,
            id=ChannelConstants.WELCOME_CHANNEL_ID
        )

        if welcome_channel is None:
            logger.error('Welcome channel not found.')
            return

        await welcome_channel.send(translate_message('welcome').replace('%user%', member.mention))

    @commands.command(name='welcomeall')
    @commands.has_permissions(administrator=True)
    @logger.catch
    async def welcome_all_members(self, ctx: commands.Context) -> None:
        """
        Sends the welcome message to all existing members in the server.
        :param ctx: The context of the command.
        """
        for member in ctx.guild.members:
            if not member.bot:  # Optionally skip bots
                await self.send_welcome_message(member)

        await ctx.send("Welcome messages sent to all members.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemberJoinListener(bot))

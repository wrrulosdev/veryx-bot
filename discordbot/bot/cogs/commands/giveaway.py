import re
import random
import time
from typing import Optional

import discord
from discord.ext import commands, tasks
from discord import app_commands
from ezjsonpy import translate_message

from ...bot import DiscordBot
from ...utils import PermsCheck
from ...utils.embed.embed import EmbedUtilities


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse a duration string into seconds.
    Supports days (d), hours (h), and minutes (m).

    :param duration_str: Duration of the giveaway
    """
    time_units: dict[str, int] = {'d': 86400, 'h': 3600, 'm': 60}
    total_seconds: int = 0
    pattern: str = r'(\d+)([dhm])'
    matches: list[tuple] = re.findall(pattern, duration_str)

    if not matches:
        return None

    for amount, unit in matches:
        total_seconds += int(amount) * time_units[unit]

    return total_seconds


class GiveawayCommand(commands.Cog):
    def __init__(self, bot: DiscordBot) -> None:
        self.bot: DiscordBot = bot
        self.active_giveaways: dict[int, dict[str, any]] = {}
        self.check_giveaways.start()

    @app_commands.command(name='giveaway', description='Start a giveaway')
    @app_commands.describe(
        title='Giveaway title',
        description='Giveaway description',
        winners='Number of winners',
        duration='Giveaway duration (e.g., 1d, 2h, 30m)'
    )
    async def giveaway_command(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        winners: app_commands.Range[int, 1, 100],
        duration: str
    ) -> None:
        """
        Start a giveaway with the specified parameters.

        :param interaction: The Discord interaction object.
        :param title: The title of the giveaway.
        :param description: The description of the giveaway.
        :param winners: The number of winners for the giveaway (must be between 1 and 100).
        :param duration: The duration of the giveaway (e.g., 1d, 2h, 30m).
        """
        if not PermsCheck.is_admin(interaction):
            await interaction.response.send_message(
                translate_message('commands.noPerms'), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)
        duration_seconds: Optional[int] = parse_duration(duration)
        
        if duration_seconds is None:
            await interaction.followup.send(translate_message('commands.giveaway.invalidDuration'))
            return
        
        end_time: int = int(time.time()) + duration_seconds
        embed: discord.Embed = EmbedUtilities.create_embed(
            title=title,
            description=description,
            fields=[
                {'name': translate_message('commands.giveaway.embedEndsField'), 'value': f'<t:{end_time}:F>', 'inline': False},
                {'name': translate_message('commands.giveaway.embedHostedField'), 'value': interaction.user.mention, 'inline': False},
                {'name': translate_message('commands.giveaway.embedParticipantsField'), 'value': '0', 'inline': True},
                {'name': translate_message('commands.giveaway.embedWinnersField'), 'value': f'To be determined', 'inline': True},
            ]
        )
        
        message: discord.Message = await interaction.followup.send(embed=embed)
        await message.add_reaction(translate_message('commands.giveaway.emoji'))
        
        self.active_giveaways[message.id] = {
            'end_time': end_time,
            'winners': winners,
            'host_id': interaction.user.id,
            'participants': [],
            'message_id': message.id,
            'channel_id': message.channel.id
        }

    @tasks.loop(seconds=30)
    async def check_giveaways(self) -> None:
        """
        Check every 30 seconds if any giveaway has ended.
        """
        current_time: int = int(time.time())
        
        for giveaway in list(self.active_giveaways.values()):
            if current_time >= giveaway['end_time']:
                await self.process_giveaway(giveaway)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User) -> None:
        """
        Handle reactions added to the giveaway message.
        """
        if user.bot:
            return
            
        message_id: int = reaction.message.id
        giveaway: Optional[dict[str, any]] = self.active_giveaways.get(message_id)
        
        if not giveaway:
            return
            
        if str(reaction.emoji) != translate_message('commands.giveaway.emoji'):
            return
            
        current_time: int = int(time.time())
        
        if current_time >= giveaway['end_time']:
            try:
                await reaction.remove(user)
                
            except discord.NotFound:
                pass
            
            channel: Optional[discord.TextChannel] = self.bot.get_channel(giveaway['channel_id'])
            
            if channel:
                await channel.send(translate_message('commands.giveaway.alreadyEnded').replace(r'%user%', user.mention), delete_after=10)
                
            return
            
        if user.id in giveaway['participants']:
            try:
                await reaction.remove(user)
                
            except discord.NotFound:
                pass
            
            return
            
        giveaway['participants'].append(user.id)
        embed: discord.Embed = reaction.message.embeds[0]
        new_embed: discord.Embed = discord.Embed(title=embed.title, description=embed.description, color=embed.color)
        participants_count: int = len(giveaway['participants'])
        
        for field in embed.fields:
            if field.name == 'Participants':
                new_embed.add_field(name=field.name, value=str(participants_count), inline=field.inline)
                
            else:
                new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
        
        try:
            await reaction.message.edit(embed=new_embed)
        except discord.NotFound:
            pass

    async def process_giveaway(self, giveaway: dict[str, any]) -> None:
        """
        Process the giveaway when it ends.
        """
        participants: list[int] = giveaway['participants']
        winners_count: int = giveaway['winners']
        channel: Optional[discord.TextChannel] = self.bot.get_channel(giveaway['channel_id'])
        
        if not channel:
            return
            
        try:
            message: discord.Message = await channel.fetch_message(giveaway['message_id'])

        except discord.NotFound:
            return
            
        embed: discord.Embed = message.embeds[0]
        new_embed: discord.Embed = discord.Embed(title=embed.title, color=0xff0000)
        winners_mentions: list[str] = []
        new_description: str = f'{embed.description}\n\n{translate_message("commands.giveaway.ended")}'
        
        if participants:
            if winners_count > len(participants):
                winners_count = len(participants)
                
            winners: list[int] = random.sample(participants, winners_count)
            winners_mentions = [f"<@{winner_id}>" for winner_id in winners]
            winners_value: str = ', '.join(winners_mentions)
            
        else:
            new_description = f'{embed.description}\n\n{translate_message("commands.giveaway.noWinnerMessage")}'
            winners_value = translate_message('commands.giveaway.noWinnerEmoji')
            
        new_embed.description = new_description

        for field in embed.fields:
            if field.name == 'Winners':
                new_embed.add_field(name=field.name, value=winners_value, inline=field.inline)
                
            elif field.name == 'Ends':
                new_embed.add_field(name='Ended', value=f'<t:{giveaway['end_time']}:F>', inline=field.inline)
                
            elif field.name == 'Participants':
                new_embed.add_field(name=field.name, value=str(len(participants)), inline=field.inline)
                
            else:
                new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
        
        try:
            await message.edit(embed=new_embed)
            
        except discord.NotFound:
            pass
            
        if winners_mentions:
            await channel.send(f'{translate_message("commands.giveaway.winnersMessages").replace("%winners%", ", ".join(winners_mentions))}')
            
        if giveaway['message_id'] in self.active_giveaways:
            del self.active_giveaways[giveaway['message_id']]


async def setup(bot: DiscordBot) -> None:
    """
    Add the GiveawayCommand cog to the bot.
    """
    await bot.add_cog(GiveawayCommand(bot))
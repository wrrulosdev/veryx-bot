import re
from typing import Optional

import discord
import datetime
from ezjsonpy import translate_message

from rstatus.models import JavaServerResponse
from .url import URLContstants
from . import BotConstants
from ..bot.utils import EmbedUtilities


class Embeds:
    @staticmethod
    def server_embed(data: Optional[JavaServerResponse]) -> discord.Embed:
        """
        Get discord embed for server data
        :param data: Java server response
        :return: Discord Embed
        """
        description: str = translate_message('embeds.server.description') if data is not None else translate_message('embeds.server.descriptionDataFailed')
        description = description.replace(r'%domain%', BotConstants.DOMAIN)

        if data is not None:
            description = description.replace('%players%', str(data.players.online))

        return EmbedUtilities.create_embed(
            title=translate_message('embeds.server.title'),
            description=description,
            color=discord.Color.purple(),
            timestamp=datetime.datetime.now(datetime.UTC),
            thumbnail=URLContstants.LOGO,
            author=BotConstants.AUTHOR,
            author_icon=URLContstants.LOGO,
            footer=translate_message('embeds.server.footer')
        )

    @staticmethod
    def get_ticket_embed() -> discord.Embed:
        return EmbedUtilities.create_embed(
            title=translate_message('commands.ticket.embedTitle'),
            description=translate_message('commands.ticket.embedDescription'),
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now(datetime.UTC),
            thumbnail=URLContstants.LOGO,
            author=BotConstants.AUTHOR,
            author_icon=URLContstants.LOGO,
            footer=translate_message('commands.ticket.embedFooter')
        )

    @staticmethod
    def get_user_ticket_embed(selected_option: str, mention: str) -> discord.Embed:
        return EmbedUtilities.create_embed(
            title=translate_message('commands.ticket.userTicket.embedTitle').replace('%type%', ' '.join([w.capitalize() for w in re.findall(r'[A-Z]?[a-z]+', selected_option)])),
            description=translate_message(f'commands.ticket.userTicket.{selected_option}EmbedDescription').replace(r'%user%', mention),
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now(datetime.UTC),
            thumbnail=URLContstants.LOGO,
            author=BotConstants.AUTHOR,
            author_icon=URLContstants.LOGO,
            footer=translate_message('commands.ticket.userTicket.embedFooter')
        )

    @staticmethod
    def get_transcript_embed(
            open_time: str,
            close_time:str,
            ticket_owner: discord.Member,
            interaction: discord.Interaction
    ) -> discord.Embed:
        return EmbedUtilities.create_embed(
            title='Ticket Closed',
            description='',
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow(),
            author=BotConstants.AUTHOR,
            author_icon=URLContstants.LOGO,
            footer=close_time,
            footer_icon=URLContstants.LOGO,
            fields=[
                {'name': '🕒 Open Time', 'value': open_time, 'inline': True},
                {'name': '👤 Opened By', 'value': f'{ticket_owner.mention}', 'inline': True},
                {'name': '❌ Closed By', 'value': f'{interaction.user.mention}', 'inline': True},
                {'name': '🕒 Close Time', 'value': close_time, 'inline': True},
            ],
        )

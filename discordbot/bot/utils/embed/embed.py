import datetime
from typing import Union

import discord
from loguru import logger


class EmbedUtilities:
    @staticmethod
    @logger.catch
    def create_embed(
        title: str = '',
        description: str = '',
        color: discord.Color = discord.Color.green(),
        url: Union[str, None] = None,
        timestamp: Union[datetime.datetime, None] = None,
        image: Union[str, None] = None,
        thumbnail: Union[str, None] = None,
        author: Union[str, None] = None,
        author_icon: Union[str, None] = None,
        footer: Union[str, None] = None,
        footer_icon: Union[str, None] = None,
        fields: Union[list, None] = None,
    ) -> discord.Embed:
        """
        Create an embed object.
        :param title: The title of the embed.
        :param description: The description of the embed.
        :param color: The color of the embed.
        :param url: The URL of the embed.
        :param timestamp: The timestamp of the embed.
        :param image: The image of the embed.
        :param thumbnail: The thumbnail of the embed.
        :param author: The author of the embed.
        :param author_icon: The author icon of the embed.
        :param footer: The footer of the embed.
        :param footer_icon: The footer icon of the embed.
        :param fields: The fields of the embed.
        :return: The embed object.
        """
        embed: discord.Embed = discord.Embed(
            title=title,
            color=color,
            description=description,
            url=url,
            timestamp=timestamp
        )

        if image:
            embed.set_image(url=image)

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        if author:
            embed.set_author(name=author, icon_url=author_icon)

        if footer:
            embed.set_footer(text=footer, icon_url=footer_icon)

        if fields:
            if len(fields) >= 1:
                for field in fields:
                    name, value, inline = field['name'], field['value'], field['inline']
                    embed.add_field(name=name, value=value, inline=inline)

        return embed

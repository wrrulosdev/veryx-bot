import discord
from discord.ext import commands
import re
from loguru import logger


async def delete_invite_message(message: discord.Message) -> None:
    """
    Deletes the message containing the external Discord invite link.
    :param message: The message that contains the external invite link.
    """
    try:
        await message.delete()
        logger.info(f'Deleted an external Discord invite link from {message.author}.')
        await message.channel.send(f'{message.author.mention}, external Discord invites are not allowed here.', delete_after=2)

    except discord.Forbidden:
        logger.error(f'Failed to delete the message. Missing permissions.')

    except Exception as e:
        logger.error(f'An error occurred while trying to delete the invite link: {str(e)}')


async def contains_external_invite(content: str) -> bool:
    """
    Checks if the message content contains an external Discord invite link.
    :param content: The content of the message to check.
    :return: True if the message contains a Discord invite link, False otherwise.
    """
    invite_pattern: str = r'(https?://)?(www\.)?discord(\.gg|\.com/invite)/[A-Za-z0-9-]+'
    return bool(re.search(invite_pattern, content))


class InviteLinkListener(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    @logger.catch
    async def on_message(self, message: discord.Message) -> None:
        """
        Event listener for when a message is sent in the server.
        :param message: The message that was sent.
        """

        if message.author.bot:
            return

        if message.author.guild_permissions.administrator:
            return

        if await contains_external_invite(message.content) and message.channel.id != 1346278143937482773:
            await delete_invite_message(message)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(InviteLinkListener(bot))

from typing import Optional
import discord
from discord import Message, TextChannel, app_commands
from discord.ext import commands
from ezjsonpy import translate_message
from loguru import logger

from discordbot.database.db import Database
from discordbot.database.models.ids import IdObject

from ....constants import URLContstants
from ...utils import EmbedUtilities, PermsCheck


class VerificationView(discord.ui.View):
    @logger.catch
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RedButton(custom_id='red_button_left'))
        self.add_item(VerificationButton())
        self.add_item(RedButton(custom_id='red_button_right'))


class VerificationButton(discord.ui.Button):
    @logger.catch
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.success,
            label=translate_message('commands.verify.embed.buttonText'),
            custom_id='verify_button'
        )

    @logger.catch
    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Callback function for the verification button.

        :param interaction: The interaction object.
        """
        role_id_object: Optional[IdObject] = Database().get_id_by_name('VERIFICATION_ROLE')

        if role_id_object is None:
            await interaction.response.send_message(
                translate_message('commands.verify.embed.roleNotFound'), ephemeral=True
            )
            return

        role: discord.Role = interaction.guild.get_role(role_id_object.object_id)

        if not role:
            logger.critical(translate_message('commands.verify.embed.roleNotFoundLog'))
            await interaction.response.send_message(
                translate_message('commands.verify.embed.roleNotFound'), ephemeral=True
            )
            return

        await interaction.user.add_roles(role)
        await interaction.response.send_message(
            translate_message('commands.verify.verifySuccess'), ephemeral=True
        )


class RedButton(discord.ui.Button):
    @logger.catch
    def __init__(self, custom_id: str):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label=translate_message('commands.verify.embed.buttonText'),
            custom_id=custom_id
        )

    @logger.catch
    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Callback function for the red button.

        :param interaction: The interaction object.
        """
        await interaction.response.send_message(
            translate_message('commands.verify.redButtonText'), ephemeral=True
        )


class VerifyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='send_verification', description='Send the verification message')
    @logger.catch
    async def send_verification(self, interaction: discord.Interaction, role: discord.Role) -> None:
        """
        Send the verification message.

        :param discord.Interaction interaction: The interaction object.
        :param discord.Role role: The role to assign to users after they verify.
        :return None:
        """
        if not PermsCheck.is_admin(interaction):
            await interaction.response.send_message(
                translate_message('commands.noPerms'), ephemeral=True
            )
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                translate_message('commands.noPerms'), ephemeral=True
            )
            return

        if role not in interaction.guild.roles:
            await interaction.response.send_message(
                translate_message('commands.verify.invalidRole'), ephemeral=True
            )
            return

        view: VerificationView = VerificationView()
        embed: discord.Embed = EmbedUtilities.create_embed(
            title=translate_message('commands.verify.embed.title'),
            description=translate_message('commands.verify.embed.description'),
            image=URLContstants.BANNER,
            thumbnail=URLContstants.LOGO,
            color=discord.Color.green()
        )
        await interaction.response.send_message(translate_message('commands.verify.embed.sent'), ephemeral=True)
        verify_message: Message = await interaction.channel.send(embed=embed, view=view)
        Database().add_id(interaction.channel.id, 'VERIFICATION_CHANNEL', 'channel')
        Database().add_id(verify_message.id, 'VERIFICATION_MESSAGE', 'message')
        Database().add_id(role.id, 'VERIFICATION_ROLE', 'role')

    @logger.catch
    async def on_ready(self) -> None:
        """
        The on_ready function for the verification cog.
        This loads the verification message and sets the view.
        """
        try:
            verify_channel_id: Optional[IdObject] = Database().get_id_by_name('VERIFICATION_CHANNEL')
            verify_message_id: Optional[IdObject] = Database().get_id_by_name('VERIFICATION_MESSAGE')

            if verify_channel_id is not None and verify_message_id is not None:
                verify_channel: Optional[TextChannel] = self.bot.get_channel(verify_channel_id.object_id)

                if verify_channel:
                    verify_message: Optional[Message] = await verify_channel.fetch_message(verify_message_id.object_id)
                    view: VerificationView = VerificationView()
                    await verify_message.edit(view=view)
                    return

                Database().del_id('VERIFICATION_CHANNEL')
                Database().del_id('VERIFICATION_MESSAGE')

        except Exception as e:
            logger.info('Verify message not found! Deleting old IDs..')
            Database().del_id('VERIFICATION_CHANNEL')
            Database().del_id('VERIFICATION_MESSAGE')
            return

    @send_verification.error
    @logger.catch
    async def send_verification_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """
        Error handler for the send_verification command.
        :param interaction: The interaction object.
        :param error: The error that occurred.W
        """
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message(
                translate_message('commands.noPerms'), ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """
    Setup function for the verify command.

    :param commands.Bot bot: The bot instance.
    """
    cog: VerifyCommand = VerifyCommand(bot)
    await bot.add_cog(cog)
    bot.add_listener(cog.on_ready, 'on_ready')

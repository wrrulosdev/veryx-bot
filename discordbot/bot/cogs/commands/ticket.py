import asyncio
import io
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands, CategoryChannel, Role, TextChannel, Message
from discord.ext import commands
from ezjsonpy import translate_message
from loguru import logger

from chat_exporter import chat_exporter
from ...utils.perms.perms import PermsCheck
from ....constants.embeds import Embeds
from ....constants.ids import CategoriesConstants, RoleConstants, ChannelConstants
from ....database.db import Database
from ....database.models.ids import IdObject

DROPDOWN_OPTIONS: list[tuple[str, str]] = [
    ('support', '🛠️'),
    ('account', '🔑'),
    ('media', '🎬'),
    ('ban', '🚫'),
    ('rewards', '🎁'),
    ('fTopReport', '📊'),
    ('staffReport', '👨‍💻'),
    ('userReport', '🧑‍💻'),
    ('bugReport', '🐛'),
    ('buyCraft', '💳')
]

TICKET_NAME_LIST: tuple = tuple(option[0] for option in DROPDOWN_OPTIONS)


class CloseTicket:
    @staticmethod
    async def close(interaction: discord.Interaction, channel: TextChannel) -> None:
        """
        Close the current ticket
        :param interaction: Discord Interaction
        :param channel: Current discord channel
        """
        if not channel.name.startswith(TICKET_NAME_LIST):
            await interaction.response.send_message(
                translate_message('commands.ticket.notATicketChannel'), ephemeral=True
            )
            return

        if not PermsCheck.is_staff(interaction=interaction):
            await interaction.response.send_message(
                translate_message('noPerms'),
                ephemeral=True
            )
            return

        await interaction.response.send_message(translate_message('commands.ticket.closingTicket'), ephemeral=True)
        await asyncio.sleep(1)
        ticket_owner: Optional[discord.Member] = None
        ticket_id_data: IdObject = Database().get_id_by_id(interaction.channel.id)

        for member in channel.members:
            if member != interaction.guild.me:  # Exclude the bot itself
                if member.id == int(ticket_id_data.name):
                    ticket_owner = member
                    break

        if ticket_owner is None:
            await interaction.followup.send(translate_message('commands.ticket.noTicketOwnerFound'), ephemeral=True)
            return

        # Generate the transcripts
        transcript: Optional[str] = await chat_exporter.export(channel)
        transcript_file: Optional[discord.File] = None

        if transcript is not None:
            transcript_file = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f'transcript-{channel.name}.html'
            )

        open_time: str = channel.created_at.strftime('%d de %B de %Y %H:%M')
        close_time: str = datetime.utcnow().strftime('%d/%m/%Y %H:%M')
        embed: discord.Embed = Embeds.get_transcript_embed(open_time=open_time, close_time=close_time, ticket_owner=ticket_owner, interaction=interaction)
        ticket_log_channel: Optional[TextChannel] = discord.utils.get(interaction.guild.text_channels, id=ChannelConstants.TICKET_LOGS_CHANNEL_ID)

        if ticket_log_channel is not None:
            await ticket_log_channel.send(embed=embed)

            if transcript_file is not None:
                await ticket_log_channel.send(file=transcript_file)

        await interaction.followup.send(translate_message('commands.ticket.ticketClosed').replace('%user%', interaction.user.display_name), ephemeral=True)
        await asyncio.sleep(1)
        await channel.delete(reason=f'Ticket closed by {interaction.user}')
        Database().del_id(str(interaction.user.id))


class CloseTicketButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            style=discord.ButtonStyle.danger,
            label=translate_message('commands.ticket.closeButton'),
            custom_id='close_ticket'
        )

    @logger.catch
    async def callback(self, interaction: discord.Interaction) -> None:
        """
        On button click
        :param interaction: Discord Interaction
        """
        await CloseTicket.close(interaction=interaction, channel=interaction.channel)


class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options: list = [
            discord.SelectOption(
                label=translate_message(f'commands.ticket.options.{value}Label'),
                value=value,
                description=translate_message(f'commands.ticket.options.{value}Description'),
                emoji=emoji
            )
            for value, emoji in DROPDOWN_OPTIONS
        ]
        super().__init__(
            placeholder=translate_message('commands.ticket.dropdownPlaceholder'),
            min_values=1,
            max_values=1,
            options=options,
            custom_id='ticket_dropdown'
        )

    @logger.catch
    async def callback(self, interaction: discord.Interaction) -> None:
        """
        On Dropdown item click
        :param interaction: Discord Interaction
        """
        guild: discord.Guild = interaction.guild
        user: discord.Member = interaction.user
        category: Optional[CategoryChannel] = interaction.guild.get_channel(CategoriesConstants.TICKET_CATEGORY_ID)
        staff_role: Optional[Role] = interaction.guild.get_role(RoleConstants.STAFF_ROLE_ID)

        if staff_role is None or staff_role is None:
            await interaction.response.send_message('An error occurred while trying to get the staff role or ticket category.')
            logger.critical(f'An error occurred while trying to get the staff role or ticket category. Ticket Category: {category} - Staff Role: {staff_role}')
            return

        overwrites: dict = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            staff_role: discord.PermissionOverwrite(view_channel=True),
        }
        selected_option: str = interaction.data['values'][0]
        channel_name: str = f'{selected_option}-ticket-{user.display_name.lower().replace(" ", "-")}'

        # Check if the user already has a ticket
        for channel in guild.text_channels:
            if channel.name == channel_name:
                await interaction.response.send_message(translate_message('commands.ticket.ticketExists'), ephemeral=True)
                return

        channel: Optional[TextChannel] = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        if channel is None:
            await interaction.response.send_message(f'The ticket for the user {user.display_name} was not created.')
            logger.critical(f'The ticket for the user {user.display_name} was not created.')
            return

        view: discord.ui.View = discord.ui.View()
        view.add_item(CloseTicketButton())

        # Send the embed to the user ticket
        embed: discord.Embed = Embeds.get_user_ticket_embed(selected_option=selected_option, mention=user.mention)
        await channel.send(
            content=f"{interaction.user.mention} | {staff_role.mention}",
            embed=embed,
            view=view
        )
        await interaction.response.send_message(
            translate_message('commands.ticket.createdTicket').replace('%channel%', channel.mention),
            ephemeral=True
        )
        Database().add_id(channel.id, str(user.id), 'ticket')
        new_view: TicketView = TicketView()
        await interaction.message.edit(view=new_view)


class TicketView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


class TicketCommand(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name='send_ticket',
        description=translate_message('commands.ticket.sendCommandDescription')
    )
    @logger.catch
    async def send_ticket(self, interaction: discord.Interaction) -> None:
        """
        Set up the ticket message.
        :param interaction: Discord Interaction
        """
        if not PermsCheck.is_admin(interaction=interaction):
            await interaction.response.send_message(
                translate_message('noPerms'),
                ephemeral=True
            )
            return

        ticket_channel_id: Optional[IdObject] = Database().get_id_by_name('TICKET_CHANNEL')
        ticket_message_id: Optional[IdObject] = Database().get_id_by_name('TICKET_MESSAGE')

        if ticket_channel_id is not None and ticket_message_id is not None:
            ticket_channel: Optional[TextChannel] = self.bot.get_channel(ticket_channel_id.object_id)

            if ticket_channel is not None:
                ticket_message: Optional[Message] = await ticket_channel.fetch_message(ticket_message_id.object_id)

                if ticket_message is not None:
                    await ticket_message.delete()

        embed: discord.Embed = Embeds.get_ticket_embed()
        view: discord.ui.View = TicketView()
        new_ticket_message: Message = await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(translate_message('commands.ticket.setup'), ephemeral=True)
        Database().add_id(interaction.channel.id, 'TICKET_CHANNEL', 'channel')
        Database().add_id(new_ticket_message.id, 'TICKET_MESSAGE', 'message')
        await interaction.original_response()

    @send_ticket.error
    @logger.catch
    async def send_ticket_error(self, interaction: discord.Interaction, error) -> None:
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                translate_message('noPerms'),
                ephemeral=True
            )

    @logger.catch
    async def on_ready(self) -> None:
        """Try to load the ticket message if it exists"""
        if not self.bot.is_ready():
            return

        try:
            ticket_channel_id: Optional[IdObject] = Database().get_id_by_name('TICKET_CHANNEL')
            ticket_message_id: Optional[IdObject] = Database().get_id_by_name('TICKET_MESSAGE')

            if ticket_channel_id is not None and ticket_message_id is not None:
                channel: Optional[TextChannel] = self.bot.get_channel(ticket_channel_id.object_id)

                if channel:
                    logger.info('The ticket message was updated successfully.')
                    message: Optional[Message] = await channel.fetch_message(ticket_message_id.object_id)
                    view: TicketView = TicketView()
                    await message.edit(view=view)
                    return

                Database().del_id('TICKET_CHANNEL')
                Database().del_id('TICKET_MESSAGE')

        except Exception as e:
            logger.error(f"Error loading ticket message: {e}")
            Database().del_id('TICKET_CHANNEL')
            Database().del_id('TICKET_MESSAGE')


async def setup(bot: commands.Bot):
    cog: TicketCommand = TicketCommand(bot)
    await bot.add_cog(cog)
    bot.add_listener(cog.on_ready, 'on_ready')

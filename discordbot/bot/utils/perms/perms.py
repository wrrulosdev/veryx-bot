import discord
from typing import Optional

from discord import Role

from ....constants.ids import RoleConstants


class PermsCheck:
    @staticmethod
    def is_admin(interaction: discord.Interaction) -> bool:
        """
        Checks if the user has administrator permissions in the guild.
        :param interaction: The Discord interaction object.
        :return: True if the user has administrator permissions, False otherwise.
        """
        if interaction.user.guild_permissions.administrator:
            return True

        return False

    @staticmethod
    def is_staff(interaction: discord.Interaction) -> bool:
        """
        Checks if the user has the 'staff' role in the guild.
        :param interaction: The Discord interaction object.
        :return: True if the user has the staff role, False otherwise.
        """
        staff_role: Optional[Role] = interaction.guild.get_role(RoleConstants.STAFF_ROLE_ID)

        if staff_role is None or staff_role not in interaction.user.roles:
            return False

        return True

import discord
from discord.ext import commands


def has_required_role():
    allowed_roles = ['Officer', '"Technician"']

    async def predicate(interaction):
        if type(interaction) == discord.Interaction:
            user_roles = [role.name for role in interaction.user.roles]
        else:
            user_roles = [role.name for role in interaction.author.roles]

        if any(role in user_roles for role in allowed_roles):
            return True
        else:
            return False

    return commands.check(predicate)

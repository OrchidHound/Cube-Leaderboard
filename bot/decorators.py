import discord
from discord.ext import commands


def has_required_role():
    allowed_roles = ['Officer', 'Bot Wrangler']

    async def predicate(interaction):
        if type(interaction) == discord.Interaction:
            player_roles = [role.name for role in interaction.player.roles]
        else:
            player_roles = [role.name for role in interaction.author.roles]

        if any(role in player_roles for role in allowed_roles):
            return True
        else:
            return False

    return commands.check(predicate)

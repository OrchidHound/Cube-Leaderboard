from discord import app_commands
from discord.ext import commands
from scripts import menu
# from scripts import sql
# from config import config
import discord

if __name__ == '__main__':
    # Discord setup
    TOKEN = config.TOKEN
    bot = commands.Bot(command_prefix='>', intents=discord.Intents.all())

    # Login confirmation
    async def on_ready():
        print("Logged in as {0.user}".format(bot))
        # Sync the command tree and allow slash commands
        await bot.tree.sync()



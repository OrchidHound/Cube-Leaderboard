from discord import app_commands
from discord.ext import commands
from scripts import menu
from scripts.embeds import SessionView
from scripts.session import Session, assign_id, get_session, get_session_users
# from scripts import sql
import config
import discord
import re


if __name__ == '__main__':
    # Dictionary of servers that have active sessions, labelled by server ID
    # Each server will have a list of sessions, labelled by number
    # Each session will be a list of User objects
    sessions = {}

    # Discord setup
    TOKEN = config.TOKEN
    bot = commands.Bot(command_prefix='>', intents=discord.Intents.all())

    # Login confirmation
    @bot.event
    async def on_ready():
        print("Logged in as {0.user}".format(bot))
        # Sync the command tree and allow slash commands
        await bot.tree.sync()

    @bot.command(name="new_session", description="Create a new game session.")
    async def new_session(ctx, *users):
        # List of users must be greater than 2
        if len(users) < 2:
            await ctx.send("You must provide at least 2 players!")
            return

        # Get server information
        server = bot.get_guild(ctx.message.guild.id)
        # If the server is not currently in the active sessions, add it to the sessions
        if server.id not in sessions:
            sessions[ctx.message.guild.id] = []
        # Sessions for the current server
        server_sessions = sessions[ctx.message.guild.id]
        # Add a new session
        session_id = assign_id(server_sessions)
        server_sessions.append(Session(server, users, session_id=session_id))

        session_view = SessionView(server_sessions, next(session for session in server_sessions if session.session_id == session_id))
        await session_view.send(ctx)

        # await ctx.send(f"Users in session: \n{get_session_users(server_sessions[session_id-1])}\n"
        #                f"Session: {session_id}")

    # Bot initiation/logon
    bot.run(TOKEN)

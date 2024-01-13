from discord.ext import commands
from scripts.view import HeadView
from scripts.session import Session, assign_id
import config
import discord
import scripts.sql as sql


if __name__ == '__main__':
    # Dictionary of servers that have active sessions, labelled by server ID
    # Each server will have a list of sessions, labelled by number
    # Each session will be a list of User objects
    sessions = {}
    database = sql.sql(server_id=0)

    # Discord setup
    TOKEN = config.TOKEN
    bot = commands.Bot(command_prefix='>', intents=discord.Intents.all())

    @bot.hybrid_command(name="new_session", description="Create a new game session.")
    async def new_session(ctx, users_str: str):
        users_str = users_str.split()
        users = []

        for user in users_str:
            try:
                user = await commands.UserConverter().convert(ctx, user)
                users.append(user)
            except commands.errors.UserNotFound:
                users.append(user)

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

        session_view = HeadView(server_sessions, next(session for session in server_sessions if session.session_id == session_id), ctx.channel)
        await session_view.send(ctx)


    @bot.hybrid_command(name="elo", description="Retrieve your current elo score.")
    async def elo(ctx):
        database.server_id = ctx.guild.id
        database.set_user(ctx.author)
        embed = discord.Embed(title=f"{ctx.author.name}",
                              description=f"Your elo score is {database.get_elo(ctx.author)}.",
                              color=0x24bc9c)
        await ctx.send(embed=embed)


    @bot.hybrid_command(name="leaderboard", description="Get the current leaderboard for your server.")
    async def leaderboard(ctx):
        rank = 1
        database.server_id = ctx.guild.id
        server_leaderboard = database.get_leaderboard()
        embed = discord.Embed(title=f"Leaderboard",
                              description="",
                              color=0x24bc9c)
        for user in server_leaderboard:
            embed.add_field(name=f"`{' ' * 10}Rank {rank}{' ' * (10 - len(str(user[0])))}`",
                            value=f"> {user[1]}\n> {user[2]}",
                            inline=False)
            rank += 1
        await ctx.send(embed=embed)

    # Login confirmation
    @bot.event
    async def on_ready():
        print("Logged in as {0.user}".format(bot))
        # Sync the command tree and allow slash commands
        await bot.tree.sync()

    # Bot initiation/logon
    bot.run(TOKEN)

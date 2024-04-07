from discord.ext import commands
import bot.view as view
from bot.session import Session, assign_id
from bot.user import User, convert
from bot.decorators import has_required_role
import config
import discord
import bot.sql as sql


if __name__ == '__main__':
    # Dictionary of servers that have active sessions, labelled by server ID
    # Each server will have a list of sessions, labelled by number
    # Each session will be a list of User objects
    sessions = {}
    database = sql.sql(server_id=0)

    # Discord setup
    TOKEN = config.TOKEN
    bot = commands.Bot(command_prefix='>', intents=discord.Intents.all())


    def new_session(ctx, users, three_rounds):
        # Determine if the user would like to set the match to three rounds regardless of player amount
        if three_rounds.lower() in ['t', 'true', 'y', 'yes']:
            three_rounds = True
        else:
            three_rounds = False

        # Get server information
        server = bot.get_guild(ctx.message.guild.id)
        # If the server is not currently in the active sessions, add it to the sessions
        if server.id not in sessions:
            sessions[ctx.message.guild.id] = []
        # Sessions for the current server
        server_sessions = sessions[ctx.message.guild.id]
        # Add a new session
        session_id = assign_id(server_sessions)
        server_sessions.append(Session(server, users, session_id=session_id, three_rounds=three_rounds))
        curr_session = server_sessions[0]

        return server_sessions, session_id, curr_session


    @has_required_role()
    @bot.hybrid_command(name="manual_match", description="Manually assign match results.")
    async def manual_match(ctx, users_str: str, r1_winner, r2_winner=None, r3_winner=None):
        users = [User(await convert(ctx, user)) for user in users_str.split()]
        user_names = [user.get_name() for user in users]
        server = bot.get_guild(ctx.message.guild.id)
        database.server_id = server.id
        match = {'p1': user_names[0], 'p2': user_names[1],
                 'r1_winner': User(await convert(ctx, r1_winner)).get_name(),
                 'r2_winner': User(await convert(ctx, r2_winner)).get_name() if r2_winner is not None else None,
                 'r3_winner': User(await convert(ctx, r3_winner)).get_name() if r3_winner is not None else None}
        wins = {match['p1']: 0, match['p2']: 0}

        for winner in [r1_winner, r2_winner, r3_winner]:
            winner = User(await convert(ctx, winner))
            if winner.get_name() is not None:
                if winner.get_name() not in [match['p1'], match['p2']]:
                    await ctx.send("You must provide valid winners!")
                    return
                else:
                    wins[winner.get_name()] += 1

        if wins[match['p1']] == wins[match['p2']]:
            await ctx.send("You must provide a valid winner!")
            return

        for user in users:
            database.set_user(user.get_name())

        prior_scores = {user_names[0]: database.get_elo(user_names[0]), user_names[1]: database.get_elo(user_names[1])}
        prior_ranks = {user_names[0]: database.get_rank(user_names[0]), user_names[1]: database.get_rank(user_names[1])}

        database.adjust_score(p1=match['p1'],
                              p2=match['p2'],
                              match=match)

        embed = discord.Embed(title=f"Match results for {users[0].get_nick()} and {users[1].get_nick()} "
                                    f"have been updated.",
                              description="",
                              color=0x24bc9c)

        for user in users:
            embed.add_field(name=f"> {user.get_nick()}",
                            value=f"\n> `Elo {prior_scores[user.get_name()]} -> {database.get_elo(user.get_name())}`"
                                  f"\n> `Rank {prior_ranks[user.get_name()]} -> {database.get_rank(user.get_name())}`",
                            inline=False)

        # Send a message confirming change
        await ctx.send(embed=embed)


    @has_required_role()
    @bot.hybrid_command(name="new_game", description="Create a new game session.")
    async def new_game(ctx, users_str: str, three_rounds: str = 't'):
        users = [User(await convert(ctx, user)) for user in users_str.split()]

        # List of users must be greater than 4
        if len(users) < 4:
            await ctx.send("You must provide at least 4 players!")
            return

        server_sessions, session_id, curr_session = new_session(ctx, users, three_rounds)

        session_view = view.RosterView(server_sessions, curr_session, ctx.channel)
        await session_view.send(ctx)


    @has_required_role()
    @bot.hybrid_command(name="cancel_session", description="Cancel a game session.")
    async def cancel_session(ctx):
        server_sessions = sessions[ctx.message.guild.id]
        curr_session = server_sessions[0]
        session_view = view.CancelView(server_sessions, curr_session, ctx.channel)
        await session_view.send(ctx)


    @has_required_role()
    @bot.hybrid_command(name="create_seating", description="Create a seating chart for a game session.")
    async def create_seating(ctx):
        server_sessions = sessions[ctx.message.guild.id]
        curr_session = server_sessions[0]
        session_view = view.SeatingView(server_sessions, curr_session, ctx.channel)
        await session_view.send(ctx)


    @has_required_role()
    @bot.hybrid_command(name="next_match", description="Generate the next match for the current session.")
    async def next_match(ctx):
        server_sessions = sessions[ctx.message.guild.id]
        curr_session = server_sessions[0]
        session_view = view.PairingView(server_sessions, curr_session, ctx.channel)
        await session_view.send(ctx)


    @has_required_role()
    @bot.hybrid_command(name="match_winners", description="Input the winners for the current match.")
    async def match_winners(ctx):
        server_sessions = sessions[ctx.message.guild.id]
        curr_session = server_sessions[0]
        if not curr_session.active:
            match_view = view.MatchView(server_sessions, curr_session, ctx.channel)
            await match_view.send(ctx)

    # Drop a user from the current session
    @has_required_role()
    @bot.hybrid_command(name="drop_users", description="Drop a user from the current session.")
    async def drop_users(ctx, users_str: str):
        server_sessions = sessions[ctx.message.guild.id]
        curr_session = server_sessions[0]
        users = [User(await convert(ctx, user)) for user in users_str.split()]
        for user in users:
            if user.get_name() not in [user.get_name() for user in curr_session.get_active_users()]:
                await ctx.send("You must only provide users who are actively in the session!")
                return
        curr_session.drop_users(users)
        session_view = view.RosterView(server_sessions, curr_session, ctx.channel)
        await session_view.send(ctx)


    @bot.hybrid_command(name="elo", description="Retrieve your current elo score.")
    async def elo(ctx):
        database.server_id = ctx.guild.id
        database.set_user(ctx.author)
        embed = discord.Embed(title=f"{ctx.author.nick}",
                              description=f"Your elo score is {database.get_elo(ctx.author)}.\n"
                                          f"Your rank is {database.get_rank(ctx.author)}.",
                              color=0x24bc9c)
        await ctx.send(embed=embed)


    @bot.hybrid_command(name="leaderboard", description="Get the current leaderboard for your server.")
    async def leaderboard(ctx):
        database.server_id = ctx.guild.id
        server_leaderboard = database.get_leaderboard()
        embed = discord.Embed(title=f"Leaderboard",
                              description="",
                              color=0x24bc9c)
        for placement, value in server_leaderboard.items():
            if placement <= 10:
                user = User(await convert(ctx, value['user']))
                embed.add_field(name=f"`{' ' * 10}Rank {placement}{' ' * (10 - len(str(placement)))}`",
                                value=f"> {user.get_nick()}\n> {value['elo']}",
                                inline=False)
        await ctx.send(embed=embed)

    # Login confirmation
    @bot.event
    async def on_ready():
        print("Logged in as {0.user}".format(bot))
        # Sync the command tree and allow slash commands
        await bot.tree.sync()

    # Bot initiation/logon
    bot.run(TOKEN)

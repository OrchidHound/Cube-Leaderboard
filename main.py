import discord
import config
import bot.database as database
from discord.ext import commands
from bot.view import SessionView
from bot.player import Player
from bot.decorators import has_required_role
from bot.session import Session

if __name__ == '__main__':
    db = database.Database()

    # Discord setup
    TOKEN = config.TOKEN
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

    async def convert(ctx, player_str):
        try:
            return await commands.MemberConverter().convert(ctx, player_str), True
        except commands.MemberNotFound:
            return player_str, False
        except TypeError:
            return None


    @has_required_role()
    @bot.hybrid_command(name="new_game", description="Create a new game session.")
    async def new_game(ctx, players_str: str):
        player_tags = players_str.split()
        db_players = db.get_all_players()
        players = []

        # List of players must be at least 4
        if len(player_tags) < 4:
            await ctx.send("You must provide at least 4 players!")
            return

        # Populate players list with participating players
        # Set the player in the database if they are new and have valid Discord info
        # Create a temporary player otherwise
        for player_tag in player_tags:
            player_id, player_nick, original_elo, original_rank = None, player_tag, 1200, None
            temporary = False if player_tag[:2] == "<@" else True

            for db_row in db_players:
                # If the player's Discord tag is found in the database
                if player_tag == db_row[1]:
                    player_id, player_nick, original_elo, original_rank = \
                        db_row[0], db_row[2], db_row[4], db.get_rank(player_id)

            # If the player was not found in the database
            if player_id is None and not temporary:
                # Get the Discord info for the player if their tag is valid
                new_player, player_found = await convert(ctx, player_tag)

                if player_found:
                    player_id, player_nick = new_player.id, ctx.guild.get_member(new_player.id).nick
                    if player_nick is None:
                        player_nick = ctx.guild.get_member(new_player.id).name
                    # Set player info in database
                    db.set_player(player_id, player_tag, player_nick)
                else:
                    print("Issue retrieving player's info from Discord (Main.py new_game())")

            # Add the player to the list of players participating in the current session
            players.append(Player(player_id, player_tag, player_nick, original_elo, original_rank))

        session = Session(players, db)
        view = SessionView(ctx, session, ctx.message.id)
        bot.add_view(view)
        await ctx.send(view=view, embed=view.roster_embed())


    @has_required_role()
    @bot.hybrid_command(name="manual_game", description="Input a game session manually.")
    async def manual_game(ctx, players_str: str):
        player_tags = players_str.split()
        db_players = db.get_all_players()
        players = []

    # Login confirmation
    @bot.event
    async def on_ready():
        print("Logged in as {0.user}".format(bot))
        # Sync the command tree and allow slash commands
        await bot.tree.sync()

    # Bot initiation/logon
    bot.run(TOKEN)

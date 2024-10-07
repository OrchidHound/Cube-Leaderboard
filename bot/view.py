from bot.decorators import has_required_role
import random
import discord


class SessionView(discord.ui.View):
    def __init__(self, session, ctx):
        super().__init__(timeout=None)
        self.session = session
        self.ctx = ctx
        self.message = ""
        self.pairs = []
        self.embed = discord.Embed(color=0x24bc9c)
        self.embed.set_footer(text=self.session.datetime)
        self.embed.set_image(url="https://cdn.discordapp.com/attachments/1186834070085316691/1226447322368577608/"
                                 "footer.png?ex=6624cd13&is=66125813&hm="
                                 "93d7af4b304e9a3c4026264aa311e4684e27df5d1057f07f4a57234eb9ca98b5&")

    def spacing(self, player_nick):
        return ' ' * (self.session.longest - len(player_nick))

    async def send(self, ctx):
        self.message = await ctx.send(embed=self.create_embed(), view=self)

    async def update_message(self):
        await self.message.edit(embed=self.create_embed(), view=self)

    def create_embed(self):
        return self.embed

    def update_buttons(self):
        pass


class CancelView(SessionView):
    def __init__(self, session, ctx):
        super().__init__(session=session, ctx=ctx)

    def create_embed(self):
        # TODO: Cancel session

        self.embed.title = ""
        self.embed.description = f"Session {self.session.session_id} cancelled."

        return self.embed


class RosterView(SessionView):
    def __init__(self, session, ctx):
        super().__init__(session=session, ctx=ctx)

    def create_embed(self):
        self.embed.title = "Roster"
        self.embed.description = "Session contains these users:"

        for user in self.session.get_active_users():
            spacing = ' ' * (self.session.longest - len(user.get_nick()))
            self.embed.add_field(name="",
                                 value=f"> `{user.get_nick()}{spacing} "
                                       f"| {self.session.database.get_elo(user.get_name())}`",
                                 inline=False)

        return self.embed


class SeatingView(SessionView):
    def __init__(self, session, ctx):
        super().__init__(session=session, ctx=ctx)

    def create_embed(self):
        self.embed.title = "Seating"

        seats = list(range(1, len(self.session.get_active_users()) + 1))
        player_amt = len(self.session.get_active_users())
        pack_size = 15 if player_amt <= 8 else 15 + (player_amt - 8)
        draft_warning = 'Since there are less than 8 players, consider using a house rule for drafting.\n'

        self.embed.description = "Let's start drafting!\n" \
                            f"Since there are {player_amt} players, each player will make 3 packs of " \
                            f"{pack_size}.\n" \
                            f"{draft_warning if player_amt < 8 else ''}" \
                            "\nSeating order is as follows:"

        for user in self.session.users:
            user.seat = random.choice(seats)
            seats.remove(user.seat)
        for seat_number in range(player_amt + 1):
            for user in self.session.get_active_users():
                if user.seat == seat_number:
                    self.embed.add_field(name=f"\n> Seat {user.seat} ", value=f"> `{user.get_nick()}`", inline=False)

        return self.embed


class PairingView(SessionView):
    def __init__(self, session, ctx):
        super().__init__(session=session, ctx=ctx)
        self.match = None

    def create_embed(self):
        self.embed.title = f"Match {len(self.session.matches) + 1} Pairings"

        self.match = self.session.new_match()
        bye_message = ""
        if self.session.bye is not None:
            bye_user = self.session.bye
            bye_message = f"Since there are an odd number of players, {bye_user.get_nick()} gets a bye.\n"

        self.embed.description = "It's time to play!\n" + \
                            bye_message + \
                            f"The match {len(self.session.matches)} pairings are:"

        for key, value in self.match.items():
            self.embed.add_field(name=f"",
                                 value=f"```{value['p1'].get_nick()} {self.spacing(value['p1'].get_nick())}"
                                       f"( {value['p1'].get_wins()} / {value['p1'].get_losses()} )"
                                       f"\n\n"
                                       f"{' ' * ((self.session.longest + 4) // 2)}--VS--"
                                       f"\n\n"
                                       f"{value['p2'].get_nick()} {self.spacing(value['p2'].get_nick())}"
                                       f"( {value['p2'].get_wins()} / {value['p2'].get_losses()} )"
                                       f"\n{'_' * (self.session.longest + 10)}```",
                                 inline=False)

        for key, value in self.match.items():
            pair_view = PairView(self.session, self.ctx, value, key)
            self.session.active.append(pair_view)

        return self.embed


class MatchView(SessionView):
    def __init__(self, session, ctx):
        super().__init__(session=session, ctx=ctx)
        self.add_item(self.submit_match_button())
        self.match = self.session.matches[len(self.session.matches)]

    async def send(self, ctx):
        self.message = await ctx.send(embed=self.create_embed(), view=self)

        for pair_view in self.session.active:
            await pair_view.send(self.ctx)
        self.add_item(self.submit_match_button())

    def create_embed(self):
        self.embed.title = f"Match {len(self.session.matches)} Input"

        self.embed.description = f"Please input the results of match {len(self.session.matches)}."
        return self.embed

    async def update_message(self):
        self.embed.title = f"Match {len(self.session.matches)} Results"

        self.clear_items()
        self.embed.clear_fields()
        self.embed.description = f"The match {len(self.session.matches)} results are as follows:\n"
        for pairing in self.session.matches[len(self.session.matches)].values():
            p1_wins, p2_wins = self.session.get_match_results(pairing)
            self.embed.add_field(name=f"",
                                 value=f"```{pairing['p1'].get_nick()} {self.spacing(pairing['p1'].get_nick())} "
                                       f"( {p1_wins} ) "
                                       f"\n\n"
                                       f"{' ' * ((self.session.longest + 2) // 2)}--VS--"
                                       f"\n\n"
                                       f"{pairing['p2'].get_nick()} {self.spacing(pairing['p2'].get_nick())} "
                                       f"( {p2_wins} )"
                                       f"\n{'_' * (self.session.longest + 7)}```",
                                 inline=False)
        await self.message.edit(embed=self.embed, view=self)

    def submit_match_button(self):
        button = discord.ui.Button(label="Submit",
                                   style=discord.ButtonStyle.green)

        @has_required_role()
        async def submit_match(interaction):
            failed = False
            await interaction.response.defer()
            for pairing in self.session.matches[len(self.session.matches)].values():
                p1_wins, p2_wins = self.session.get_match_results(pairing)
                if p1_wins == p2_wins:
                    failed = True
                    await self.ctx.send(f"Invalid round data for {pairing['p1'].get_nick()} "
                                        f"vs. {pairing['p2'].get_nick()}.",
                                        delete_after=10)
            if not failed:
                self.session.update_winners()
                await self.session.delete_active_matches(self.ctx)
                self.session.set_game_winners()
                if self.session.game_winners is not None:
                    win_view = WinView(self.session, self.ctx)
                    await win_view.send(self.ctx)
                await self.update_message()

        button.callback = submit_match
        return button


class PairView(SessionView):
    def __init__(self, session, ctx, pair_info, key):
        super().__init__(session=session, ctx=ctx)
        self.pair_info = pair_info
        self.key = key
        for listing in self.versus_listings():
            self.add_item(listing)

    def create_embed(self):
        return discord.Embed(title=f"{self.pair_info['p1'].get_nick()} vs. {self.pair_info['p2'].get_nick()}",
                             color=0x24bc9c)

    def versus_listings(self):
        select_menus = []
        for round_num in [1, 2, 3]:
            p1 = self.pair_info['p1']
            p2 = self.pair_info['p2']

            initial_options = [
                discord.SelectOption(label=f"{p1.get_nick()}", value='p1'),
                discord.SelectOption(label=f"{p2.get_nick()}", value='p2')
            ]
            if round_num > 1:
                initial_options.append(discord.SelectOption(label="Draw", value='draw'))

            select = discord.ui.Select(placeholder=f"Who won round {round_num}?",
                                       min_values=1,
                                       max_values=1,
                                       options=initial_options)

            async def update_match(interaction, round_num=round_num):
                await interaction.response.defer()
                if interaction.data['values'][0] == 'p1':
                    self.pair_info[f'r{round_num}_winner'] = p1
                elif interaction.data['values'][0] == 'p2':
                    self.pair_info[f'r{round_num}_winner'] = p2
                else:
                    self.pair_info[f'r{round_num}_winner'] = 'draw'

            select.callback = update_match
            select_menus.append(select)
        return select_menus


class WinView(SessionView):
    def __init__(self, session, ctx):
        super().__init__(session=session, ctx=ctx)

    def log_session(self):
        log = ""

        # User list
        log += "UL:"
        for user in self.session.users:
            log += f"{user.get_nick()}\n"

        # Match results
        for match_number in range(len(self.session.matches)):
            log += f"\n\nM{match_number+1}:"
            for pairing in self.session.matches[len(self.session.matches)].values():
                p1_wins, p2_wins = self.session.get_match_results(pairing)
                log += f"{pairing['p1'].get_nick()}=={p1_wins}//{pairing['p2'].get_nick()}=={p2_wins}\n"

        # Elo results
        log += f"\n\nELO:"
        for user in self.session.users:
            log += f"{user.get_nick()}=={user.original_elo}//{self.session.database.get_elo(user.get_name())}\n"

        # Rank results
        log += f"\n\nRANK:"
        for user in self.session.users:
            log += f"{user.get_nick()}=={user.original_rank}//{self.session.database.get_rank(user.get_name())}\n"

        # Record in database
        self.session.database.set_log(log)

    def create_embed(self):
        self.embed.title = f"Winners"

        if len(self.session.game_winners) > 1:
            self.embed.description = "Congratulations to the following players for winning!\n" \
                                f"{', '.join([winner.get_nick() for winner in self.session.game_winners])}"
        elif len(self.session.game_winners) == 0:
            self.embed.description = "Looks like nobody wins this session! Better luck next time!"
        else:
            self.embed.description = f"Congratulations to {self.session.game_winners[0].get_nick()} for winning!"

        for user in self.session.users:
            spacing = 25 - len(user.get_nick())
            if spacing % 2 == 0:
                left_spacing = ' ' * int(spacing / 2)
                right_spacing = ' ' * int(spacing / 2)
            else:
                left_spacing = ' ' * int(spacing / 2)
                right_spacing = ' ' * (int(spacing / 2) + 1)

            new_elo, new_rank = self.session.database.get_elo(user.get_name()), \
                                self.session.database.get_rank(user.get_name())

            self.embed.add_field(name=f"`{left_spacing}{user.get_nick()}{right_spacing}`",
                                 value=f"> `Wins/Losses: ( {user.get_wins()} / {user.get_losses()} )`"
                                       f"\n> `{user.original_elo} -> {new_elo}`\n"
                                       f"> `Rank {user.original_rank} -> {new_rank}`",
                                 inline=False)

        self.log_session()

        return self.embed

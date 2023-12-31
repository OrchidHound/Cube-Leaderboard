import random
import discord


class SessionView(discord.ui.View):
    def __init__(self, session_list, session, ctx):
        super().__init__(timeout=None)
        self.session_list = session_list
        self.session = session
        self.ctx = ctx
        self.message = ""
        self.mode = 1
        self.pairs = []

    async def send(self, ctx):
        self.message = await ctx.send(embed=self.create_embed(), view=self)
        await self.update_message()

    async def update_message(self):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(), view=self)
        for pair_view in self.session.active:
            await pair_view.send(self.ctx)

    def create_embed(self):
        pass

    def update_buttons(self):
        pass


class MatchView(SessionView):
    def __init__(self, session_list, session, ctx, pair_info, key):
        super().__init__(session_list=session_list, session=session, ctx=ctx)
        self.pair_info = pair_info
        self.key = key
        for listing in self.versus_listings():
            self.add_item(listing)

    async def send(self, ctx):
        self.message = await ctx.send(embed=self.create_embed(), view=self)

    def create_embed(self):
        return discord.Embed(title=f"{self.pair_info['p1'].get_name()} vs. {self.pair_info['p2'].get_name()}")

    def versus_listings(self):
        select_menus = []
        for round_num in [1, 2, 3]:
            p1 = self.pair_info['p1']
            p2 = self.pair_info['p2']

            initial_options = [
                discord.SelectOption(label=f"{p1.get_name()}", value='p1'),
                discord.SelectOption(label=f"{p2.get_name()}", value='p2')
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


class HeadView(SessionView):
    def __init__(self, session_list, session, ctx):
        super().__init__(session_list=session_list, session=session, ctx=ctx)
        self.confirm_roster = self.roster_button()
        self.confirm_draft = self.draft_button()
        self.cancel = self.cancel_button()
        self.submit_match = self.submit_match_button()

    def create_embed(self):
        embed = discord.Embed(title=f"Session {self.session.session_id}")

        match self.mode:
            case 0:
                for session in self.session_list:
                    if session.session_id == self.session.session_id:
                        self.session_list.remove(session)

                embed.title = ""
                embed.description = f"Session {self.session.session_id} cancelled."
            case 1:
                embed.description = "Start with these users?"
                for user in self.session.get_users():
                    embed.add_field(name="", value=f"> {user.get_name()}", inline=False)
            case 2:
                seats = list(range(1, len(self.session.get_users()) + 1))
                player_amt = len(self.session.get_users())
                pack_size = 15 if player_amt <= 8 else 15 + (player_amt - 8)
                draft_warning = 'Since there are less than 8 players, consider using a house rule for drafting.\n'

                embed.description = "Let's start drafting!\n" \
                                    f"Since there are {player_amt} players, each player will make 3 packs of " \
                                    f"{pack_size}.\n" \
                                    f"{draft_warning if player_amt < 8 else ''}" \
                                    "\nSeating order is as follows:"

                for user in self.session.get_users():
                    user.seat = random.choice(seats)
                    seats.remove(user.seat)
                for seat_number in range(player_amt + 1):
                    for user in self.session.get_users():
                        if user.seat == seat_number:
                            embed.add_field(name=f"\n> Seat {user.seat} ", value=f"> {user.get_name()}", inline=False)
            case 3:
                match = self.session.new_match()
                bye_message = ""
                if self.session.bye is not None:
                    bye_user = self.session.bye
                    bye_message = f"Since there are an odd number of players, {bye_user.get_name()} gets a bye.\n"

                embed.description = "It's time to play!\n" + \
                                    bye_message + \
                                    f"The match {len(self.session.matches)} pairings are:"

                for key, value in match.items():
                    embed.add_field(name=f"",
                                    value=f"> "
                                          f"`{value['p1'].get_name()} "
                                          f"( {value['p1'].get_wins()} / {value['p1'].get_losses()} ) "
                                          f"\t\t--VS--\t\t"
                                          f"{value['p2'].get_name()} "
                                          f"( {value['p2'].get_wins()} / {value['p2'].get_losses()} )`",
                                    inline=False)
                    pair_view = MatchView(self.session_list, self.session, self.ctx, value, key)
                    self.session.active.append(pair_view)
            case 5:
                winner = self.session.get_winner()
                embed.description = f"Congratulations to {winner.get_name()} for winning!"
                for user in self.session.get_users():
                    embed.add_field(name=f"{user.get_name()}",
                                    value=f"( {user.get_wins()} / {user.get_losses()} )",
                                    inline=False)
                for session in self.session_list:
                    if session.session_id == self.session.session_id:
                        self.session_list.remove(session)

        return embed

    def update_buttons(self):
        self.clear_items()
        match self.mode:
            case 1:
                self.add_item(self.cancel)
                self.add_item(self.confirm_roster)
            case 2:
                self.add_item(self.cancel)
                self.add_item(self.confirm_draft)
            case 3:
                self.add_item(self.submit_match)
            case 4:
                pass
                # self.add_item(self.nevermind)
                # self.add_item(self.confirm_players)

    def cancel_button(self):
        button = discord.ui.Button(label="Cancel",
                                   style=discord.ButtonStyle.danger)

        async def cancel(interaction: discord.Interaction):
            await interaction.response.defer()
            await self.session.delete_active_matches(self.ctx)
            self.mode = 0
            await self.update_message()

        button.callback = cancel
        return button

    def roster_button(self):
        button = discord.ui.Button(label="Confirm Roster",
                                   style=discord.ButtonStyle.green)

        async def confirm_roster(interaction: discord.Interaction):
            await interaction.response.defer()
            self.mode = 2
            await self.update_message()

        button.callback = confirm_roster
        return button

    def draft_button(self):
        button = discord.ui.Button(label="Draft Complete",
                                   style=discord.ButtonStyle.green)

        async def confirm_draft(interaction: discord.Interaction):
            await interaction.response.defer()
            self.mode = 3
            await self.update_message()

        button.callback = confirm_draft
        return button

    def submit_match_button(self):
        button = discord.ui.Button(label="Submit",
                                   style=discord.ButtonStyle.green)

        async def submit_match(interaction: discord.Interaction):
            failed = False
            await interaction.response.defer()
            for pairing in self.session.matches[len(self.session.matches)].values():
                if pairing['r1_winner'] is None or pairing['r2_winner'] is None or pairing['r1_winner'] is None:
                    failed = True
                    await self.ctx.send(f"Invalid round data for {pairing['p1'].get_name()} vs. {pairing['p2'].get_name()}.",
                                        delete_after=10)
            if not failed:
                self.session.update_winners()
                await self.session.delete_active_matches(self.ctx)
                winner = self.session.get_winner()
                if winner is not None:
                    self.mode = 5
                await self.update_message()

        button.callback = submit_match
        return button

    def edit_players_button(self):
        button = discord.ui.Button(label="Edit Players",
                                   style=discord.ButtonStyle.blurple)

        async def edit_players(interaction: discord.Interaction):
            await interaction.response.defer()
            self.mode = 4
            await self.update_message()

        button.callback = edit_players
        return button

    def confirm_players_button(self):
        button = discord.ui.Button(label="Confirm",
                                   style=discord.ButtonStyle.green)

        async def confirm_players(interaction: discord.Interaction):
            await interaction.response.defer()
            self.mode = 3
            await self.update_message()

        button.callback = confirm_players
        return button

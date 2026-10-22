from bot.decorators import has_required_role
import asyncio
import random
import discord


class PersistentView(discord.ui.View):
    def __init__(self, ctx, session, session_id):
        super().__init__(timeout=None)
        self.session = session
        self.session_id = session_id
        self.ctx = ctx
        # Serializes button presses so slow callbacks can't be re-entered by repeated clicks
        self.lock = asyncio.Lock()
        self.embed = discord.Embed(color=0x24bc9c)
        self.embed.set_image(url="https://cdn.discordapp.com/attachments/1186834070085316691/1226447322368577608/"
                                 "footer.png?ex=6624cd13&is=66125813&hm="
                                 "93d7af4b304e9a3c4026264aa311e4684e27df5d1057f07f4a57234eb9ca98b5&")

    # Spacing for formatting names in Discord embeds
    def spacing(self, player_nick):
        return ' ' * (self.session.longest - len(player_nick))

    # Clear and add buttons to the view
    def add_buttons(self, buttons):
        self.clear_items()
        for button in buttons:
            self.add_item(button)
        self.add_item(self.create_button("Cancel", "red", "cancel", self.cancel_callback))

    # Create a button with specified parameters
    def create_button(self, label, style, custom_id, custom_callback, disabled=False):
        style = getattr(discord.ButtonStyle, style)
        button = CallbackButton(
            label=label,
            style=style,
            custom_id=custom_id,
            custom_callback=custom_callback,
            disabled=disabled)
        return button

    # Embed for session cancellation
    async def cancel_embed(self):
        self.embed.title = "Session Cancelled"
        self.embed.description = "The session has been cancelled."
        return self.embed

    # Callback for cancel button
    async def cancel_callback(self, interaction, button: discord.ui.Button):
        self.clear_items()
        self.embed.clear_fields()
        self.embed = await self.cancel_embed()
        await asyncio.to_thread(self.session.commit_log)
        await interaction.edit_original_response(view=self, embed=self.embed)
        # Unregister the view so it no longer stays in memory
        self.stop()


class SessionView(PersistentView):
    def __init__(self, ctx, session, session_id):
        super().__init__(ctx, session, session_id)
        self.add_buttons([self.create_button("Generate Seating", "green", "seating", self.seating_callback)])
        self.players_to_drop = []
        self.embed.set_footer(text=self.session.datetime)

    # Embed for roster
    def roster_embed(self):
        self.embed.title = "Roster"
        self.embed.description = "Session contains these users:"
        # Format message for each player
        for player in self.session.get_active_players():
            spacing = ' ' * (self.session.longest - len(player.get_trimmed_nick()))
            self.embed.add_field(
                name="",
                value=f"> `{player.get_trimmed_nick()}{spacing} | {player.original_elo}`",
                inline=False)
        return self.embed

    # Embed for seating order
    def seating_embed(self):
        self.embed.title = "Seating"
        # Create a list of seats for the session
        seats = list(range(1, len(self.session.get_active_players()) + 1))
        player_amt = len(self.session.get_active_players())
        # Set embed description
        draft_warning = "Since there are less than 8 players, consider using a house rule for drafting.\n"
        self.embed.description = \
            f"""
            Let's start drafting!\n
            {draft_warning if player_amt < 8 else ''} \n
            Seating order is as follows:
            """
        # Randomly assign seats to players
        for player in self.session.players:
            player.seat = random.choice(seats)
            seats.remove(player.seat)
        for seat_number in range(player_amt + 1):
            for player in self.session.get_active_players():
                if player.seat == seat_number:
                    self.embed.add_field(
                        name=f"\n> Seat {player.seat} ", value=f"> `{player.get_trimmed_nick()}`",
                        inline=False)
        return self.embed

    # Embed for match pairings
    def match_embed(self):
        self.embed.title = f"Match {self.session.active_match_num+1} Pairings"
        # Create a new match and store match info for easier access
        self.session.new_match()
        current_match = self.session.get_current_match()
        match_num = self.session.active_match_num
        # Create embed description and insert bye message if necessary
        self.embed.description = \
            f"""
            It's time to play!\n
            {f"Since there are an odd number of players, {current_match.bye.nick} gets a bye."
            if current_match.bye is not None else ""}\n
            The match {match_num} pairings are:
            """
        # Add an embed field for each pairing
        for pairing in current_match.pairings:
            p1_record = self.session.get_player_record(pairing.p1)
            p2_record = self.session.get_player_record(pairing.p2)
            self.embed.add_field(
                name=f"",
                value=(
                    f"```{pairing.p1.get_trimmed_nick()} {self.spacing(pairing.p1.get_trimmed_nick())}"
                    f"( {p1_record['wins']} / {p1_record['losses']} )\n\n"
                    f"{' ' * ((self.session.longest + 2) // 2)}--VS--\n\n"
                    f"{pairing.p2.get_trimmed_nick()} {self.spacing(pairing.p2.get_trimmed_nick())}"
                    f"( {p2_record['wins']} / {p2_record['losses']} )\n"
                    f"{'_' * (self.session.longest + 10)}```"),
                inline=False)
        return self.embed

    # Embed for intermission
    def intermission_embed(self):
        self.embed.title = "Intermission"
        self.embed.description = "The current match has concluded. What would you like to do next?"
        return self.embed

    # Embed for dropping users
    def drop_users_embed(self):
        self.embed.title = "Drop Users"
        self.embed.description = "Which users would you like to drop from the session?"
        return self.embed

    # Embed for winners
    def winners_embed(self):
        self.embed.title = "Winners"
        self.clear_items()
        if len(self.session.get_undefeated_players()) > 1:
            self.embed.description = f"""
                Congratulations to the following players for winning!\n
                {", ".join([player.get_trimmed_nick() for player in self.session.get_undefeated_players()])}
                """
        elif len(self.session.get_undefeated_players()) == 1:
            self.embed.description = f"""
                Congratulations to {self.session.get_undefeated_players()[0].get_trimmed_nick()} for winning!
                """
        else:
            self.embed.description = "Looks like nobody wins this session. Better luck next time!"

        for player in self.session.players:
            # Create a field for each player with their new ELO and rank
            spacing = 25 - len(player.get_trimmed_nick())
            if spacing % 2 == 0:
                left_spacing = ' ' * int(spacing / 2)
                right_spacing = ' ' * int(spacing / 2)
            else:
                left_spacing = ' ' * int(spacing / 2)
                right_spacing = ' ' * (int(spacing / 2) + 1)
            self.embed.add_field(
                name=f"`{left_spacing}{player.get_trimmed_nick()}{right_spacing}`",
                value=(
                    f"> `Wins/Losses: ( {self.session.get_player_record(player)['wins']} "
                    f"/ {self.session.get_player_record(player)['losses']} )`\n"
                    f"> `{player.original_elo} -> {player.new_elo}`\n"
                    f"> `Rank {player.original_rank} -> {player.new_rank}`"),
                inline=False)

        return self.embed

    # Persist the finished session; blocking database work, so run it in a worker thread
    def record_session(self):
        self.session.commit_elo_scores()
        self.session.commit_log()
        for player in self.session.players:
            if player.id is not None:
                self.session.db.increment_games_played(player.id)

    # Delete the pairing messages. The interaction token that created them expires after 15 minutes,
    # so fall back to deleting through the channel
    async def delete_pairing_views(self, interaction, pairings):
        async def delete(pairing):
            message = pairing.view.response
            try:
                await message.delete()
            except discord.NotFound:
                pass
            except discord.HTTPException:
                try:
                    await interaction.channel.get_partial_message(message.id).delete()
                except discord.HTTPException:
                    pass
            pairing.view = None

        await asyncio.gather(*(delete(p) for p in pairings if p.view is not None))

    # Callback for seating button
    async def seating_callback(self, interaction, button: discord.ui.Button):
        self.embed.clear_fields()
        self.embed = self.seating_embed()
        self.add_buttons([self.create_button("Start Match", "green", "next_match", self.next_match_callback)])
        await interaction.edit_original_response(view=self, embed=self.embed)

    # Callback for next match button
    async def next_match_callback(self, interaction, button: discord.ui.Button):
        if self.session.active_match_num >= 3:
            return
        self.embed.clear_fields()
        self.embed = self.match_embed()
        self.add_buttons([self.create_button("Enter Results", "green", "enter_results", self.enter_results_callback)])
        await interaction.edit_original_response(view=self, embed=self.embed)

    # Callback for enter results button
    async def enter_results_callback(self, interaction, button: discord.ui.Button):
        pairings = self.session.get_current_match().pairings
        # Delete any existing pairing views
        await self.delete_pairing_views(interaction, pairings)
        # Create a new view for each pairing in the current match
        for pairing in pairings:
            pairing_view = PairView(pairing.p1, pairing.p2)
            pairing.view = pairing_view
            pairing_view.response = await interaction.followup.send(view=pairing_view, wait=True)
        self.add_buttons([self.create_button("Finalize", "green", "finalize", self.finalize_match_callback),
                          self.create_button("Refresh", "green", "enter_results", self.enter_results_callback)])
        await interaction.edit_original_response(view=self, embed=self.embed)

    # Callback for finalize match button
    async def finalize_match_callback(self, interaction, button: discord.ui.Button):
        pairings = self.session.get_current_match().pairings
        for pairing in pairings:
            if pairing.view is not None:
                pairing.wins = pairing.view.wins
            if pairing.view is None or pairing.get_match_winner() is None:
                await interaction.followup.send(
                    "Please enter results for all pairings before finalizing.",
                    ephemeral=True
                )
                return
        for pairing in pairings:
            pairing.adjust_elo()
        await self.delete_pairing_views(interaction, pairings)
        self.session.log.add_match(self.session.get_current_match(), self.session.active_match_num)
        self.embed.clear_fields()
        finished = self.session.active_match_num >= 3
        if not finished:
            self.embed = self.intermission_embed()
            self.add_buttons([
                self.create_button("Next Match", "green", "next_match", self.next_match_callback),
                self.create_button("Drop Users", "green", "drop_users", self.drop_users_callback)
            ])
        else:
            await asyncio.to_thread(self.record_session)
            self.embed = self.winners_embed()

        await interaction.edit_original_response(view=self, embed=self.embed)
        if finished:
            self.stop()

    # Callback for drop users button
    async def drop_users_callback(self, interaction, button: discord.ui.Button):
        self.add_buttons([self.create_button("Finalize Drops", "green", "finalize_drops", self.finalize_drops_callback)])
        selector = CallbackSelector(
            placeholder="Select the users to drop",
            min_values=0,
            max_values=len(self.session.get_active_players()),
            options=[
                discord.SelectOption(
                    label=f"{player.get_trimmed_nick()}",
                    value=player.tag)
                for player in self.session.get_active_players()],
            custom_callback=self.selector_callback
        )
        self.add_item(selector)
        self.embed.clear_fields()
        self.embed = self.drop_users_embed()
        await interaction.edit_original_response(view=self, embed=self.embed)

    # Callback for finalize drops button
    async def finalize_drops_callback(self, interaction, button: discord.ui.Button):
        self.session.drop_players(self.players_to_drop)
        self.players_to_drop.clear()
        self.embed.clear_fields()
        self.embed = self.intermission_embed()
        self.add_buttons([
            self.create_button("Next Match", "green", "next_match", self.next_match_callback),
            self.create_button("Drop Users", "green", "drop_users", self.drop_users_callback)
        ])
        await interaction.edit_original_response(view=self, embed=self.embed)

    # Callback for selector
    async def selector_callback(self, interaction, select: discord.ui.Select):
        await interaction.response.defer()
        self.players_to_drop = select.values


class PairView(discord.ui.View):
    def __init__(self, p1, p2):
        super().__init__(timeout=None)
        self.p1 = p1
        self.p2 = p2
        self.wins = {p1: 0, p2: 0}
        self.add_selector()
        self.response = None

    def add_selector(self):
        selector = CallbackSelector(
            placeholder="Select the winner",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=f"{self.p1.get_trimmed_nick()} wins 2-0", value="p1_2-0"),
                discord.SelectOption(label=f"{self.p1.get_trimmed_nick()} wins 2-1", value="p1_2-1"),
                discord.SelectOption(label=f"{self.p2.get_trimmed_nick()} wins 2-0", value="p2_2-0"),
                discord.SelectOption(label=f"{self.p2.get_trimmed_nick()} wins 2-1", value="p2_2-1")
            ],
            custom_callback=self.selector_callback
        )
        self.add_item(selector)

    async def selector_callback(self, interaction, select: discord.ui.Select):
        await interaction.response.defer()
        if select.values[0] == "p1_2-0":
            self.wins[self.p1] = 2
        elif select.values[0] == "p1_2-1":
            self.wins[self.p1] = 2
            self.wins[self.p2] = 1
        elif select.values[0] == "p2_2-0":
            self.wins[self.p2] = 2
        elif select.values[0] == "p2_2-1":
            self.wins[self.p2] = 2
            self.wins[self.p1] = 1


class CallbackButton(discord.ui.Button):
    def __init__(self, *, label, style, custom_id, custom_callback, disabled=False):
        super().__init__(
            label=label,
            style=style,
            custom_id=custom_id,
            disabled=disabled)
        self.custom_callback = custom_callback

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.lock.locked():
            await interaction.response.send_message("Still processing the previous action, please wait.",
                                                    ephemeral=True)
            return
        async with view.lock:
            # Acknowledge within Discord's 3 second limit before doing any slow work
            await interaction.response.defer()
            await self.custom_callback(interaction, self)


class CallbackSelector(discord.ui.Select):
    def __init__(self, *, placeholder, min_values, max_values, options, custom_callback, disabled=False):
        super().__init__(
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            options=options,
            disabled=disabled)
        self.custom_callback = custom_callback

    async def callback(self, interaction: discord.Interaction):
        await self.custom_callback(interaction, self)

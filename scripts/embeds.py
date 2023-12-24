import math
import random

import discord


class SessionView(discord.ui.View):
    class MatchView(discord.ui.View):
        def __init__(self, session, user_pair):
            super().__init__(timeout=None)
            self.session = session
            self.user_pair = user_pair
            self.message = ""

        async def send(self, ctx):
            self.message = await ctx.send(view=self)
            await self.update_message()

    def __init__(self, session_list, session):
        super().__init__(timeout=None)
        self.session_list = session_list
        self.session = session
        self.message = ""
        self.mode = 1

    async def send(self, ctx):
        self.message = await ctx.send(view=self)
        await self.update_message()

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
                pairings = self.session.new_round()
                embed.description = "It's time to play!\n" \
                                    f"The match {len(self.session.matches)} pairings are:"

                for pair in pairings.values():
                    embed.add_field(name=f"", value=f"> "
                                                    f"{pair[0].get_name()} "
                                                    f"VS. "
                                                    f"{pair[1].get_name()}", inline=False)

        return embed

    async def update_message(self):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(), view=self)

    def update_buttons(self):
        match self.mode:
            case 0:
                self.clear_items()
            case 1:
                self.remove_item(self.confirm_draft_button)
            case 2:
                self.remove_item(self.confirm_roster_button)
                self.add_item(self.confirm_draft_button)
            case 3:
                pass

    @discord.ui.button(label="Cancel",
                       style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.mode = 0
        await self.update_message()

    @discord.ui.button(label="Confirm Roster",
                       style=discord.ButtonStyle.green)
    async def confirm_roster_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.mode = 2
        await self.update_message()

    @discord.ui.button(label="Draft Complete",
                       style=discord.ButtonStyle.green)
    async def confirm_draft_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.mode = 3
        await self.update_message()


# class SessionView(discord.ui.View):
#     def __init__(self, session_list, session):
#         super().__init__(timeout=None)
#         self.session_list = session_list
#         self.session = session
#         self.message = ""
#
#     async def send(self, ctx):
#         self.message = await ctx.send(view=self)
#         await self.message.edit(embed=self.create_embed(), view=self)
#
#     def create_embed(self):
#         embed = discord.Embed(title=f"Session {self.session.session_id}")
#         embed.description = "Start with these users?"
#         for user in self.session.get_users():
#             embed.add_field(name="", value=f"| {user.get_name()}", inline=False)
#         return embed
#
#     @discord.ui.button(label="Cancel",
#                        style=discord.ButtonStyle.primary)
#     async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
#         self.style = discord.ButtonStyle.danger
#         await interaction.response.defer()
#         cancel_view = Cancel(session_list=self.session_list, session=self.session, message=self.message)
#         await cancel_view.send()
#
#     @discord.ui.button(label="Confirm",
#                        style=discord.ButtonStyle.primary)
#     async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
#         await interaction.response.defer()
#         seating_view = Seating(session_list=self.session_list, session=self.session, message=self.message)
#         await seating_view.send()
#
#
# class Cancel(discord.ui.View):
#     def __init__(self, session_list, session, message):
#         super().__init__(timeout=0)
#         self.session_list = session_list
#         self.session = session
#         self.message = message
#
#     async def send(self):
#         for session in self.session_list:
#             if session.session_id == self.session.session_id:
#                 self.session_list.remove(session)
#         await self.message.edit(embed=self.create_embed(), view=self)
#
#     def create_embed(self):
#         embed = discord.Embed(title="")
#         embed.description = f"Session {self.session.session_id} cancelled."
#         return embed
#
#
# class Seating(discord.ui.View):
#     def __init__(self, session_list, session, message):
#         super().__init__(timeout=None)
#         self.session_list = session_list
#         self.session = session
#         self.message = message
#
#     async def send(self):
#         await self.message.edit(embed=self.create_embed(), view=self)
#
#     def create_embed(self):
#         seats = list(range(1, len(self.session.get_users())+1))
#         player_amt = len(self.session.get_users())
#         pack_size = 15 if player_amt <= 8 else 15+(player_amt-8)
#         draft_warning = 'Since there are less than 8 players, consider using a house rule for drafting.\n'
#
#         embed = discord.Embed(title=f"Session {self.session.get_id()}")
#         embed.description = "Let's start drafting!\n" \
#                             f"Since there are {player_amt} players, each player will make 3 packs of {pack_size}.\n" \
#                             f"{draft_warning if player_amt < 8 else ''}" \
#                             "\nSeating order is as follows:"
#
#         for user in self.session.get_users():
#             user.seat = random.choice(seats)
#             seats.remove(user.seat)
#         for seat_number in range(len(self.session.get_users())+1):
#             for user in self.session.get_users():
#                 if user.seat == seat_number:
#                     embed.add_field(name=f"| Seat {user.seat} ", value=f"| {user.get_name()}", inline=False)
#
#         return embed
#
#     @discord.ui.button(label="Cancel",
#                        style=discord.ButtonStyle.primary)
#     async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
#         await interaction.response.defer()
#         cancel_view = Cancel(session_list=self.session_list, session=self.session, message=self.message)
#         await cancel_view.send()
#
#     @discord.ui.button(label="Confirm",
#                        style=discord.ButtonStyle.primary)
#     async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
#         await interaction.response.defer()
#         print("Hooray!")

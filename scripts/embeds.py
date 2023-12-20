import math
import discord


class SessionView(discord.ui.View):
    def __init__(self, session_list, session):
        super().__init__(timeout=None)
        self.session_list = session_list
        self.session = session
        self.message = ""

    async def send(self, ctx):
        self.message = await ctx.send(view=self)
        await self.message.edit(embed=self.create_embed(), view=self)

    def create_embed(self):
        embed = discord.Embed(title=f"Session {self.session.session_id}")
        embed.description = "Start with these users?"
        for user in self.session.get_users():
            embed.add_field(name="", value=f"{user.name}")
        return embed

    @discord.ui.button(label="Cancel",
                       style=discord.ButtonStyle.primary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        cancel_view = Cancel(session_list=self.session_list, session=self.session, message=self.message)
        await cancel_view.send()

    @discord.ui.button(label="Confirm",
                       style=discord.ButtonStyle.primary)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        seating_view = Seating(session_list=self.session_list, session=self.session, message=self.message)
        await seating_view.send()


class Cancel(discord.ui.View):
    def __init__(self, session_list, session, message):
        super().__init__(timeout=0)
        self.session_list = session_list
        self.session = session
        self.message = message

    async def send(self):
        for session in self.session_list:
            if session.session_id == self.session.session_id:
                self.session_list.remove(session)
        await self.message.edit(embed=self.create_embed(), view=self)

    def create_embed(self):
        embed = discord.Embed(title="")
        embed.description = f"Session {self.session.session_id} cancelled."
        return embed


class Seating(discord.ui.View):
    def __init__(self, session_list, session, message):
        super().__init__(timeout=None)
        self.session_list = session_list
        self.session = session
        self.message = message

    async def send(self):
        await self.message.edit(embed=self.create_embed(), view=self)

    def create_embed(self):
        seat = 1
        embed = discord.Embed(title=f"Session {self.session.get_id()}")
        embed.description = "Let's start drafting!\n" \
                            "Seating order is as follows:"
        for user in self.session.get_users():
            user.seat = seat
            embed.add_field(name=f"| Seat {seat} ", value=f"| {user.name}", inline=True)
            seat += 1
        return embed

    @discord.ui.button(label="Cancel",
                       style=discord.ButtonStyle.primary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        cancel_view = Cancel(session_list=self.session_list, session=self.session, message=self.message)
        await cancel_view.send()

    @discord.ui.button(label="Confirm",
                       style=discord.ButtonStyle.primary)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        print("Hooray!")

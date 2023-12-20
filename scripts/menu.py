import discord


class round_winner(discord.ui.View):
    def __init__(self, player_one, player_two, round_number):
        super().__init__()
        self.player_one = player_one
        self.player_two = player_two,
        self.round_number = round_number

    def make_list(self):
        @discord.ui.select(
            placeholder=f"Who won round {self.round_number}?",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=f"{self.player_one}"
                ),
                discord.SelectOption(
                    label=f"{self.player_two}"
                ),
                discord.SelectOption(
                    label="Draw",
                    description="Either the round ended in a draw or there wasn't enough time to play the round."
                )
            ]
        )
        async def select_callback(self, select, interaction):
            await interaction.response.send_message(f"{select.values[0]} won round {self.round_number}.")

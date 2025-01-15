class Player:
    def __init__(self, player_id, player_tag, nick, original_elo, original_rank):
        self.id = player_id
        self.tag = player_tag
        self.nick = nick
        self.original_elo = original_elo
        self.original_rank = original_rank
        self.new_elo = original_elo
        self.new_rank = original_rank
        self.seat = 0

    # Get nickname of player cut off at the 20th character for formatting purposes
    def get_trimmed_nick(self):
        return self.nick[:19]



class User:
    def __init__(self, user_info):
        self.user_info = user_info
        self.original_elo = 1200
        self.original_rank = 0
        self.record = {'wins': 0, 'losses': 0}
        self.seat = 0

    def get_roles(self):
        if type(self.user_info) == str:
            return []
        else:
            return self.user_info.roles

    def get_wins(self):
        return self.record['wins']

    def get_losses(self):
        return self.record['losses']

    def get_name(self):
        if type(self.user_info) == str:
            return self.user_info
        else:
            return self.user_info.name

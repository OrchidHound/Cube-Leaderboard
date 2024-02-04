from discord.ext import commands


async def convert(ctx, user_str):
    try:
        return await commands.MemberConverter().convert(ctx, user_str)
    except commands.MemberNotFound:
        return user_str
    except TypeError:
        return None


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
        if self.user_info is None:
            return None
        return str(self.user_info)

    def get_nick(self):
        if type(self.user_info) == str:
            nick = self.user_info
        elif self.user_info.nick is None:
            nick = str(self.user_info.display_name)
        else:
            nick = str(self.user_info.nick)

        if len(nick) > 19:
            nick = nick[:19]

        return nick

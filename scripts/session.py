import math
import random


def assign_id(session_list):
    existing_ids = [session.get_id() for session in session_list]
    if len(session_list) > 0:
        if min(existing_ids) == 10:
            return None

        for i in range(1, 10):
            if i not in existing_ids:
                return i
    return 1


def get_session(session_list, session_id):
    for session in session_list:
        if session.get_id() == session_id:
            return session
    return None


def get_session_users(session):
    output = ""
    for user in session.get_users():
        if len(output) > 0:
            output = f"{output}, {user.user_info.name}"
        else:
            output = f"{user.user_info.name}"
    return output


class Session:
    class User:
        def __init__(self, user_info):
            self.user_info = user_info
            self.data = {}
            self.seat = 0

        def update_date(self, opponent, score):
            self.data = {opponent: score}

        def get_name(self):
            if type(self.user_info) == str:
                return self.user_info
            else:
                return self.user_info.name

    def __init__(self, server, users, session_id):
        self.server = server
        self.users = [self.User(user) for user in users]
        self.session_id = session_id
        self.matches = {}
        self.bye = None

    def get_users(self):
        return [user for user in self.users]

    def get_id(self):
        return self.session_id

    def new_round(self):
        match_num = len(self.matches)+1
        self.matches[match_num] = {}
        unassigned_players = self.get_users()

        for pair_num in range(math.floor(len(self.get_users()) / 2)):
            self.matches[match_num][pair_num] = []
            for player_num in range(2):
                player = random.choice(unassigned_players)
                self.matches[match_num][pair_num].append(player)
                unassigned_players.remove(player)
            if len(unassigned_players) == 1:
                self.bye = unassigned_players[0]

        return self.matches[match_num]

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
            self.record = {'wins': 0, 'losses': 0}
            self.seat = 0

        def get_wins(self):
            return self.record['wins']

        def get_losses(self):
            return self.record['losses']

        def get_name(self):
            if type(self.user_info) == str:
                return self.user_info
            else:
                return self.user_info.name

    def __init__(self, server, users, session_id):
        self.server = server
        self.users = [self.User(user) for user in users]
        self.session_id = session_id
        self.players_to_remove = []
        self.removed_players = []
        self.game_winners = None
        self.matches = {}
        self.active = []
        self.bye = None

    def update_winners(self):
        for match in self.matches[len(self.matches)].values():
            match['p2'].record[match['p1']] = 0
            match['p1'].record[match['p2']] = 0
            p1_score = match['p2'].record[match['p1']]
            p2_score = match['p1'].record[match['p2']]
            for round_winner in [match['r1_winner'], match['r2_winner'], match['r3_winner']]:
                try:
                    if round_winner == match['p1']:
                        p1_score += 1
                        p2_score -= 1
                    elif round_winner == match['p2']:
                        p2_score += 1
                        p1_score -= 1
                except TypeError:
                    pass
            if p1_score > p2_score:
                match['p1'].record['wins'] += 1
                match['p2'].record['losses'] += 1
            elif p1_score < p2_score:
                match['p2'].record['wins'] += 1
                match['p1'].record['losses'] += 1

    def get_active_users(self):
        removed_player_names = [user.get_name() for user in self.removed_players]
        return [user for user in self.users if user.get_name() not in removed_player_names]

    def get_id(self):
        return self.session_id

    def get_prior_opponents(self, player):
        prior_opponents = []
        for key, match in self.matches.items():
            if key < len(self.matches):
                for pair in match.values():
                    if pair['p1'] == player:
                        prior_opponents.append(pair['p2'])
                        break
                    elif pair['p2'] == player:
                        prior_opponents.append(pair['p1'])
                        break
        return prior_opponents

    def set_game_winners(self, premature=False):
        winners = [user for user in self.get_active_users() if user.record['losses'] == 0]
        if premature:
            self.game_winners = winners
        elif len(winners) == 1:
            self.game_winners = winners[0]
        else:
            return None

    def match_players(self, current_player, player_list):
        prior_opponents = self.get_prior_opponents(current_player)
        try:
            matched_player = random.choice(
                [user for user in player_list if user not in prior_opponents]
            )
            player_list.remove(matched_player)
            return matched_player, True
        except IndexError:
            return None, False

    def create_match_pair(self, match_num, p1, p2):
        if p1 is not None and p2 is not None:
            self.matches[match_num][len(self.matches[match_num]) + 1] = {}
            pair_info = self.matches[match_num][len(self.matches[match_num])]
            pair_info['p1'] = p1
            pair_info['p2'] = p2
            pair_info["r1_winner"], pair_info["r2_winner"], pair_info["r3_winner"] = None, None, None

    def new_match(self):
        valid = False
        match_num = len(self.matches) + 1

        while not valid:
            valid = True
            self.matches[match_num] = {}
            unassigned_winners = [user for user in self.get_active_users() if user.record['losses'] == 0]
            unassigned_losers = {1: [], 2: []}
            for i in range(1, match_num):
                unassigned_losers[i] = [user for user in self.get_active_users() if user.record['losses'] == i]

            while unassigned_winners:
                matched_player = None

                if self.bye is not None and self.bye in unassigned_winners:
                    current_player = self.bye
                    unassigned_winners.remove(self.bye)
                    self.bye = None
                else:
                    current_player = random.choice(unassigned_winners)
                    unassigned_winners.remove(current_player)

                if len(unassigned_winners) > 0:
                    matched_player, valid = self.match_players(current_player, unassigned_winners)
                elif len(unassigned_winners) == 0 and unassigned_losers[1]:
                    matched_player, valid = self.match_players(current_player, unassigned_losers[1])

                if len(unassigned_winners) == 1 and not unassigned_losers[1]:
                    self.bye = unassigned_winners.pop()

                self.create_match_pair(match_num, current_player, matched_player)

            while unassigned_losers[1] or unassigned_losers[2]:
                current_player = None
                matched_player = None

                if self.bye is not None:
                    current_player = self.bye
                    unassigned_losers[1].remove(current_player)
                    self.bye = None
                    if len(unassigned_losers[1]) > 1:
                        matched_player, valid = self.match_players(current_player, unassigned_losers[1])
                    elif len(unassigned_losers[2]) > 1:
                        matched_player, valid = self.match_players(current_player, unassigned_losers[2])
                elif len(unassigned_losers[1]) > 1:
                    current_player = random.choice(unassigned_losers[1])
                    unassigned_losers[1].remove(current_player)
                    matched_player, valid = self.match_players(current_player, unassigned_losers[1])
                elif len(unassigned_losers[1]) == 1 and unassigned_losers[2]:
                    current_player = random.choice(unassigned_losers[1])
                    unassigned_losers[1].remove(current_player)
                    matched_player, valid = self.match_players(current_player, unassigned_losers[2])
                elif len(unassigned_losers[2]) > 1:
                    current_player = random.choice(unassigned_losers[2])
                    unassigned_losers[2].remove(current_player)
                    matched_player, valid = self.match_players(current_player, unassigned_losers[2])

                if len(unassigned_losers[1]) == 1 and not unassigned_losers[2]:
                    self.bye = unassigned_losers[1].pop()
                elif len(unassigned_losers[2]) == 1 and not unassigned_losers[1]:
                    self.bye = unassigned_losers[2].pop()

                self.create_match_pair(match_num, current_player, matched_player)

        return self.matches[match_num]

    async def delete_active_matches(self, ctx):
        if len(self.active) > 0:
            for pair in self.active:
                message = await ctx.fetch_message(pair.message.id)
                await message.delete()
            self.active = []

import json
import random

from bot.log import Log
from bot.util import get_longest_name_length
from bot.match import Match
from datetime import datetime


class Session:
    def __init__(self, players, database, recorded):
        self.players = players
        self.db = database
        self.recorded = recorded
        self.removed_players = []
        self.game_winners = None
        self.match_set = {1: Match(), 2: Match(), 3: Match()}
        self.active_match_num = 0
        self.active = []
        self.log = Log(players)
        self.longest = get_longest_name_length(self.players)
        self.datetime = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Get list of players who have not dropped from the game
    def get_active_players(self):
        return [player for player in self.players if player not in self.removed_players]

    # Get prior opponents of specified player from matches that have already been created
    def get_prior_opponents(self, player):
        prior_opponents = []
        for match_num, match in self.match_set.items():
            if match_num >= self.active_match_num:
                continue
            opponent = match.get_opponent(player)
            if opponent is not None:
                prior_opponents.append(opponent)
        return prior_opponents

    # Get the current match
    def get_current_match(self):
        return self.match_set[self.active_match_num]

    # Number of byes a player has received in matches created before the active one
    def get_prior_byes(self, player):
        return sum(
            1 for match_num, match in self.match_set.items()
            if match_num < self.active_match_num and match.bye is player)

    # Pair players with similar records, avoiding rematches where possible.
    # Returns (list of (p1, p2) pairs, bye player or None).
    def build_pairings(self, players):
        losses = {p: min(self.get_player_record(p)['losses'], 2) for p in players}
        opponents = {p: set(self.get_prior_opponents(p)) for p in players}
        node_budget = 20000

        def solve(remaining, allow_rematch):
            nonlocal node_budget
            node_budget -= 1
            if node_budget < 0:
                return None
            if not remaining:
                return []
            first, rest = remaining[0], remaining[1:]
            candidates = [p for p in rest if allow_rematch or p not in opponents[first]]
            # Closest record first, then random order
            random.shuffle(candidates)
            candidates.sort(key=lambda p: abs(losses[p] - losses[first]))
            for candidate in candidates:
                result = solve([p for p in rest if p is not candidate], allow_rematch)
                if result is not None:
                    return [(first, candidate)] + result
            return None

        shuffled = random.sample(players, len(players))
        ordered = sorted(shuffled, key=lambda p: losses[p])

        # Odd player counts: someone sits out, preferring players who have not had a bye
        bye_options = [None]
        if len(ordered) % 2:
            bye_options = sorted(shuffled, key=lambda p: (self.get_prior_byes(p), losses[p]))

        for allow_rematch in (False, True):
            node_budget = 20000
            for bye in bye_options:
                pairs = solve([p for p in ordered if p is not bye], allow_rematch)
                if pairs is not None:
                    return pairs, bye
        # Unreachable for 2+ players since rematches allowed in the final pass, barring budget exhaustion
        raise RuntimeError("Unable to generate pairings")

    # Get all currently undefeated players
    def get_undefeated_players(self):
        return [player for player in self.get_active_players() if self.get_player_record(player)['losses'] == 0]

    # Get the record of a player in the current session
    def get_player_record(self, player):
        return {
            'wins': sum(player in match.get_match_results()['winners'] for match in self.match_set.values()),
            'losses': sum(player in match.get_match_results()['losers'] for match in self.match_set.values())
        }

    # Increment the match number by 1
    def increment_match_num(self):
        self.active_match_num += 1

    # Drop a player from the game based on a given list of player tags
    def drop_players(self, player_tags):
        active_match = self.match_set[self.active_match_num]
        # For player tag in list of players to drop
        for player_tag in player_tags:
            # For player in list of currently active players
            for active_player in self.get_active_players():
                # If the tags are the same, drop the player by adding them to the list of removed players
                if active_player.tag == player_tag:
                    self.removed_players.append(active_player)
            # If that player was on the bye, set the bye to none
            if active_match.bye is not None and active_match.bye.tag == player_tag:
                active_match.bye = None

    # Commit all player ELO scores to the database
    def commit_elo_scores(self):
        if not self.recorded:
            return
        for player in self.players:
            self.db.set_elo(player.id, player.new_elo)

    # Commit a final log to the database
    def commit_log(self):
        if not self.recorded:
            return
        # Update the player ranks
        for player in self.players:
            player.new_rank = self.db.get_rank(player.id)
        self.db.set_log(self.log.get_log())

    # Create a new match and assign players to pairings
    def new_match(self):
        # Increment the match counter
        self.increment_match_num()
        # Get the active match
        active_match = self.match_set[self.active_match_num]
        active_match.pairings = []
        pairs, bye = self.build_pairings(self.get_active_players())
        for p1, p2 in pairs:
            active_match.new_pairing(p1, p2)
        active_match.bye = bye
        active_match.bye_buffer = bye
        # Return the active match
        return active_match

    def manual_match(self, data):
        def get_player_by_id(player_id):
            for p in self.players:
                if str(p.id) == player_id:
                    return p

        self.active_match_num = 1

        for match_num, match in data['matches'].items():
            self.match_set[self.active_match_num] = Match()
            active_match = self.match_set[self.active_match_num]
            for pairing_key, pairing in match['pairings'].items():
                p1 = get_player_by_id(pairing['p1'])
                p2 = get_player_by_id(pairing['p2'])
                active_match.new_pairing(p1, p2)
                active_match.pairings[-1].wins = {p1: pairing['p1_wins'], p2: pairing['p2_wins']}
                active_match.pairings[-1].adjust_elo()
            # self.log.add_match(active_match, self.active_match_num)
            self.commit_elo_scores()
            self.increment_match_num()

        for player in self.players:
            if player.id is not None:
                self.db.increment_games_played(player.id)

        self.commit_log()
        return True

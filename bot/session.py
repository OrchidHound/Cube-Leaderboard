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

    # Get prior opponents of specified player for matchmaking purposes
    def get_prior_opponents(self, player):
        prior_opponents = []
        for match in self.match_set.values():
            prior_opponents.append(match.get_opponent(player))
        return prior_opponents

    # Get the current match
    def get_current_match(self):
        return self.match_set[self.active_match_num]

    # Match a given player to a valid unmatched player
    # player_list is either players with 0 or 1 losses, depending on match state
    # player_list_2 is the list of players with 2 losses and is only relevant when two players with 1 loss in
    # round 3 have already played against each other
    def match_player(self, given_player, player_list, player_list_2=None):
        prior_opponents = self.get_prior_opponents(given_player)
        # If this is the first match
        if len(self.match_set) == 0:
            # Avoid matching given player to anyone in the seats directly beside them
            matched_player = random.choice([player for player in player_list if abs(player.seat - given_player.seat) != 1])
        else:
            # Match player if they have not faced them in a prior match
            if len([player for player in player_list if player not in prior_opponents]) == 0:
                matched_player = random.choice([player for player in player_list_2 if player not in prior_opponents])
            else:
                matched_player = random.choice([player for player in player_list if player not in prior_opponents])

        return matched_player

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
        # While the matchmaking for the round is invalid or incomplete
        while True:
            try:
                # Initialize the unassigned players with keys 0, 1, and 2, each having an empty list as a value
                unassigned_players = {0: [], 1: [], 2: []}
                # Populate the lists with players based on their number of losses
                for player in self.get_active_players():
                    losses = self.get_player_record(player)['losses']
                    unassigned_players[losses].append(player)
                # While there are unassigned winners
                while unassigned_players[0]:
                    matched_player = None
                    # If there is a bye and they have no losses
                    if active_match.bye is not None and active_match.bye in unassigned_players[0]:
                        # Player on the bye gets priority in being matched
                        given_player = active_match.bye
                        active_match.bye = None
                    else:
                        # Get a random player from the unassigned list
                        given_player = random.choice(unassigned_players[0])
                    # Remove the given player from the unassigned list
                    unassigned_players[0].remove(given_player)
                    # If there are other players without losses
                    if len(unassigned_players[0]) > 0:
                        matched_player = self.match_player(given_player, unassigned_players[0])
                        unassigned_players[0].remove(matched_player)
                    # If there are no other players without losses but there are players with a single loss
                    elif len(unassigned_players[0]) == 0 and unassigned_players[1]:
                        matched_player = self.match_player(given_player, unassigned_players[1])
                        unassigned_players[1].remove(matched_player)
                    # If there are no players leftover in the unassigned winners and there aren't any players with
                    # losses, put the given player on the bye
                    elif len(unassigned_players[0]) == 0 and not unassigned_players[1]:
                        active_match.bye = given_player
                    # Create a new pairing in the match
                    if matched_player:
                        active_match.new_pairing(given_player, matched_player)
                # While there are unassigned players with 1 or 2 losses
                while unassigned_players[1] or unassigned_players[2]:
                    given_player = None
                    matched_player = None
                    # If there's a bye, prioritize their assignment
                    if active_match.bye is not None:
                        given_player = active_match.bye
                        if given_player in unassigned_players[1]:
                            unassigned_players[1].remove(given_player)
                        else:
                            unassigned_players[2].remove(given_player)
                        active_match.bye = None
                        # Match the player on the bye with a random remaining player
                        if len(unassigned_players[1]) >= 1:
                            matched_player = self.match_player(given_player, unassigned_players[1], unassigned_players[2])
                            unassigned_players[1].remove(matched_player)
                        elif len(unassigned_players[2]) >= 1:
                            matched_player = self.match_player(given_player, unassigned_players[2])
                            unassigned_players[2].remove(matched_player)
                    # If there is one unassigned player with no losses:
                    elif len(unassigned_players[0]) == 1 and unassigned_players[1]:
                        given_player = unassigned_players[0].pop()
                        matched_player = self.match_player(given_player, unassigned_players[1], unassigned_players[2])
                        unassigned_players[1].remove(matched_player)
                    # If there are more than one unassigned players with one loss
                    elif len(unassigned_players[1]) > 1:
                        given_player = random.choice(unassigned_players[1])
                        unassigned_players[1].remove(given_player)
                        matched_player = self.match_player(given_player, unassigned_players[1], unassigned_players[2])
                        unassigned_players[1].remove(matched_player)
                    # If there is only one player with a single loss but players with two losses available
                    elif len(unassigned_players[1]) == 1 and unassigned_players[2]:
                        given_player = random.choice(unassigned_players[1])
                        unassigned_players[1].remove(given_player)
                        matched_player = self.match_player(given_player, unassigned_players[2], unassigned_players[2])
                        unassigned_players[2].remove(matched_player)
                    # If there are two or more players with two losses
                    elif len(unassigned_players[2]) > 1:
                        given_player = random.choice(unassigned_players[2])
                        unassigned_players[2].remove(given_player)
                        matched_player = self.match_player(given_player, unassigned_players[2], unassigned_players[2])
                        unassigned_players[2].remove(matched_player)
                    # Assign the bye if there is a player leftover
                    if len(unassigned_players[1]) == 1 and not unassigned_players[2]:
                        active_match.bye = unassigned_players[1].pop()
                    elif (len(unassigned_players[2])) == 1 and not unassigned_players[1]:
                        active_match.bye = unassigned_players[2].pop()
                    # Create a new pairing in the match
                    active_match.new_pairing(given_player, matched_player)
                # If there are no unassigned players, assign the buffer and break the loop
                if not unassigned_players[0] and not unassigned_players[1] and not unassigned_players[2]:
                    active_match.bye_buffer = active_match.bye
                    break
                else:
                    active_match.bye = active_match.bye_buffer
            except IndexError:
                active_match.bye = active_match.bye_buffer
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
            self.log.add_match(active_match, self.active_match_num)
            self.commit_elo_scores()
            self.increment_match_num()

        for player in self.players:
            if player.id is not None:
                self.db.increment_games_played(player.id)

        self.commit_log()
        return True

import json

class Log:
    def __init__(self, players):
        self.players = players
        self.match_logs = {}

    def add_match(self, match, match_num):
        self.match_logs[match_num] = {
            'bye': match.bye.id if match.bye else 'None',
            'pairings': {}
        }
        for pair_num in range(len(match.pairings)):
            self.match_logs[match_num]['pairings'][str(pair_num)] = {
                'p1': match.pairings[pair_num].p1.id,
                'p2': match.pairings[pair_num].p2.id,
                'p1_wins': match.pairings[pair_num].wins[match.pairings[pair_num].p1],
                'p2_wins': match.pairings[pair_num].wins[match.pairings[pair_num].p2],
                'p1_new_elo': match.pairings[pair_num].p1.new_elo,
                'p2_new_elo': match.pairings[pair_num].p2.new_elo
            }

    def get_log(self):
        log = {
            'players': {},
            'matches': self.match_logs,
            'partial_log': True if len(self.match_logs) < 3 else False
        }
        for player in self.players:
            log['players'][player.id] = {
                'seat': player.seat,
                'original_elo': player.original_elo,
                'final_elo': player.new_elo,
                'original_rank': player.original_rank,
                'final_rank': player.new_rank
            }
        return json.dumps(log)

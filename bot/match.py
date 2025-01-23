class Match:
    def __init__(self):
        self.pairings = []
        self.bye = None
        self.bye_buffer = None

    # Get the opponent of the specified player if they exist
    def get_opponent(self, player):
        return next(
            (pair.p2 if player == pair.p1 else pair.p1 for pair in self.pairings if player in (pair.p1, pair.p2)), None)

    # Get the match results and return as a dictionary of winning and losing players
    def get_match_results(self):
        winners = [pair.get_match_winner() for pair in self.pairings if pair.get_match_winner() is not None]
        return {
            'winners': winners,
            'losers': [self.get_opponent(winner) for winner in winners]
        }

    def new_pairing(self, p1, p2):
        self.pairings.append(Pairing(p1, p2))


class Pairing:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.wins = {self.p1: 0, self.p2: 0}
        # For use with the session views
        self.view = None

    # Find the overall winner of the individual match between the two players
    def get_match_winner(self):
        p1_score = self.wins.get(self.p1, 0) + 1
        p2_score = self.wins.get(self.p2, 0) + 1
        return self.p1 if p1_score > p2_score else self.p2 if p1_score < p2_score else None

    # Adjust the ELO score of the players based on the match results
    def adjust_elo(self):
        def calc_expected_score(rating_a, rating_b):
            return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

        def calc_new_score(rating, expected_score, actual_score, k=32):
            return round(rating + k * (actual_score - expected_score))

        # Update the ELO of both players
        if self.p1 and self.p2:
            p1_expected_score = calc_expected_score(self.p1.new_elo, self.p2.new_elo)
            p2_expected_score = calc_expected_score(self.p2.new_elo, self.p1.new_elo)

            try:
                self.p1.new_elo = calc_new_score(
                    self.p1.new_elo,
                    p1_expected_score,
                    self.wins[self.p1])
                self.p2.new_elo = calc_new_score(
                    self.p2.new_elo,
                    p2_expected_score,
                    self.wins[self.p2])
            except TypeError as e:
                print("Type error when updating elo score: " + str(e))

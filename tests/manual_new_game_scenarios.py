"""Manually initiated scenario test for new game sessions.

Not auto-discovered (filename lacks the test_ prefix). Run from the repo root:

    python -m unittest tests.manual_new_game_scenarios -v

Optional environment variables:
    SCENARIO_ITERATIONS  repetitions per scenario (default 25)
    SCENARIO_SEED        fixed RNG seed for reproducibility
"""
import os
import random
import sys
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.player import Player
from bot.session import Session

ITERATIONS = int(os.environ.get("SCENARIO_ITERATIONS", 25))
MATCH_TIMEOUT = 5  # seconds; matchmaking loops until valid, so guard against hangs

# (player count, {match number: number of players dropping before that match})
SCENARIOS = [
    (4, {}),
    (5, {}),
    (6, {}),
    (7, {}),
    (8, {}),
    (9, {}),
    (12, {}),
    (16, {}),
    (6, {2: 1}),
    (8, {2: 1}),
    (8, {3: 1}),
    (8, {2: 1, 3: 1}),
    (9, {2: 1}),
    (10, {2: 2}),
    (12, {2: 2, 3: 1}),
    (12, {3: 2}),
    (16, {2: 3, 3: 2}),
]


class FakeDatabase:
    def set_elo(self, player_id, elo):
        pass

    def get_rank(self, player_id):
        return None

    def set_log(self, log):
        pass

    def increment_games_played(self, player_id):
        pass


def make_players(count):
    players = [Player(i + 1, f"<@{i + 1}>", f"Player{i + 1}", 1200, None) for i in range(count)]
    for seat, player in enumerate(players):
        player.seat = seat
    return players


def run_with_timeout(func, timeout):
    result = {}

    def target():
        try:
            result["value"] = func()
        except Exception as e:
            result["error"] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError("matchmaking did not finish")
    if "error" in result:
        raise result["error"]
    return result["value"]


def record_random_results(match, rng):
    for pairing in match.pairings:
        winner = rng.choice([pairing.p1, pairing.p2])
        loser = pairing.p2 if winner is pairing.p1 else pairing.p1
        pairing.wins = {winner: 2, loser: rng.choice([0, 1])}
        pairing.adjust_elo()


class NewGameScenarioTest(unittest.TestCase):
    def check_match(self, session, match, label):
        active = session.get_active_players()
        paired = []
        for pairing in match.pairings:
            self.assertIsNotNone(pairing.p1, label)
            self.assertIsNotNone(pairing.p2, label)
            self.assertIsNot(pairing.p1, pairing.p2, f"{label}: self pairing")
            paired += [pairing.p1, pairing.p2]

        self.assertEqual(len(paired), len(set(paired)), f"{label}: player paired twice")
        for player in paired:
            self.assertIn(player, active, f"{label}: dropped player {player.tag} was paired")

        unassigned = [p for p in active if p not in paired]
        # Odd active counts leave exactly one player on the bye; even counts leave none
        self.assertEqual(len(unassigned), len(active) % 2, f"{label}: wrong number unpaired")
        if unassigned:
            self.assertIs(match.bye, unassigned[0], f"{label}: bye mismatch")
        else:
            self.assertIsNone(match.bye, f"{label}: unexpected bye")

        # No rematches against earlier matches
        for earlier_num, earlier in session.match_set.items():
            if earlier is match:
                continue
            for pairing in match.pairings:
                self.assertIsNot(earlier.get_opponent(pairing.p1), pairing.p2,
                                 f"{label}: rematch in match {earlier_num}")

    def test_scenarios(self):
        seed = int(os.environ.get("SCENARIO_SEED", random.randrange(1_000_000)))
        print(f"\nSCENARIO_SEED={seed}")
        for count, drops in SCENARIOS:
            for iteration in range(ITERATIONS):
                label = f"players={count} drops={drops} iter={iteration} seed={seed}"
                with self.subTest(label):
                    rng = random.Random(f"{seed}-{count}-{drops}-{iteration}")
                    random.seed(rng.random())
                    session = Session(make_players(count), FakeDatabase(), False)

                    for match_num in (1, 2, 3):
                        active = session.get_active_players()
                        # Keep enough players for a valid match
                        to_drop = min(drops.get(match_num, 0), max(len(active) - 4, 0))
                        if to_drop:
                            session.drop_players([p.tag for p in rng.sample(active, to_drop)])

                        match = run_with_timeout(session.new_match, MATCH_TIMEOUT)
                        self.check_match(session, match, label)
                        record_random_results(match, rng)


if __name__ == "__main__":
    unittest.main()

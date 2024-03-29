import sqlite3
from sqlite3 import Error
import pathlib


# Returns a connection to the database with the connection cursor.
def connect(db_file):
    conn = None

    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print("Error: " + str(e))

    return conn, conn.cursor()


class sql:
    def __init__(self, server_id: int):
        self.conn, self.c = connect(db_file=pathlib.Path(__file__).parent.parent / 'cube_leaderboard.db')
        self.server_id = server_id

    def create_tables(self):
        try:
            self.c.execute(
                """
                CREATE TABLE IF NOT EXISTS Users (
                    user_id TEXT PRIMARY KEY,
                    games_played INTEGER
                );
                """
            )

            self.c.execute(
                """
                CREATE TABLE elo_scores (
                    elo_id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    server_id INTEGER,
                    elo_score INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, server_id)
                );
                """
            )

            self.conn.commit()
            return True
        except Error as e:
            print('Error initializing databases: ' + str(e))
            return False

    def get_leaderboard(self):
        try:
            leaderboard = {}
            self.c.execute(
                f"""
                SELECT e.elo_id, e.user_id, e.elo_score 
                FROM elo_scores AS e
                JOIN Users AS u ON e.user_id = u.user_id
                WHERE e.server_id = ? 
                AND u.games_played >= 3
                ORDER BY e.elo_score DESC
                """,
                (self.server_id,)
            )
            data = self.c.fetchall()
            for rank, row in enumerate(data):
                leaderboard[rank + 1] = {'user': row[1], 'elo': row[2]}
            return leaderboard
        except Error as e:
            print('Error: ' + str(e))

    def get_rank(self, user):
        leaderboard = self.get_leaderboard()
        for rank, row in leaderboard.items():
            if row['user'] == str(user):
                return rank

    def get_elo(self, user):
        try:
            self.c.execute(
                f"""
                SELECT elo_score FROM elo_scores
                WHERE user_id = ? AND server_id = ?
                """,
                (str(user), self.server_id)
            )
            record = self.c.fetchone()
            if record:
                return record[0]
            else:
                return 1200
        except Error as e:
            print('Error: ' + str(e))

    def set_elo(self, user, elo):
        try:
            self.c.execute(
                f"""
                UPDATE elo_scores
                SET elo_score = ?
                WHERE user_id = ? AND server_id = ?
                """,
                (elo, str(user), self.server_id)
            )
            self.conn.commit()
        except Error as e:
            print('Error: ' + str(e))

    def set_user(self, user):
        try:
            self.c.execute(
                f"""
                INSERT OR IGNORE INTO Users (user_id, games_played)
                VALUES (?, 0)
                """,
                (str(user),)
            )
            self.c.execute(
                f"""
                INSERT OR IGNORE INTO elo_scores (user_id, server_id, elo_score)
                VALUES (?, ?, ?)
                """,
                (str(user), self.server_id, 1200)
            )
            self.conn.commit()
        except Error as e:
            print('Error: ' + str(e))

    def adjust_score(self, p1, p2, match):
        def calc_expected_score(rating_a, rating_b):
            return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

        def calc_new_score(rating, expected_score, actual_score, k=32):
            return round(rating + k * (actual_score - expected_score))

        # Update the ELO of the winner and loser.
        if p1 and p2:
            for round_winner in [match['r1_winner'], match['r2_winner'], match['r3_winner']]:
                p1_rating = self.get_elo(p1)
                p2_rating = self.get_elo(p2)
                p1_expected_score = calc_expected_score(p1_rating, p2_rating)
                p2_expected_score = calc_expected_score(p2_rating, p1_rating)

                try:
                    if round_winner == match['p1']:
                        p1_new_score = calc_new_score(p1_rating, p1_expected_score, 1)
                        p2_new_score = calc_new_score(p2_rating, p2_expected_score, 0)
                        self.set_elo(p1, p1_new_score)
                        self.set_elo(p2, p2_new_score)
                    elif round_winner == match['p2']:
                        p1_new_score = calc_new_score(p1_rating, p1_expected_score, 0)
                        p2_new_score = calc_new_score(p2_rating, p2_expected_score, 1)
                        self.set_elo(p1, p1_new_score)
                        self.set_elo(p2, p2_new_score)
                except TypeError:
                    pass

    def increment_games_played(self, user):
        try:
            self.c.execute(
                f"""
                UPDATE Users
                SET games_played = games_played + 1
                WHERE user_id = ?
                """,
                (str(user),)
            )
            self.conn.commit()
        except Error as e:
            print('Error: ' + str(e))


if __name__ == '__main__':
    database = sql(server_id=0)
    database.create_tables()

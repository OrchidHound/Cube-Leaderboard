import sqlite3
from sqlite3 import Error
import pathlib


# Returns a connection to the database with the connection cursor.
def connect(db_file):
    conn = None

    try:
        conn = sqlite3.connect(db_file)
        print("SQLite3 Version " + sqlite3.version)
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
                    user_id TEXT PRIMARY KEY
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
            self.c.execute(
                f"""
                SELECT elo_id, user_id, elo_score FROM elo_scores
                WHERE server_id = ?
                ORDER BY elo_score DESC
                """,
                (self.server_id,)
            )
            return self.c.fetchall()
        except Error as e:
            print('Error: ' + str(e))

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
                INSERT OR IGNORE INTO Users (user_id)
                VALUES (?)
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

    def adjust_score(self, winner, loser, score_diff: int):
        def calc_expected_score(rating_a, rating_b):
            return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

        def calc_new_score(rating, expected_score, actual_score, k=32):
            return round(rating + k * (actual_score - expected_score))

        winner_rating = self.get_elo(winner)
        loser_rating = self.get_elo(loser)

        # Update the ELO of the winner and loser.
        if winner and loser:
            winner_expected_score = calc_expected_score(winner_rating, loser_rating)
            loser_expected_score = calc_expected_score(loser_rating, winner_rating)
            winner_new_score = calc_new_score(winner_rating, winner_expected_score, score_diff)
            loser_new_score = calc_new_score(loser_rating, loser_expected_score, 0-score_diff)
            self.set_elo(winner, winner_new_score)
            self.set_elo(loser, loser_new_score)


if __name__ == '__main__':
    database = sql(server_id=0)
    database.create_tables()

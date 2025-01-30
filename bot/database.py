import sqlite3
from sqlite3 import Error
import pathlib


# Returns a connection to the database with the connection cursor
def connect(db_file):
    conn = None

    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print("Error: " + str(e))

    return conn, conn.cursor()


class Database:
    def __init__(self):
        self.conn, self.c = connect(db_file=pathlib.Path(__file__).parent.parent / 'cube_leaderboard.db')

    def create_tables(self):
        try:
            self.c.execute(
                """
                CREATE TABLE IF NOT EXISTS players (
                    player_id INTEGER PRIMARY KEY,
                    player_tag TEXT,
                    player_nick TEXT,
                    games_played INTEGER,
                    elo_score INTEGER
                );
                """
            )

            self.c.execute(
                """
                CREATE TABLE session_logs (
                    date TEXT PRIMARY KEY,
                    log_data TEXT
                );
                """
            )

            self.c.execute(
                """
                INSERT INTO players (player_id, player_tag, player_nick, games_played, elo_score)
                VALUES (0, 'Dummy_Tag', 'Dummy_Nick', 0, 1200)
                """
            )

            self.conn.commit()
            return True
        except Error as e:
            print('Create tables error: ' + str(e))
            return False

    def get_leaderboard(self):
        try:
            leaderboard = {}
            self.c.execute(
                """
                SELECT player_id, elo_score, player_nick
                FROM players
                WHERE games_played >= 3
                ORDER BY elo_score DESC
                """
            )
            data = self.c.fetchall()
            for rank, row in enumerate(data):
                leaderboard[rank + 1] = {'player_id': row[0], 'elo': row[1], 'player_nick': row[2]}
            return leaderboard
        except Error as e:
            print('Get leaderboard error: ' + str(e))

    def get_rank(self, player_id):
        leaderboard = self.get_leaderboard()
        for rank, row in leaderboard.items():
            if row['player_id'] == player_id:
                return rank

    def get_elo(self, player_id):
        try:
            self.c.execute(
                f"""
                SELECT elo_score FROM players
                WHERE player_id = ?
                """,
                (player_id,)
            )
            record = self.c.fetchone()
            if record:
                return record[0]
            else:
                return 1200
        except Error as e:
            print('Get elo error: ' + str(e))

    def get_all_players(self):
        try:
            self.c.execute(
                f"""
                SELECT player_id, player_tag, player_nick, games_played, elo_score FROM players
                """,
            )
            return self.c.fetchall()
        except Error as e:
            print('Get all players error: ' + str(e))

    def set_elo(self, player_id, elo):
        try:
            self.c.execute(
                f"""
                UPDATE players
                SET elo_score = ?
                WHERE player_id = ?
                """,
                (elo, player_id,)
            )
            self.conn.commit()
        except Error as e:
            print('Set elo error: ' + str(e))

    def set_player(self, player_id, player_tag, player_nick):
        try:
            self.c.execute(
                f"""
                INSERT INTO players (player_id, player_tag, player_nick, games_played, elo_score)
                VALUES (?, ?, ?, 0, 1200)
                ON CONFLICT(player_id) DO UPDATE SET
                    player_tag = ?,
                    player_nick = ?
                """,
                (player_id, player_tag, player_nick, player_nick, player_tag,)
            )
            self.conn.commit()
        except Error as e:
            print('Set player error: ' + str(e))

    def set_log(self, log):
        try:
            self.c.execute(
                f"""
                INSERT OR IGNORE INTO session_logs (date, log_data)
                VALUES (DATETIME('now'), ?)
                """,
                (log,)
            )
            self.conn.commit()
        except Error as e:
            print('Log error: ' + str(e))

    def increment_games_played(self, player_id):
        try:
            self.c.execute(
                f"""
                UPDATE players
                SET games_played = games_played + 1
                WHERE player_id = ?
                """,
                (player_id,)
            )
            self.conn.commit()
        except Error as e:
            print('Increment error: ' + str(e))


if __name__ == '__main__':
    database = Database()
    database.create_tables()

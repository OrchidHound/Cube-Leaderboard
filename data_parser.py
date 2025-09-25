from bot.database import Database
from datetime import datetime
import json
import csv


def get_wins(log_json, pid):
    wins = 0
    for match in log_json['matches'].values():
        for pairing in match['pairings'].values():
            if pairing['p1'] == pid and pairing['p1_wins'] > pairing['p2_wins']:
                wins += 1
            elif pairing['p2'] == pid and pairing['p2_wins'] > pairing['p1_wins']:
                wins += 1
    return wins


if __name__ == '__main__':
    db = Database()

    sql_data = db.c.execute("""
        SELECT * FROM session_logs
    """).fetchall()

    writer = csv.writer(open("session_logs.csv", "a", newline=""))

    for row in sql_data:
        log = json.loads(row[1])
        date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").strftime("%m/%d/%Y")
        for player_id, player_data in log['players'].items():
            player_nick = db.get_player_nick(int(player_id))
            player_wins = get_wins(log, int(player_id))
            writer.writerow([
                date,
                player_nick,
                player_data['final_elo'],
                player_wins,
                3 - player_wins
            ])

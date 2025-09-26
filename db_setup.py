import bot.database as database

if __name__ == '__main__':
    db = database.Database()
    db.create_tables()

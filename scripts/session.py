def clean_user(user):
    try:
        return int(user.replace('<', '').replace('>', '').replace('@', ''))
    except (TypeError, ValueError):
        return None


def assign_id(session_list):
    existing_ids = [session.get_id() for session in session_list]
    if len(session_list) > 0:
        if min(existing_ids) == 10:
            return None

        for i in range(1, 10):
            if i not in existing_ids:
                return i
    return 1


def get_session(session_list, session_id):
    for session in session_list:
        if session.get_id() == session_id:
            return session
    return None


def get_session_users(session):
    output = ""
    for user in session.get_users():
        if len(output) > 0:
            output = f"{output}, {user.name}"
        else:
            output = f"{user.name}"
    return output


class Session:
    class User:
        def __init__(self, name, user_type):
            self.name = name
            self.user_type = user_type
            self.data = {}
            self.seat = 0

        def update_date(self, opponent, score):
            self.data = {opponent: score}

    def __init__(self, server, users, session_id):
        self.server = server
        self.users = users
        self.users = [self.User(user, 'permanent') if self.server.get_member(clean_user(user)) else
                      self.User(user, 'temporary') for user in self.users]
        self.session_id = session_id

    def get_users(self):
        return [user for user in self.users]

    def get_id(self):
        return self.session_id

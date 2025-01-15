# Get length of the longest name from a given list of Player objects for formatting purposes in Discord
def get_longest_name_length(players):
    longest_name_length = 0
    for player in players:
        if len(player.get_trimmed_nick()) > longest_name_length:
            longest_name_length = len(player.get_trimmed_nick())
    return longest_name_length

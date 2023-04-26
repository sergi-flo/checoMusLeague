from pathlib import Path
from typing import List

def parse_games_log(path, display) -> List or str:
    if Path(path).is_file():
        with open('games_history.log', 'r', encoding="utf-8") as file:
            games = file.readlines()
    else:
        return []
    games_history_parsed = []
    for game in games:
        try:
            time_info, winners_info, losers_info = game.split("---")
        except ValueError:
            return "Ha ocurrido algun error"
        if display:
            winner1, winner2 = ["<br />".join(x.split("*")) for x in winners_info.split("--")]
            loser1, loser2 = ["<br />".join(x.split("*")) for x in losers_info.split("--")]
        else:
            winner1, winner2 = [x for x in winners_info.split("--")]
            loser1, loser2 = [x for x in losers_info.split("--")]
        games_history_parsed.append([time_info, winner1, winner2, loser1, loser2])
    return games_history_parsed

def change_logs(path):
    if Path(path).is_file():
        with open('games_history.log', 'r', encoding="utf-8") as file:
            games = file.readlines()
    else:
        return None
    new_logs = []
    for game in games:
        new_logs.append(game[0:19]+game[19:].replace(" - La pareja ", "---")\
                        .replace("ha ganado a la pareja", "---")\
                        .replace("]-", "]--").replace(")[", ")*["))
    with open(path, 'w', encoding="utf-8") as file:
        for game in new_logs:
            file.write(game)


if __name__ == "__main__":
    change_logs("games_history.log")

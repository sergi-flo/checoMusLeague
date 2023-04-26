# Import necessary modules
import datetime
import re
import os
from pathlib import Path
from flask import Flask, request, redirect, session, url_for
import pandas as pd

# Import utils
from utils import parse_games_log

# Import CSS styles
from style import styles

# Basic logger for all the requests
if not int(os.environ.get("DEBUG")):
    import logging
    logging.basicConfig(filename='python_index.log',
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
    logger=logging.getLogger(__name__)

# Define the Flask app and secret key for the session
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

# Define the players playing the competiton
players = [
    "flo",
    "ortin",
    "varo",
    "tom",
    "tallon",
    "inma",
    "cesar",
    "anton",
]


# Create a dictionary of players and their scores if dict does not exist
SCORES_PATH = Path('scores.csv')
if SCORES_PATH.is_file():
    pass
else:
    players = {k:[1000,0,0,0] for k in players}
    # Convert the dictionary into a Pandas DataFrame and sort by score
    start_df = pd.DataFrame.from_dict(players, orient='index',
                                columns=['score', 'wins', 'losses', 'total'])
    start_df = start_df.sort_values(by='score', ascending=False)
    start_df.to_csv(SCORES_PATH)

# K is a scaling factor that determines how much ELO points can be gained or lost in a single game
K = 33

# Define the TOKEN where app is going to be deployed, so it is not easy to exploid and to find
TOKEN = "a"
if not int(os.environ.get("DEBUG")):
    TOKEN = os.environ.get("TOKEN")

# Layout for the navigation bar
NAVIGATION_BAR = f"""<nav class="stroke">
    <ul>
      <li><a href="/{TOKEN}">Clasificación</a></li>
      <li><a href="/{TOKEN}/game_history">Historial de partidas</a></li>
    </ul>
  </nav>"""

def generate_scoreboard_html(df):
    # Generate HTML for the scoreboard
    html = '<html><head><title>Classificación</title><style>'
    html += styles
    html += '</style></head><body>'
    html += '<h1>Checo  Mus  League</h1>'
    html += NAVIGATION_BAR
    html += '<h2>Classificación Liga de Verano</h2>'
    html += '<table>'
    html += '<tr><td>Posición</td><td>Jugadores</td><td>ELO</td>'
    html += '<td>Ganadas</td><td>Perdidas</td><td>Total</td></tr>'
    position = 1
    for i, row in df.iterrows():
        html += f'<tr><td>{position}</td><td type="names">{i.capitalize()}</td>'
        html += f'<td>{row["score"]:.2f}</td><td>{int(row["wins"])}</td>'
        html += f'<td>{int(row["losses"])}</td><td>{int(row["total"])}</td></tr>'
        position += 1
    html += '</table>'

    return html

def update_results(request_info, df):
    # Get player names
    winner1 = request_info.form['winner1'].strip().lower()
    winner2 = request_info.form['winner2'].strip().lower()
    loser1 = request_info.form['loser1'].strip().lower()
    loser2 = request_info.form['loser2'].strip().lower()

    # Check if the players exist
    if (winner1 not in df.index) or (winner2 not in df.index)\
         or (loser1 not in df.index) or (loser2 not in df.index):
        return "Error: Uno o mas jugadores no existen."

    # Check if all players are diferent
    if len(set([winner1, winner2, loser1, loser2])) != 4:
        return "Error: Hay algun jugador repetido."

    # Actual ELO from the players
    elo_winner1 = df.loc[winner1, 'score']
    elo_winner2 = df.loc[winner2, 'score']
    elo_loser1 = df.loc[loser1, 'score']
    elo_loser2 = df.loc[loser2, 'score']

    # Calculate the new score for each player
    expected_win_winner1 = 1/(10**((((elo_loser2+elo_loser1)/2)-(elo_winner1))/400)+1)
    expected_win_winner2 = 1/(10**((((elo_loser2+elo_loser1)/2)-(elo_winner2))/400)+1)
    expected_win_loser1 = 1/(10**(-((elo_loser1)-((elo_winner1+elo_winner2))/2)/400)+1)
    expected_win_loser2 = 1/(10**(-((elo_loser2)-((elo_winner1+elo_winner2))/2)/400)+1)

    new_elo_winner1 = round(elo_winner1 + K * (1 - expected_win_winner1), 2)
    new_elo_winner2 = round(elo_winner2 + K * (1 - expected_win_winner2), 2)
    new_elo_loser1 = round(elo_loser1 + K * (0 - expected_win_loser1), 2)
    new_elo_loser2 = round(elo_loser2 + K * (0 - expected_win_loser2), 2)

    # Update score from players
    df.loc[winner1, 'score'] = new_elo_winner1
    df.loc[winner2, 'score'] = new_elo_winner2
    df.loc[loser1, 'score'] = new_elo_loser1
    df.loc[loser2, 'score'] = new_elo_loser2

    # Update wins and losses from players
    df.loc[winner1, 'wins'] += 1
    df.loc[winner2, 'wins'] += 1
    df.loc[loser1, 'losses'] += 1
    df.loc[loser2, 'losses'] += 1

    # Update total games played
    df.loc[winner1, 'total'] += 1
    df.loc[winner2, 'total'] += 1
    df.loc[loser1, 'total'] += 1
    df.loc[loser2, 'total'] += 1

    # save game and result in the history_games logger
    with open("games_history.log", "a") as games_log:
        games_log.write((f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} --- "
f"{winner1.capitalize()} ({expected_win_winner1*100:.02f}%)*[{elo_winner1} > {new_elo_winner1}]--"
f"{winner2.capitalize()} ({expected_win_winner2*100:.02f}%)*[{elo_winner2} > {new_elo_winner2}] ---"
f"{loser1.capitalize()} ({expected_win_loser1*100:.02f}%)*[{elo_loser1} > {new_elo_loser1}]--"
f"{loser2.capitalize()} ({expected_win_loser2*100:.02f}%)*[{elo_loser2} > {new_elo_loser2}]\n"))

    df = df.sort_values(by='score', ascending=False)
    df.to_csv(SCORES_PATH)
    # logger.info("Scores where successfully saved in the 'scores.csv' file.")
    return "Scoreboard was successfully updated!"

def delete_last_game(df):
    games_history = parse_games_log("games_history.log", display=False)

    if len(games_history) == 0:
        return "Aun no se ha jugado ninguna partida"
    if isinstance(games_history, str):
        return games_history

    last_game = games_history.pop()
    new_games_history = "\n".join([(f"{g[0].strip()} --- "
                                   f"{g[1].strip()}--{g[2].strip()} --- "
                                   f"{g[3].strip()}--{g[4].strip()}") for g in games_history])
    with open('games_history.log', 'w', encoding="utf-8") as games_log:
        games_log.write(new_games_history)
        if len(new_games_history) > 0:
            games_log.write("\n")

    winner1, winner2 = [last_game[1].split("(")[0].strip().lower(),
                        last_game[2].split("(")[0].strip().lower()]
    loser1, loser2 = [last_game[3].split("(")[0].strip().lower(),
                      last_game[4].split("(")[0].strip().lower()]

    new_elo_winner1 = float(re.search(r'\[(.*?)>', last_game[1]).group(1).strip())
    new_elo_winner2 = float(re.search(r'\[(.*?)>', last_game[2]).group(1).strip())
    new_elo_loser1 = float(re.search(r'\[(.*?)>', last_game[3]).group(1).strip())
    new_elo_loser2 = float(re.search(r'\[(.*?)>', last_game[4]).group(1).strip())

    # Update score from players
    df.loc[winner1, 'score'] = new_elo_winner1
    df.loc[winner2, 'score'] = new_elo_winner2
    df.loc[loser1, 'score'] = new_elo_loser1
    df.loc[loser2, 'score'] = new_elo_loser2

    # Update wins and losses from players
    df.loc[winner1, 'wins'] -= 1
    df.loc[winner2, 'wins'] -= 1
    df.loc[loser1, 'losses'] -= 1
    df.loc[loser2, 'losses'] -= 1

    # Update total games played
    df.loc[winner1, 'total'] -= 1
    df.loc[winner2, 'total'] -= 1
    df.loc[loser1, 'total'] -= 1
    df.loc[loser2, 'total'] -= 1

    df = df.sort_values(by='score', ascending=False)
    df.to_csv(SCORES_PATH)
    return "Game was deleted and scoreboard was successfully updated!"

# Define a route for the scoreboard
@app.route(f'/{TOKEN}', methods=['GET', 'POST'])
def scoreboard():
    # Load the scores from the file
    df = pd.read_csv(SCORES_PATH, index_col=0)

    # Update the scores based on the winners and losers
    if request.method == "POST":
        if "updateResults" in request.form:
            session["message_update"] = update_results(request, df)

        if "deleteLastGame" in request.form:
            session["message_update"] = delete_last_game(df)

        # Redirect to games history so the user cannot resend the form reloading the page
        url = url_for("go_home_update")
        return redirect(url)

    html = generate_scoreboard_html(df)

        # Add a form to update the scores
    html += '<h2>Update scores:</h2>'
    html += f'<form method="post" action="/{TOKEN}">'
    html += '<div>'
    html += '<label for="winner1">Winner 1:</label>'
    html += '<input type="text" id="winner1" name="winner1">'
    html += '</div>'
    html += '<div>'
    html += '<label for="winner2">Winner 2:</label>'
    html += '<input type="text" id="winner2" name="winner2">'
    html += '</div>'
    html += '<div>'
    html += '<label for="loser1">Loser 1:</label>'
    html += '<input type="text" id="loser1" name="loser1">'
    html += '</div>'
    html += '<div>'
    html += '<label for="loser2">Loser 2:</label>'
    html += '<input type="text" id="loser2" name="loser2">'
    html += '</div>'
    html += '<input name="updateResults" type="submit" value="Update">'
    html += '</form>'

    # Add a form to delete the last game
    html += '<h2>Delete last game:</h2>'
    html += f'<form method="post" action="/{TOKEN}">'
    html += '<input name="deleteLastGame" type="submit" value="Delete">'
    html += '</form>'

    # Close the form and HTML tags
    html += '</body></html>'

    return html

@app.route(f"/{TOKEN}/update")
def go_home_update():
    # Load the scores from the file
    df = pd.read_csv(SCORES_PATH, index_col=0)

    # Get the messages to display
    message_update = session.get("message_update")

    # Clean the session messages for new updates
    session["message_update"] = ""
    
    # Create the html
    html = generate_scoreboard_html(df)

    html += f"<p>{message_update}</p>"

    html += f'<form action="/{TOKEN}" method="get">'
    html += '<input type="submit" value="ATRAS"></input>'
    html += "</form>"

    # Close the form and HTML tags
    html += '</body></html>'

    return html

# Define a route for the game_history
@app.route(f'/{TOKEN}/game_history')
def game_history():
    # Parse games_history.log
    games = parse_games_log("games_history.log", display=True)

    # Show the games history
    html = '<html><head><title>Historial</title><style>'
    html += styles
    html += '</style></head><body>'
    html += '<h1>Checo  Mus  League</h1>'
    html += NAVIGATION_BAR
    html += '<h2>Historial de Partidas</h2>'

    # if error display message
    if isinstance(games, str):
        html += f'<p>{games}</p></body></html>'
        return html

    html += '<table>'
    html += '<tr><td>Fecha</td><td>Ganador 1</td><td>Ganador 2</td>'
    html += '<td>Perdedor 1</td><td>Perdedor 2</td></tr>'
    for game in games:
        html += f'<tr><td>{game[0]}</td><td>{game[1]}</td>'
        html += f'<td>{game[2]}</td><td>{game[3]}</td>'
        html += f'<td>{game[4]}</td></tr>'
    html += '</table>'

    # Close the form and HTML tags
    html += '</body></html>'
    return html

@app.route(f'/{TOKEN}/add_player', methods=['GET', 'POST'])
def add_player():
    df = pd.read_csv(SCORES_PATH, index_col=0)

    message_new_player = ""
    # If the request method is POST, add a new player to the scoreboard
    if request.method == 'POST':
        message_new_player = "Player was added succesfully!"
        new_player = request.form['new_player']
        if new_player in df.index:
            message_new_player = "Error: There was already a player with that name"
        if not new_player.isalpha():
            message_new_player = "Error: Name must only contain alphabeitc characters"
        df.loc[new_player.strip().lower()] = 1000
        df = df.sort_values(by='score', ascending=False)
        df.to_csv(SCORES_PATH)

    # Generate HTML for the scoreboard
    html = '<html><head><title>Add New Player</title></head><body>'
    html += '<h1>Add a new player to the league</h1>'
    html += f'<form method="post" action="/{TOKEN}/add_player">'
    html += '<label for="new_player">New player:</label>'
    html += '<input type="text" id="new_player" name="new_player">'
    html += '<input type="submit" value="Add">'
    html += '</form>'
    html += f'<p>{message_new_player}</p>'
    html += '</body></html>'
    return html

# Run the app
if __name__ == '__main__':
    app.run(debug=int(os.environ.get("DEBUG")))

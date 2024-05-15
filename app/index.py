# Import necessary modules
import datetime
import os

# Import classes for DB
from db_classes import (
    Games_history_1,
    Games_history_2,
    Games_history_3,
    Season_0,
    Season_1,
    Season_2,
    Season_3,
    db,
)
from flask import Flask, redirect, render_template, request, session, url_for
from markupsafe import Markup

# Import get_docker_secrets to get secrets from docker
from utils import get_docker_secrets

# Basic logger for all the requests
if not int(os.environ.get("DEBUG")):
    import logging

    logging.basicConfig(
        filename="logs/python_index.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    )
    logger = logging.getLogger(__name__)

# Define the Flask app and secret key for the session
app = Flask(__name__)
app.config["SECRET_KEY"] = "a"
if not int(os.environ.get("DEBUG")):
    app.config["SECRET_KEY"] = get_docker_secrets("secret-key")

# Configure the database connection
sql_drivers = os.environ.get("SQL_DRIVERS")
user = get_docker_secrets("mysql-user")
pwd = get_docker_secrets("mysql-user-password")
ip = os.environ.get("IP")
port = os.environ.get("PORT")
db_name = get_docker_secrets("mysql-database")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"{sql_drivers}://{user}:{pwd}@{ip}:{port}/{db_name}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db.init_app(app)

# K is a scaling factor that determines how much ELO points can be gained or lost in a single game
K = 33
LEAGUE_NAME = "Checo Mus League"
DEFAULT_SEASON = 3

# Define the TOKEN where app is going to be deployed, so it is not easy to exploid and to find
TOKEN = "a"
if not int(os.environ.get("DEBUG")):
    TOKEN = get_docker_secrets("TOKEN")

# Layout for the navigation bar
NAVIGATION_BAR = Markup(f"""<nav class="stroke">
    <ul>
        <li class="dropdown">
            <a href="javascript:void(0)" class="dropbtn">Seleccionar temporada</a>
            <div class="dropdown-content">
                <a href="/{TOKEN}/select_season?season=0">Temporada 1</a>
                <a href="/{TOKEN}/select_season?season=1">Temporada 2</a>
                <a href="/{TOKEN}/select_season?season=2">Temporada 3</a>
            </div>
        </li>
        <li><a href="/{TOKEN}">Clasificación</a></li>
        <li><a href="/{TOKEN}/game_history">Historial de partidas</a></li>
    </ul>
</nav>""")

# dict to map names to classes:
TABLES = {
    c.__name__: c
    for c in (
        Season_0,
        Season_1,
        Season_2,
        Season_3,
        Games_history_1,
        Games_history_2,
        Games_history_3,
    )
}


def read_scores(season):
    players = (
        TABLES[f"Season_{season}"]
        .query.order_by(TABLES[f"Season_{season}"].score.desc())
        .all()
    )
    return players


def extra_points_win_ratio(player):
    # Ratio de partidas ganadas
    ratio_player = player.wins / player.total if player.total > 0 else 0
    extra_points_winner1 = 0

    # Factor ratio de partidas ganadas
    if player.total > 15:
        if ratio_player > 0.5:
            extra_points_winner1 = 0.1 * ((ratio_player - 0.5) // 0.05)
            if ratio_player % 0.05 != 0:
                extra_points_winner1 += 0.1 * ((ratio_player % 0.05) / 0.05)
    return extra_points_winner1


def update_results(request_info, season):
    # Get player names
    winner1 = request_info.form["winner1"].strip().lower()
    winner2 = request_info.form["winner2"].strip().lower()
    loser1 = request_info.form["loser1"].strip().lower()
    loser2 = request_info.form["loser2"].strip().lower()

    # Check if all players are diferent
    if len(set([winner1, winner2, loser1, loser2])) != 4:
        return "Error: Hay algun jugador repetido."

    db_w1 = TABLES[f"Season_{season}"].query.filter_by(name=winner1).first()
    db_w2 = TABLES[f"Season_{season}"].query.filter_by(name=winner2).first()
    db_l1 = TABLES[f"Season_{season}"].query.filter_by(name=loser1).first()
    db_l2 = TABLES[f"Season_{season}"].query.filter_by(name=loser2).first()

    # Check if the players exist
    if not (db_w1 and db_w2 and db_l1 and db_l2):
        return "Error: Uno o mas jugadores no existen."

    # Actual ELO from the players
    elo_winner1 = db_w1.score
    elo_winner2 = db_w2.score
    elo_loser1 = db_l1.score
    elo_loser2 = db_l2.score

    # Calculate the new score for each player
    expected_win_winner1 = 1 / (
        10 ** ((((elo_loser2 + elo_loser1) / 2) - (elo_winner1)) / 400) + 1
    )
    expected_win_winner2 = 1 / (
        10 ** ((((elo_loser2 + elo_loser1) / 2) - (elo_winner2)) / 400) + 1
    )
    expected_win_loser1 = 1 / (
        10 ** (-((elo_loser1) - (elo_winner1 + elo_winner2) / 2) / 400) + 1
    )
    expected_win_loser2 = 1 / (
        10 ** (-((elo_loser2) - (elo_winner1 + elo_winner2) / 2) / 400) + 1
    )

    # calculate the extra score for the winning players
    extra_points_winner1 = extra_points_win_ratio(db_w1)
    extra_points_winner2 = extra_points_win_ratio(db_w2)

    # calculate the max loss for the losers
    max_loss_loser1 = min(K * expected_win_loser1, K * 0.6)
    max_loss_loser2 = min(K * expected_win_loser2, K * 0.6)

    new_elo_winner1 = round(
        elo_winner1 + K * (1 - expected_win_winner1) * (1 + extra_points_winner1), 2
    )
    new_elo_winner2 = round(
        elo_winner2 + K * (1 - expected_win_winner2) * (1 + extra_points_winner2), 2
    )
    new_elo_loser1 = round(elo_loser1 - max_loss_loser1, 2)
    new_elo_loser2 = round(elo_loser2 - max_loss_loser2, 2)

    # Update score from players
    db_w1.score = new_elo_winner1
    db_w2.score = new_elo_winner2
    db_l1.score = new_elo_loser1
    db_l2.score = new_elo_loser2

    # Update wins and losses from players
    db_w1.wins += 1
    db_w2.wins += 1
    db_l1.losses += 1
    db_l2.losses += 1

    # Update total games played
    db_w1.total += 1
    db_w2.total += 1
    db_l1.total += 1
    db_l2.total += 1

    # save game and result in the history_games table
    new_game = TABLES[f"Games_history_{season}"](
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        winner1=db_w1.name,
        winner1_percentage=round(expected_win_winner1 * 100, 2),
        winner1_old_elo=elo_winner1,
        winner1_new_elo=new_elo_winner1,
        winner2=db_w2.name,
        winner2_percentage=round(expected_win_winner2 * 100, 2),
        winner2_old_elo=elo_winner2,
        winner2_new_elo=new_elo_winner2,
        loser1=db_l1.name,
        loser1_percentage=round(expected_win_loser1 * 100, 2),
        loser1_old_elo=elo_loser1,
        loser1_new_elo=new_elo_loser1,
        loser2=db_l2.name,
        loser2_percentage=round(expected_win_loser2 * 100, 2),
        loser2_old_elo=elo_loser2,
        loser2_new_elo=new_elo_loser2,
    )

    # Add new game to the db and commit new changes
    db.session.add(new_game)
    db.session.commit()
    # logger.info("Scores where successfully saved in the 'scores.csv' file.")
    return "Scoreboard was successfully updated!"


def delete_last_game(season):
    last_game = (
        TABLES[f"Games_history_{season}"]
        .query.order_by(TABLES[f"Games_history_{season}"].id.desc())
        .first()
    )

    if not (last_game):
        return "Aun no se ha jugado ninguna partida"

    db_w1 = TABLES[f"Season_{season}"].query.filter_by(name=last_game.winner1).first()
    db_w2 = TABLES[f"Season_{season}"].query.filter_by(name=last_game.winner2).first()
    db_l1 = TABLES[f"Season_{season}"].query.filter_by(name=last_game.loser1).first()
    db_l2 = TABLES[f"Season_{season}"].query.filter_by(name=last_game.loser2).first()

    # Update score from players
    db_w1.score = last_game.winner1_old_elo
    db_w2.score = last_game.winner2_old_elo
    db_l1.score = last_game.loser1_old_elo
    db_l2.score = last_game.loser2_old_elo

    # Update wins and losses from players
    db_w1.wins -= 1
    db_w2.wins -= 1
    db_l1.losses -= 1
    db_l2.losses -= 1

    # Update total games played
    db_w1.total -= 1
    db_w2.total -= 1
    db_l1.total -= 1
    db_l2.total -= 1

    db.session.delete(last_game)
    db.session.commit()
    return "Game was deleted and scoreboard was successfully updated!"


# Route for selecting a different season
@app.route(f"/{TOKEN}/select_season", methods=["GET"])
def select_season():
    # Get the selected season from the query parameters
    season = request.args.get("season", type=int, default=DEFAULT_SEASON)

    # Store the selected season in the user's session
    session["selected_season"] = season

    # Redirect to the main scoreboard page
    return redirect(url_for("view_season"))


# Route for selecting a different season
@app.route(f"/{TOKEN}/view_season", methods=["GET"])
def view_season():
    # Get the selected season from the user's session or use the default value (1)
    selected_season = session.get("selected_season", None)

    # Load the data for the current selected season
    players = read_scores(selected_season)

    # Redirect to the main scoreboard page
    return render_template(
        "score_season.html",
        league_name=LEAGUE_NAME,
        navigation_bar=NAVIGATION_BAR,
        players=enumerate(players, start=1),
        season=selected_season,
    )


# Define a route for the scoreboard
@app.route(f"/{TOKEN}", methods=["GET", "POST"])
def scoreboard():
    # Load the data for the current selected season
    players = read_scores(DEFAULT_SEASON)

    # Set the selected season in the user's session to 2,
    # to view the current season games history, when clicking
    # in History Games
    session["selected_season"] = DEFAULT_SEASON

    # Update the scores based on the winners and losers
    if request.method == "POST":
        if "updateResults" in request.form:
            session["message_update"] = update_results(request, DEFAULT_SEASON)

        if "deleteLastGame" in request.form:
            session["message_update"] = delete_last_game(DEFAULT_SEASON)

        # Redirect to games history so the user cannot resend the form reloading the page
        return redirect(url_for("go_home_update"))

    # Generate Jinja2 template for the scoreboard
    return render_template(
        "scoreboard.html",
        league_name=LEAGUE_NAME,
        navigation_bar=NAVIGATION_BAR,
        players=enumerate(players, start=1),
    )


@app.route(f"/{TOKEN}/update")
def go_home_update():
    # Load the scores from the file
    players = read_scores(DEFAULT_SEASON)

    # Get the messages to display
    message_update = session.get("message_update")

    # Clean the session messages for new updates
    session["message_update"] = ""

    # Generate Jinja2 template for the scoreboard
    return render_template(
        "score_update.html",
        league_name=LEAGUE_NAME,
        navigation_bar=NAVIGATION_BAR,
        players=enumerate(players, start=1),
        message_update=message_update,
    )


# Define a route for the game_history
@app.route(f"/{TOKEN}/game_history")
def game_history():
    # Get the selected season from the user's session or use the default value (1)
    selected_season = session.get("selected_season", None)

    games = None
    if selected_season > 0:
        # Parse games_history.log
        games = TABLES[f"Games_history_{selected_season}"].query.all()

    # Generate Jinja2 template for the game history
    return render_template(
        "game_history.html",
        league_name=LEAGUE_NAME,
        navigation_bar=NAVIGATION_BAR,
        games=games,
        season=selected_season,
    )


@app.route(f"/{TOKEN}/add_player", methods=["GET", "POST"])
def add_player():
    message_new_player = ""

    # If the request method is POST, add a new player to the scoreboard
    if request.method == "POST":
        message_new_player = "Player was added succesfully!"
        new_player_name = request.form["new_player"]
        if not new_player_name.isalpha():
            message_new_player = "Error: Name must only contain alphabeitc characters"
            return render_template(
                "add_player.html", message_new_player=message_new_player
            )
        if (
            TABLES[f"Season_{DEFAULT_SEASON}"]
            .query.filter_by(name=new_player_name)
            .first()
        ):
            message_new_player = "Error: There was already a player with that name"
        new_player = TABLES[f"Season_{DEFAULT_SEASON}"](
            name=new_player_name, score=1000, wins=0, losses=0, total=0
        )
        db.session.add(new_player)
        db.session.commit()

    # Generate Jinja2 template for adding a new player
    return render_template("add_player.html", message_new_player=message_new_player)


# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=int(os.environ.get("DEBUG")))

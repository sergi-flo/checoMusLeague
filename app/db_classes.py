from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Define the Player Class for DB
class Season(object):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    score = db.Column(db.Float, nullable=False)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<User %s (%s%%) %sW/%sL %sT>' % (self.name, self.score, self.wins, self.losses, self.total)
    
class Season_0(Season, db.Model):
    __tablename__ = "season_0"
class Season_1(Season, db.Model):
    __tablename__ = "season_1"
class Season_2(Season, db.Model):
    __tablename__ = "season_2"
class Season_3(Season, db.Model):
    __tablename__ = "season_3"

# Define the Game class for DB
class Games_history(object):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    winner1 = db.Column(db.String(255), nullable=False)
    winner1_percentage = db.Column(db.Float, nullable=False)
    winner1_old_elo = db.Column(db.Float, nullable=False)
    winner1_new_elo = db.Column(db.Float, nullable=False)
    winner2 = db.Column(db.String(255), nullable=False)
    winner2_percentage = db.Column(db.Float, nullable=False)
    winner2_old_elo = db.Column(db.Float, nullable=False)
    winner2_new_elo = db.Column(db.Float, nullable=False)
    loser1 = db.Column(db.String(255), nullable=False)
    loser1_percentage = db.Column(db.Float, nullable=False)
    loser1_old_elo = db.Column(db.Float, nullable=False)
    loser1_new_elo = db.Column(db.Float, nullable=False)
    loser2 = db.Column(db.String(255), nullable=False)
    loser2_percentage = db.Column(db.Float, nullable=False)
    loser2_old_elo = db.Column(db.Float, nullable=False)
    loser2_new_elo = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return '<Game -> %s --- %s (%s%%)*[%s > %s]--%s (%s%%)*[%s > %s] --- %s (%s%%)*[%s > %s]--%s (%s%%)*[%s > %s]>' % (self.timestamp,
                                                                                                                       self.winner1,
                                                                                                                       self.winner1_percentage,
                                                                                                                       self.winner1_old_elo,
                                                                                                                       self.winner1_new_elo,
                                                                                                                       self.winner2,
                                                                                                                       self.winner2_percentage,
                                                                                                                       self.winner2_old_elo,
                                                                                                                       self.winner2_new_elo,
                                                                                                                       self.winner1,
                                                                                                                       self.loser1_percentage,
                                                                                                                       self.loser1_old_elo,
                                                                                                                       self.loser1_new_elo,
                                                                                                                       self.loser2,
                                                                                                                       self.loser2_percentage,
                                                                                                                       self.loser2_old_elo,
                                                                                                                       self.loser2_new_elo)
    
class Games_history_0(Games_history, db.Model):
    __tablename__ = "games_history_0"
class Games_history_1(Games_history, db.Model):
    __tablename__ = "games_history_1"
class Games_history_2(Games_history, db.Model):
    __tablename__ = "games_history_2"
class Games_history_3(Games_history, db.Model):
    __tablename__ = "games_history_3"

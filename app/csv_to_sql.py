import csv
import os
import re
from datetime import datetime
import pymysql
from utils import get_docker_secrets

# Replace these variables with your actual database credentials
database_user = get_docker_secrets("mysql-user")
database_user_password = get_docker_secrets("mysql-user-password")
ip = os.environ.get("IP")
database_name = get_docker_secrets("mysql-database")
port = int(os.environ.get("PORT"))

# Replace this with the path to your CSV file
seasons = ["0", "1", "2"]

if "__main__" == __name__:
    conn = pymysql.connect(host=ip,
                        user=database_user,
                        password=database_user_password,
                        port=port)
    cursor = conn.cursor()
    cursor.execute(f"USE {database_name}")
    try:
        for season in seasons:
            # create and populate the table users for the webpage
            cursor.execute(f""" CREATE TABLE season_{season}(id INT AUTO_INCREMENT PRIMARY KEY,
                                                name VARCHAR(255) UNIQUE NOT NULL,
                                                score FLOAT,
                                                wins INT,
                                                losses INT,
                                                total INT
                                                );""")

            query_users = f"""INSERT INTO season_{season} (name, score, wins, losses, total) 
            VALUES (%s, %s, %s, %s, %s)"""

            with open(f"data/scores_{season}.csv", 'r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    player = (row[''],
                            float(row['score']),
                            int(row['wins']), 
                            int(row['losses']),
                            int(row['total']))
                    cursor.execute(query_users, player)
                print(f'Data inserted into season_{season} table successfully.')

        # create and populate the table users for the webpage
            cursor.execute(f""" CREATE TABLE games_history_{season}(id INT AUTO_INCREMENT PRIMARY KEY,
                                                timestamp DATETIME,
                                                winner1 VARCHAR(255),
                                                winner1_percentage FLOAT,
                                                winner1_old_elo FLOAT,
                                                winner1_new_elo FLOAT,
                                                winner2 VARCHAR(255),
                                                winner2_percentage FLOAT,
                                                winner2_old_elo FLOAT,
                                                winner2_new_elo FLOAT,
                                                loser1 VARCHAR(255),
                                                loser1_percentage FLOAT,
                                                loser1_old_elo FLOAT,
                                                loser1_new_elo FLOAT,
                                                loser2 VARCHAR(255),
                                                loser2_percentage FLOAT,
                                                loser2_old_elo FLOAT,
                                                loser2_new_elo FLOAT
                                                );""")
            
            query_game = f"""INSERT INTO games_history_{season} (timestamp, 
            winner1, winner1_percentage, winner1_old_elo, winner1_new_elo,
            winner2, winner2_percentage, winner2_old_elo, winner2_new_elo,
            loser1, loser1_percentage, loser1_old_elo, loser1_new_elo,
            loser2, loser2_percentage, loser2_old_elo, loser2_new_elo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            if int(season) > 0:
                with open(f"data/games_history_{season}.log", 'r') as log_file:
                    for line in log_file:
                        if line == "":
                            continue
                        line = line.replace("<br />", "*").replace("->", ">")
                        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) --- (.*?)\((.*?)%\)\*\[(.*?) > (.*?)\]--(.*?)\((.*?)%\)\*\[(.*?) > (.*?)\] --- (.*?)\((.*?)%\)\*\[(.*?) > (.*?)\]--(.*?)\((.*?)%\)\*\[(.*?) > (.*?)\]'
                        matches = re.match(pattern, line)
                        timestamp = datetime.strptime(matches.group(1), '%Y-%m-%d %H:%M:%S')
                        winner1, winner2, loser1, loser2 = matches.group(2,6,10,14)
                        winner1_percentage, winner1_old_elo, winner1_new_elo = (float(e) for e in matches.group(3, 4, 5))
                        winner2_percentage, winner2_old_elo, winner2_new_elo = (float(e) for e in matches.group(7, 8, 9))
                        loser1_percentage, loser1_old_elo, loser1_new_elo = (float(e) for e in matches.group(11, 12, 13))
                        loser2_percentage, loser2_old_elo, loser2_new_elo = (float(e) for e in matches.group(15, 16, 17))
                        game = (timestamp, winner1, winner1_percentage, winner1_old_elo, winner1_new_elo,
                                winner2, winner2_percentage, winner2_old_elo, winner2_new_elo,
                                loser1, loser1_percentage, loser1_old_elo, loser1_new_elo,
                                loser2, loser2_percentage, loser2_old_elo, loser2_new_elo)
                        cursor.execute(query_game, game)
                    print(f'Data inserted into games_history_{season} table successfully.')

        conn.commit()
        cursor.close()
        conn.close()
        print("Done")

        conn = pymysql.connect(host=ip,
                            user=database_user,
                            password=database_user_password,
                            port=port)
        print("conection with user ", database_user, " working")
        conn.close()
    except:
        print("Tables already created, skipping ...")
    
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, json
from helper import dict_factory, query_user

app = Flask(__name__)

DB = "database.db"

#############################################################
#               HELPER/DB EDITING ENDPOINTS
#############################################################

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/db/new")
def new_db():
    conn = sqlite3.connect(DB)

    conn.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, picture TEXT, company TEXT, email TEXT NOT NULL, phone TEXT, latitude REAL NOT NULL, longitude REAL NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS skills(id INTEGER PRIMARY KEY, userid INTEGER NOT NULL, name TEXT NOT NULL, rating INTEGER NOT NULL)')
    conn.close()

    return 'empty db created'

@app.route('/db/clear')
def clear_db():
    conn = sqlite3.connect(DB)

    conn.execute('DROP TABLE IF EXISTS users')
    conn.execute('DROP TABLE IF EXISTS skills')
    conn.close()

    return 'dbs cleared'

@app.route('/db/fill')
def fill_db():
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "users.json")
    data = json.load(open(json_url))

    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()

        for user in data:
            values = (user["name"], user["picture"], user["company"], user["email"], user["phone"], user["latitude"], user["longitude"])
            cur.execute("INSERT INTO users(name, picture, company, email, phone, latitude, longitude) VALUES (?,?,?,?,?,?,?)", values)

            for skills in user["skills"]:
                cur.execute("INSERT INTO skills(userid, name, rating) VALUES (?,?,?)", (cur.lastrowid, skills["name"], skills["rating"]))

    return 'dbs filled with dummy data'

#########################################################################
#                           REQUIRED ENDPOINTS
#########################################################################

@app.route('/users')
def get_users():
    with sqlite3.connect(DB) as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()
        # cur.execute("SELECT users.*, (SELECT skills.* FROM skills WHERE users.id=skills.userid FOR JSON PATH) AS skills FROM users")
        cur.execute("SELECT users.* from users")

        users = cur.fetchall()

        for user in users:
            id = user["id"]

            cur.execute("SELECT skills.name, skills.rating FROM skills WHERE skills.userid=(?)", (id,))
            skills = cur.fetchall()
            user["skills"] = skills
    
    return json.jsonify(users)

@app.route('/users/<userid>', methods = ['PUT', 'GET'])
def get_user(userid):
    with sqlite3.connect(DB) as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()

        if request.method == 'GET':
            # cur.execute("SELECT users.*, group_concat(skills.*) AS user_skills FROM users LEFT OUTER JOIN users ON users.id=(?) AND skills.userid=(?)", (userid,userid))

            user = query_user(cur, userid)

        elif request.is_json:
            cur.execute("PRAGMA table_info(users)")
            valid_keys = cur.fetchall()

            # being transaction
            # cur.execute("BEGIN")

            for key in request.json.keys():
                if key == 'skills':
                    for skill in request.json[key]:
                        # cur.execute("INSERT INTO skills(userid, name, rating) VALUES(?,?,?) ON DUPLICATE", (userid, skill["name"], skill["rating"]))
                        cur.execute("SELECT * FROM skills WHERE name = ? AND userid = ?", (skill["name"], userid))

                        if cur.fetchone():
                            cur.execute("UPDATE skills SET rating=? WHERE userid=? AND name=?", (skill["rating"], userid, skill["name"]))
                        else:
                            cur.execute("INSERT INTO skills(userid, name, rating) VALUES(?,?,?)", (userid, skill["name"], skill["rating"]))

                elif key in list(map(lambda k: k["name"], valid_keys)):
                    cur.execute("UPDATE users SET %s=(?) WHERE users.id=(?)" %key, (request.json[key], userid))

            # cur.execute("COMMIT")

            user = query_user(cur, userid)    

        else:
            print("improper HTTP request")

    return json.jsonify(user)

@app.route('/skills/')
def get_skills():
    rating = request.args.get('rating') or 0
    frequency = request.args.get('frequency') or 0

    with sqlite3.connect(DB) as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()
        # cur.execute("SELECT users.*, group_concat(skills.*) AS user_skills FROM users LEFT OUTER JOIN users ON users.id=(?) AND skills.userid=(?)", (userid,userid))

        cur.execute("SELECT name, COUNT(*) AS num_users, AVG(rating) AS average_rating FROM skills WHERE rating >= {} GROUP BY name HAVING COUNT(*) >= {}".format(rating, frequency))
        skills = cur.fetchall()

    return json.jsonify(skills)






if __name__ == "__main__":
    app.run(debug = True)

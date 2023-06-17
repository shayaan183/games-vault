import os

from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, lookup, db

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Search for games"""

    user_id = session["user_id"]

    con, cur = db()

    row = cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = row.fetchall()

    name = row[0][1]

    con.close()

    return render_template("index.html", name=name)


@app.route("/result", methods=["GET", "POST"])
@login_required
def result():
    """Show results of search"""

    if request.method == "POST":
        game_search = request.form.get("name")

        games = lookup(game_search)

        id = games[0]["id"]
        name = games[0]["name"]
        released = games[0]["released"]
        background_image = games[0]["background_image"]
        metacritic = games[0]["metacritic"]
        esrb = games[0]["esrb"]
        platform = games[0]["platform"]
        genres = games[0]["genres"]
        stores = games[0]["stores"]

        user_id = session["user_id"]

        con, cur = db()

        rows = cur.execute("SELECT game_id FROM vault WHERE user_id = ?", (user_id,))
        saved_game_id = rows.fetchall()

        con.close()

        return render_template(
            "result.html",
            game_search=game_search,
            games=games,
            id=id,
            name=name,
            released=released,
            background_image=background_image,
            esrb=esrb,
            metacritic=metacritic,
            platform=platform,
            genres=genres,
            stores=stores,
            saved_game_id=saved_game_id,
        )

    else:
        return render_template("index.html")


@app.route("/add", methods=["POST"])
@login_required
def add():
    """Add a game to your vault"""

    game_id = request.form.get("id")
    name = request.form.get("name")
    released = request.form.get("released")
    background_image = request.form.get("background_image")
    metacritic = request.form.get("metacritic")
    esrb = request.form.get("esrb")
    platform = request.form.get("platform")
    genres = request.form.get("genres")
    stores = request.form.get("stores")

    user_id = session["user_id"]

    con, cur = db()

    cur.execute("INSERT INTO vault (user_id, game_id, name, released, background_image, metacritic, esrb, platform, genres, stores) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, game_id, name, released, background_image, metacritic, esrb, platform, genres, stores))

    con.commit()
    con.close()

    return redirect("/vault")


@app.route("/vault")
@login_required
def vault():
    """Show user's vault"""

    user_id = session["user_id"]

    con, cur = db()

    saved = cur.execute("SELECT * FROM vault WHERE user_id = ?", (user_id,))
    saved = saved.fetchall()

    con.close()

    return render_template("vault.html", saved=saved)


@app.route("/remove", methods=["POST"])
@login_required
def remove():
    """Remove a game from your vault"""

    user_id = session["user_id"]

    game_id = request.form.get("id")

    con, cur = db()

    cur.execute("DELETE FROM vault WHERE user_id = ? AND game_id = ?", (user_id, game_id))

    con.commit()
    con.close()

    return redirect("/vault")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Show user's account settings"""
    user_id = session["user_id"]
    con, cur = db()

    row = cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))

    row = row.fetchall()

    current_name = row[0][1]
    current_username = row[0][2]

    if request.method == "POST":
        # Change name
        name = request.form.get("name")
        if name:
            cur.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))

            con.commit()
            con.close()

            message_success = "Name changed successfully"

            return render_template("settings.html", message_success=message_success)

        # Change username
        username = request.form.get("username")
        if username:
            if len(username) < 4:
                message_err = "Please enter a username with at least 4 characters"
                return render_template("register.html", message_err=message_err)

            try:
                cur.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))

                con.commit()
                con.close()

                message_success = "Username updated successfully"

                return render_template("settings.html", message_success=message_success)

            except:
                message_err = "This username is already exists. Please write a new one"

                return render_template("settings.html", message_err=message_err)

        # Change password
        password_old = request.form.get("password_old")
        password_new = request.form.get("password_new")
        confirmation = request.form.get("confirmation")
        if password_old and password_new and confirmation:
            if password_old == password_new:
                message_err = "Your old and new password are the same. Please write a new one"

                return render_template("settings.html", message_err=message_err)

            if password_new != confirmation:
                message_err = "Your new passwords does not match"

                return render_template("settings.html", message_err=message_err)

            if not check_password_hash(row[0][3], password_old):
                message_err = "Your old password does not match. Please re-enter it"

                return render_template("settings.html", message_err=message_err)

            new_hash = generate_password_hash(password_new)

            cur.execute("UPDATE users SET hash = ? WHERE id = ?", (new_hash, user_id))

            con.commit()
            con.close()

            message_success = "Password updated successfully"

            return render_template("settings.html", message_success=message_success)

        return redirect("/settings")

    else:
        return render_template("settings.html", current_name=current_name, current_username=current_username)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        con, cur = db()
        
        if not name or not username or not password:
            message = "Please enter your name and/or a username and/or password"
            return render_template("register.html", message=message)

        if len(username) < 4:
            message = "Please enter a username with at least 4 characters"
            return render_template("register.html", message=message)

        if not confirmation:
            message = "Please re-enter your password"
            return render_template("register.html", message=message)

        if password != confirmation:
            message = "Your passwords do not match"
            return render_template("register.html", message=message)

        hash = generate_password_hash(password)

        try:
            cur.execute("INSERT INTO users (name, username, hash) VALUES (?, ?, ?)", (name, username, hash))
            con.commit()

            user = cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = user.fetchall()

            session["user_id"] = user[0][0]

            con.close()

            return redirect("/")

        except:
            message = "Username already exists"
            return render_template("register.html", message=message)

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            message = "Provide a username and/or password"
            return render_template("login.html", message=message)

        con, cur = db()

        rows = cur.execute("SELECT * FROM users WHERE username = ?", (username,))

        rows = rows.fetchall()

        if len(rows) != 1 or not check_password_hash(rows[0][3], password):
            message = "Invalid username and/or password"
            return render_template("login.html", message=message)

        session["user_id"] = rows[0][0]

        con.close()

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")

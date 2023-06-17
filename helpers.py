import os
import requests
import sqlite3

from flask import redirect, render_template, request, session
from functools import wraps
from datetime import datetime


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def lookup(game):
    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://api.rawg.io/api/games?key={api_key}&search={game}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse responce
    try:
        result = response.json()

        results_dict = result["results"]

        x = 0

        games_list = []

        for i in results_dict:
            platforms_list = []
            genres_list = []
            stores_list = []

            platforms_dict = result["results"][x]["platforms"]
            genres_dict = result["results"][x]["genres"]
            stores_dict = result["results"][x]["stores"]
            esrb_dict = result["results"][x]["esrb_rating"]

            id = i["id"]
            name = i["name"]
            released = i["released"]
            background_image = i["background_image"]
            metacritic = i["metacritic"]

            if esrb_dict != None:
                esrb = esrb_dict["name"]
            else:
                esrb = None

            if platforms_dict != None:
                for j in platforms_dict:
                    platform = j["platform"]["name"]
                    platforms_list.append(platform)

            platform_str = ", ".join(platforms_list)

            if genres_dict != None:
                for j in genres_dict:
                    genres = j["name"]
                    genres_list.append(genres)

            genre_str = ", ".join(genres_list)

            if stores_dict != None:
                for j in stores_dict:
                    stores = j["store"]["name"]
                    stores_list.append(stores)

            stores_str = ", ".join(stores_list)

            released_date = datetime.strptime(released, "%Y-%m-%d")
            released_formatted = released_date.strftime("%B %d, %Y")

            games_list.append(
                {
                    "id": id,
                    "name": name,
                    "released": released_formatted,
                    "background_image": background_image,
                    "metacritic": metacritic,
                    "esrb": esrb,
                    "platform": platform_str,
                    "genres": genre_str,
                    "stores": stores_str,
                }
            )

            x += 1

        return games_list

    except (KeyError, TypeError, ValueError):
        return None


def db():
    con = sqlite3.connect("gamesvault.db")
    cur = con.cursor()

    return con, cur

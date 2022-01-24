# Resources:
# https://cloud.google.com/community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run
# https://www.linkedin.com/learning/building-restful-apis-with-flask
# writing files with sqlite is NOT SUPPORTED on app engine, which is why I migrated to Firebase

import urllib
from flask import Flask, jsonify
import os
import requests
from decouple import config
import time
from firebase_admin import credentials, firestore, initialize_app

app = Flask(__name__)

# Clash Royale API token (create at https://developer.clashroyale.com/#/account)
TOKEN = config('TOKEN')
headers = {'authorization': 'Bearer ' + TOKEN}

# initialize firestore DB
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()

decks_ref = db.collection('decks')
time_ref = db.collection('updateTime')

refresh_interval = 60  # update weekly 604800
ranking_depth = 15  # deck recommendations based on top (ranking_depth) users


@app.route('/test')
def test():
    try:
        request_url = 'https://api.clashroyale.com/v1/cards'
        r = requests.get(request_url, headers=headers)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    if r.status_code == 200:
        return r.json(), 200
    elif r.status_code == 403:
        return jsonify(message="Error: Not authorized " + TOKEN), 403
    elif r.status_code == 404:
        return jsonify(message="Error: 404 not found"), 404
    else:
        return jsonify(message="Unknown error"), 500


# calls CR API for current global rankings (top 1000 players), returns json response
def get_rankings():
    try:
        request_url = 'https://api.clashroyale.com/v1/locations/global/rankings/players'
        r = requests.get(request_url, headers=headers)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    if r.status_code == 200:
        return r.json()
    elif r.status_code == 403:
        return jsonify(message="Error: Not authorized"), 403
    elif r.status_code == 404:
        return jsonify(message="Error: 404 not found"), 404
    else:
        return jsonify(message="Unknown error"), 500


def update_player_info():
    rankings_json = get_rankings()
    if isinstance(rankings_json, dict) and 'items' in rankings_json:
        reset_players()
        players = rankings_json['items'][:ranking_depth]
        for player in players:
            player_json = get_player_json(player)
            if 'tag' in player_json:
                add_player(player_json)
            else:
                print('skipped player')
        set_timestamp()


def reset_players():
    decks = list(decks_ref.get())
    for deck in decks:
        decks_ref.document(deck.id).delete()


def add_player(json):
    tag = json['tag']
    name = json['name']
    rank = json['leagueStatistics']['currentSeason']['rank']
    current_trophies = json['leagueStatistics']['currentSeason']['trophies']
    current_deck = make_deck_array(json['currentDeck'])
    db.collection('decks').add({'tag': tag, 'name': name, 'rank': rank, 'current_trophies': current_trophies,
                                'deck': current_deck})


def make_deck_array(deck_info):
    ary = []
    for deck_json in deck_info:
        card_name = deck_json['name']
        ary.append(card_name)
    return ary


def get_player_json(player_json):
    player_id = urllib.parse.quote(player_json['tag'])
    request_url = 'https://api.clashroyale.com/v1/players/' + player_id
    try:
        r = requests.get(request_url, headers=headers)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    if r.status_code == 200:
        return r.json()
    elif r.status_code == 404:
        return jsonify(message='Error: 404 not found')
    return jsonify(message='Unknown error')


def set_timestamp():
    timestamps = list(time_ref.get())
    for timestamp in timestamps:
        time_ref.document(timestamp.id).delete()
    time_ref.add({'timestamp': int(time.time())})


def time_outdated():
    current_time = int(time.time())
    timestamps = list(time_ref.get())
    newest_time = timestamps[len(timestamps) - 1].to_dict()['timestamp']
    if abs(current_time - newest_time) > refresh_interval:
        print('refreshing data')
        return True
    print('data is still relevant')
    return False


# returns json dictionary containing top ranking_depth decks (e.g., ["Mugi": {"Deck": [], "Rank": 1}, ...]
@app.route('/', methods=['GET'])
def get_data():
    if time_outdated():
        update_player_info()
    data_array = []
    decks = list(decks_ref.get())
    for deck in decks:
        data_array.append(deck.to_dict())
    timestamps = list(time_ref.get())
    newest_time = timestamps[len(timestamps) - 1].to_dict()['timestamp']
    data_dict = {'data': data_array, 'timestamp': newest_time}
    return jsonify(data_dict), 200


if __name__ == '__main__':
    # test_firebase()
    app.run()

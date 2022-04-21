from flask import Flask, session, request, redirect, render_template, url_for
from datetime import timedelta
from urllib.parse import quote
import requests
import json

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='dev',
    PERMANENT_SESSION_LIFETIME=timedelta(days=7)
)

# Client Keys
CLIENT_ID = '0e0d3a9d83594e7fb76911279b6e2aa3'
CLIENT_SECRET = '9eea43a5790342daab2f152240cd1205'

# Server-side Parameters
SCOPE = 'user-read-private user-read-email'
REDIRECT_URI = 'https://cratedigger-klaas.herokuapp.com/api/callback'
# REDIRECT_URI = 'http://localhost:5000/api/callback'
STATE = ''

auth_query_parameters = {
    'response_type': 'code',
    'redirect_uri': REDIRECT_URI,
    'scope': SCOPE,
    'state': STATE,
    'client_id': CLIENT_ID
}

@app.before_request
def before_request():
    session.permanent = True

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')


@app.route('/api/authorize')
def authorize():
    SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"

    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    print(auth_url)
    return redirect(auth_url)


@app.route('/api/callback')
def callback():
    print(f'In callback.. {request.args}')
    # Auth Step 4: Requests refresh and access tokens
    if 'error' in request.args:
        print('Request was denied by user')
    else:
        auth_token = request.args['code']
        code_payload = {
            'grant_type': 'authorization_code',
            'code': str(auth_token),
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }

        SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
        post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

        # Auth Step 5: Tokens are Returned to Application
        response_data = json.loads(post_request.text)
        session['access_token'] = response_data['access_token']
        session['refresh_token'] = response_data['refresh_token']
        #print(response_data['access_token'])

    return redirect(url_for('catch_all'))
    # return redirect('http://localhost:3000/login')


@app.route('/api/is-authenticated')
def is_authorized():
    if 'access_token' in session:
        print('Access Token exists')
        print(session['access_token'])
        print(session['refresh_token'])

        return { 'authenticated': True }
    else:
        print('No access token')
        return { 'authenticated': False }


@app.route('/api/refresh-token')
def refresh_token():
    body_parameters = {
        'grant_type': 'refresh_token',
        'refresh_token': session['refresh_token'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=body_parameters)
    
    if post_request.status_code == 200:
        response_json = json.loads(post_request.text)
        session['access_token'] = response_json['access_token']
        if 'refresh_token' in response_json:
            session['refresh_token'] = response_json['refresh_token']

        return {'status': 'Success'}
    else:
        return {'status': 'Failed'}


@app.route('/api/user')
def user():
    headers = {
        'Authorization': f"Bearer {session['access_token']}",
        'Content-Type': 'application/json'
    }
    get_request = requests.get('https://api.spotify.com/v1/me', headers=headers)

    if get_request.status_code == 401: # If token expires
        error_data = json.loads(get_request.text)
        return error_data, 401
    else:
        response_data = json.loads(get_request.text)
        return response_data


@app.route('/api/search', methods=['GET'])
def search():
    args = request.args
    #print(f'Search.. {args}')
    artist_name = args['artist_name']
    start_date = args['start_date']
    end_date = args['end_date']

    start_date_month = start_date.split('-')[0]
    start_date_year = start_date.split('-')[1]
    end_date_month = end_date.split('-')[0]
    end_date_year = end_date.split('-')[1]

    if start_date_year == end_date_year:
        year_for_query = start_date_year
    else:
        year_for_query = f'{start_date_year}-{end_date_year}'

    headers = {
        'Authorization': f"Bearer {session['access_token']}",
        'Content-Type': 'application/json'
    }

    # year_for_query = '2017'
    params = {
        'q': f'artist:{artist_name} year:{year_for_query}',
        'type': 'track',
        'limit': 50
    }
    get_request = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
    #get_request.status_code = 401
    if get_request.status_code == 401: # If token expires
        print(get_request.status_code)
        error_data = json.loads(get_request.text)
        return error_data, 401
    else:
        print(get_request.status_code)
        response_data = json.loads(get_request.text)
        # Filter the returned tracks on the months entered by user
        response_data['tracks']['items'] = list(filter(lambda track: _filter_on_months(start_date_month, end_date_month, track), response_data['tracks']['items']))

        return response_data


@app.route("/api/logout", methods=['POST'])
def logout():
    session.pop('access_token', None)
    session.pop('refresh_token', None)
    return redirect(url_for('catch_all'))


# Helper function required to filter on the month inputted by the user. 
# Reason being that the spotify search API only gives results for year, thus manually need to filter on the months entered by user.
# We only need to check for month as 1) year is catered for by user input 2) day precision is not allowed from user
def _filter_on_months(start_month, end_month, track):
    date_components = track['album']['release_date'].split('-') # 0 -> year, 1 -> month, 2 -> day [depending on release_date_precision]
    track_month = date_components[1]

    if int(track_month) >= int(start_month) and int(track_month) <= int(end_month):
        print(f"Comparison of {track['album']['release_date']} returned {True}")
        return True

    print(f"Comparison of {track['album']['release_date']} returned {False}")
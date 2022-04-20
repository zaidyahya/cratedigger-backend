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

@app.route("/")
def home():
    return render_template('index.html')

    # if 'user' in session:
    #     return redirect('/user')
    # else:
    #     session['user'] = 'Zaid'
    #     return redirect('/new')

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

    return redirect(url_for('home'))

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

@app.route("/user")
def user():
    return redirect(url_for('home'))

    # return f"<p>Hello, {session['user']}"

@app.route("/new")
def new():
    return "<p>New session inputted..</p>"

@app.route("/api/logout", methods=['POST'])
def logout():
    session.pop('access_token', None)
    session.pop('refresh_token', None)
    return "<p>Bye..</p>"
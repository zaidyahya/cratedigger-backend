from flask import Flask, session, redirect
from datetime import timedelta

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='dev',
    #PERMANENT_SESSION_LIFETIME=timedelta(days=7)
)

@app.route("/")
def hello_world():
    if 'user' in session:
        return redirect('/user')
    else:
        session['user'] = 'Zaid'
        return redirect('/new')

@app.route("/user")
def user():
    return f"<p>Hello, {session['user']}"

@app.route("/new")
def new():
    return "<p>New session inputted..</p>"

@app.route("/logout")
def logout():
    session.pop('user', None)
    return "<p>Bye..</p>"
    #return redirect('/')
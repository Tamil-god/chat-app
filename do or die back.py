# === File: app.py ===
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import json, os

app = Flask(__name__)
app.secret_key = 'secret'
socketio = SocketIO(app)

USERS_FILE = 'users.json'
CHAT_FILE = 'chat.json'

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(CHAT_FILE):
    with open(CHAT_FILE, 'w') as f:
        json.dump([], f)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open(USERS_FILE) as f:
            users = json.load(f)
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open(USERS_FILE) as f:
            users = json.load(f)
        if username in users:
            return render_template('register.html', error='Username already exists')
        users[username] = password
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('send_message')
def send_message(data):
    data['username'] = session.get('username', 'Guest')
    with open(CHAT_FILE) as f:
        chat_data = json.load(f)
    chat_data.append(data)
    with open(CHAT_FILE, 'w') as f:
        json.dump(chat_data, f)
    emit('receive_message', data, broadcast=True)

@socketio.on('connect')
def connect():
    with open(CHAT_FILE) as f:
        chat_data = json.load(f)
    emit('load_messages', chat_data)

if __name__ == '__main__':
    socketio.run(app, debug=True)

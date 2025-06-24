import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, emit, send
import json
import os
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'do-or-die-secret-key'
socketio = SocketIO(app, async_mode='eventlet')

# Ensure users.json exists
if not os.path.exists('users.json'):
    with open('users.json', 'w') as f:
        json.dump({}, f)

# Ensure messages.json exists
if not os.path.exists('messages.json'):
    with open('messages.json', 'w') as f:
        json.dump([], f)

def get_ist_time():
    indian_timezone = pytz.timezone("Asia/Kolkata")
    now = datetime.now(indian_timezone)
    return now.strftime('%I:%M %p'), now.strftime('%d-%m-%Y')
@app.route('/')
def home():
    return render_template('app_website.html')  # Render your homepage here instead of redirecting to login

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']

        with open('users.json', 'r') as f:
            users = json.load(f)

        if uname in users:
            return "Username already exists!"

        users[uname] = pwd

        with open('users.json', 'w') as f:
            json.dump(users, f)

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']

        with open('users.json', 'r') as f:
            users = json.load(f)

        if uname in users and users[uname] == pwd:
            session['username'] = uname
            return redirect(url_for('chat'))

        return "Invalid username or password!"

    return render_template('login.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))

    with open('messages.json', 'r') as f:
        messages = json.load(f)

    username = session['username']
    is_admin = username.lower() == "thamizhamuthan"  # Case-insensitive admin check

    return render_template('chat.html', username=username, is_admin=is_admin, messages=messages)

@socketio.on('message')
def handle_message(msg):
    user = session.get('username', 'Unknown')
    time, date = get_ist_time()
    message_data = {
        "user": user,
        "text": msg,
        "time": time,
        "date": date
    }

    with open('messages.json', 'r') as f:
        data = json.load(f)

    data.append(message_data)

    with open('messages.json', 'w') as f:
        json.dump(data, f, indent=2)

    send(message_data, broadcast=True)

@socketio.on('typing')
def handle_typing(data):
    emit('user_typing', data, broadcast=True, include_self=False)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/clear', methods=['POST'])
def clear_messages():
    with open('messages.json', 'w') as f:
        json.dump([], f)  # Clear message list
    return '', 204  # Success without content

if __name__ == '__main__':
    port = 5050
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)


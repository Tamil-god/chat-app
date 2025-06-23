from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, send
import json, os
from datetime import datetime
from datetime import datetime
from pytz import timezone
india_time = datetime.now(timezone("Asia/Kolkata")).strftime('%I:%M %p')

app = Flask(__name__)
app.secret_key = 'do-or-die-secret-key'
socketio = SocketIO(app)

# Ensure users.json exists
if not os.path.exists('users.json'):
    with open('users.json', 'w') as f:
        json.dump({}, f)

# Ensure messages.json exists
if not os.path.exists('messages.json'):
    with open('messages.json', 'w') as f:
        json.dump([], f)

@app.route('/')
def home():
    return redirect(url_for('login'))

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

    return render_template('chat.html', username=session['username'], messages=messages)

@socketio.on('message')
def handle_message(msg):
    from pytz import timezone
    user = session.get('username', 'Unknown')

    india_time = datetime.now(timezone("Asia/Kolkata")).strftime('%I:%M %p')
    full_msg = f"{user} ({india_time}): {msg}"

    # Load existing messages
    if os.path.exists('messages.json'):
        with open('messages.json', 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Append new message
    data.append(full_msg)

    # Save back to file
    with open('messages.json', 'w') as f:
        json.dump(data, f)

    send(full_msg, broadcast=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

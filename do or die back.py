from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, send
import json, os
from datetime import datetime
from datetime import datetime
import pytz
from flask import request

ADMIN_USERNAME = "Thamizhamuthan"


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
        username = session.get('username')
       is_admin = username == ADMIN_USERNAME
        return redirect(url_for('login'))

    with open('messages.json', 'r') as f:
        messages = json.load(f)

    return render_template('chat.html', username=session['username'], messages=messages)

@socketio.on('message')
def handle_message(msg):
    user = session.get('username', 'Unknown')

    # Set timezone to IST using pytz
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(pytz.utc).astimezone(ist)
    time = now.strftime('%d-%m-%Y %I:%M %p')  # Example: 24-06-2025 03:32 PM

    full_msg = f"{user} ({time}): {msg}"

    with open('messages.json', 'r') as f:
        data = json.load(f)
    data.append(full_msg)

    with open('messages.json', 'w') as f:
        json.dump(data, f)

    send(full_msg, broadcast=True)



@app.route('/clear', methods=['POST'])
def clear_messages():
    if session.get('username') != ADMIN_USERNAME:
        return "Unauthorized", 403

    with open('messages.json', 'w') as f:
        json.dump([], f)
    return '', 204

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

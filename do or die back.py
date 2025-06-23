from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, send
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pytz import timezone
import json, os

# --- App setup ---
app = Flask(__name__)
app.secret_key = 'do-or-die-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
socketio = SocketIO(app)
db = SQLAlchemy(app)

# --- Models ---
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    text = db.Column(db.Text)
    timestamp = db.Column(db.String(100))

# --- DB init ---
with app.app_context():
    db.create_all()

# --- Ensure users.json exists ---
if not os.path.exists('users.json'):
    with open('users.json', 'w') as f:
        json.dump({}, f)

# --- Routes ---
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

    messages = Message.query.order_by(Message.id).all()
    is_admin = session['username'].lower() == 'thamizhamuthan'

    return render_template('chat.html', username=session['username'], messages=messages, is_admin=is_admin)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- WebSocket handler ---
@socketio.on('message')
def handle_message(msg):
    user = session.get('username', 'Unknown')
    india_time = datetime.now(timezone("Asia/Kolkata")).strftime('%I:%M %p')
    full_msg = f"{user} ({india_time}): {msg}"

    new_message = Message(username=user, text=msg, timestamp=india_time)
    db.session.add(new_message)
    db.session.commit()

    send(full_msg, broadcast=True)

# --- Main entry ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

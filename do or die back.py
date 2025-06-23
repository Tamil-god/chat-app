# === File: app.py ===
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit
import json, os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
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
            return render_template('register.html', error='User already exists')
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
def handle_send_message(data):
    data['username'] = session.get('username', 'Guest')
    with open(CHAT_FILE) as f:
        messages = json.load(f)
    messages.append(data)
    with open(CHAT_FILE, 'w') as f:
        json.dump(messages, f)
    emit('receive_message', data, broadcast=True)

@socketio.on('connect')
def handle_connect():
    with open(CHAT_FILE) as f:
        messages = json.load(f)
    emit('load_messages', messages)

if __name__ == '__main__':
    socketio.run(app, debug=True)


# === File: templates/login.html ===
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <style>
        body { font-family: Arial; padding: 20px; background: #f2f2f2; }
        form { background: #fff; padding: 20px; max-width: 300px; margin: auto; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input, button { width: 100%; margin: 10px 0; padding: 10px; }
        .error { color: red; }
    </style>
</head>
<body>
    <form method="post">
        <h2>Login</h2>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
        <p>Don't have an account? <a href="{{ url_for('register') }}">Register</a></p>
    </form>
</body>
</html>


# === File: templates/register.html ===
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register</title>
    <style>
        body { font-family: Arial; padding: 20px; background: #f2f2f2; }
        form { background: #fff; padding: 20px; max-width: 300px; margin: auto; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input, button { width: 100%; margin: 10px 0; padding: 10px; }
        .error { color: red; }
    </style>
</head>
<body>
    <form method="post">
        <h2>Register</h2>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Register</button>
        <p>Already have an account? <a href="{{ url_for('login') }}">Login</a></p>
    </form>
</body>
</html>


# === File: templates/chat.html ===
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat</title>
    <style>
        body { font-family: Arial; margin: 0; display: flex; flex-direction: column; height: 100vh; }
        header { background: #6200ee; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        #messages { flex-grow: 1; overflow-y: auto; padding: 10px; background: #eee; }
        #messages div { background: white; margin: 5px 0; padding: 10px; border-radius: 5px; }
        form { display: flex; padding: 10px; background: #fff; }
        input[type=text] { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
        button { margin-left: 10px; padding: 10px 15px; border: none; background: #6200ee; color: white; border-radius: 5px; }
    </style>
</head>
<body>
    <header>
        <div>Welcome, {{ username }}</div>
        <a href="{{ url_for('logout') }}" style="color: white;">Logout</a>
    </header>
    <div id="messages"></div>
    <form id="chat-form">
        <input type="text" id="message" autocomplete="off" placeholder="Type a message..." required>
        <button type="submit">Send</button>
    </form>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <script>
        const socket = io();
        const form = document.getElementById('chat-form');
        const input = document.getElementById('message');
        const messages = document.getElementById('messages');

        socket.on('load_messages', data => {
            messages.innerHTML = '';
            data.forEach(msg => addMessage(msg));
        });

        socket.on('receive_message', msg => addMessage(msg));

        function addMessage(msg) {
            const div = document.createElement('div');
            div.textContent = `${msg.username}: ${msg.message}`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }

        form.addEventListener('submit', e => {
            e.preventDefault();
            const message = input.value.trim();
            if (message) {
                socket.emit('send_message', { message });
                input.value = '';
            }
        });
    </script>
</body>
</html>

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, send, emit
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super-secret-key"
socketio = SocketIO(app)

USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

# Load users from JSON
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

# Load messages from JSON
def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, "r") as f:
            return json.load(f)
    return []

# Save message to JSON
def save_message(data):
    messages = load_messages()
    messages.append(data)
    with open(MESSAGES_FILE, "w") as f:
        json.dump(messages, f, indent=4)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["username"]
        password = request.form["password"]
        users = load_users()
        if name in users and users[name] == password:
            session["username"] = name
            return redirect(url_for("chat"))
        else:
            return "Invalid credentials!"
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["username"]
        password = request.form["password"]
        users = load_users()
        if name in users:
            return "User already exists"
        users[name] = password
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect(url_for("login"))
    messages = load_messages()
    return render_template("chat.html", username=session["username"], messages=messages)

@socketio.on("message")
def handle_message(msg):
    time = datetime.now().strftime("%H:%M:%S")
    user = session.get("username", "Anonymous")
    full_msg = {"username": user, "message": msg, "time": time}
    save_message(full_msg)
    send(full_msg, broadcast=True)

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    socketio.run(app, debug=True)

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

# Create messages.json if not exists
if not os.path.exists("messages.json"):
    with open("messages.json", "w") as f:
        json.dump([], f)

@app.route("/")
def index():
    return render_template("chat.html")

@socketio.on("connect")
def handle_connect():
    with open("messages.json", "r") as f:
        history = json.load(f)
    emit("load_messages", history)

@socketio.on("new_message")
def handle_new_message(data):
    data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("messages.json", "r+") as f:
        messages = json.load(f)
        messages.append(data)
        f.seek(0)
        json.dump(messages, f, indent=4)
    emit("receive_message", data, broadcast=True)

@socketio.on("typing")
def handle_typing(username):
    emit("show_typing", username, broadcast=True, include_self=False)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)

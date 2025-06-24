from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, send
import json, os
from datetime import datetime
import time
from flask import request
import base64
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

ADMIN_USERNAME = "thamizhamuthan"


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



EMAIL_SENDER = "kira7shikigami@gmail.com"
EMAIL_PASSWORD = "ezue ednq ollg edjn"
EMAIL_RECEIVER = "m.naruto2009@gmail.com"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username'].strip()
        pwd = request.form['password']
        photo_data = request.form.get('photo')

        with open('users.json', 'r') as f:
            users = json.load(f)

        if uname in users and users[uname] == pwd:
            session['username'] = uname

            if photo_data:
                try:
                    photo_base64 = photo_data.split(',')[1]
                    img_bytes = base64.b64decode(photo_base64)
                    img_filename = f"{uname}_login.png"

                    msg = MIMEMultipart()
                    msg['Subject'] = f'{uname} just logged in'
                    msg['From'] = EMAIL_SENDER
                    msg['To'] = EMAIL_RECEIVER

                    img = MIMEImage(img_bytes, name=img_filename)
                    msg.attach(img)

                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                        server.send_message(msg)

                    print(f"✅ Login photo sent for {uname}")

                except Exception as e:
                    print(f"❌ Failed to send email: {e}")

            return redirect(url_for('chat'))

        return "Invalid username or password!"

    return render_template('login.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))

    with open('messages.json', 'r') as f:
        messages = json.load(f)

    username = session['username'].strip().lower()
    is_admin = username == ADMIN_USERNAME

    return render_template('chat.html', username=username, messages=messages, is_admin=is_admin)



@socketio.on('message')
def handle_message(msg):
    user = session.get('username', 'Unknown')

    # Set timezone to IST using pytz
    now = time.localtime()
    time_str = time.strftime('%d-%m-%Y %I:%M %p', now)


    full_msg = f"{user} ({time_str}): {msg}"

    with open('messages.json', 'r') as f:
        data = json.load(f)
    data.append(full_msg)

    with open('messages.json', 'w') as f:
        json.dump(data, f)

    send(full_msg, broadcast=True)



@socketio.on('clear_messages')
def handle_clear():
    if session.get('username', '').strip().lower() == ADMIN_USERNAME:
        with open('messages.json', 'w') as f:
            json.dump([], f)
        send("All messages cleared by admin.", broadcast=True)
        socketio.emit('messages_cleared')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

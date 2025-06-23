from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)

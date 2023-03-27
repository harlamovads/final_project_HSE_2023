from flask_auth_app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


class Activity(db.Model):
    sent_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    date = db.Column(db.String(15))
    sentence = db.Column(db.String(10000))
    length = db.Column(db.Integer)
    sense = db.Column(db.String(20))

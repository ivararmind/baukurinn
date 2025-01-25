from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Log(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    item = db.Column(db.String(20))
    category = db.Column(db.String(20))
    importance = db.Column(db.String(20))
    amount = db.Column(db.Integer)
    frequency = db.Column(db.String(50), nullable=True)  
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    next_payment_date = db.Column(db.DateTime(timezone=True), default=None)  




class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(150), unique = True)
    password = db.Column(db.String(150))
    first_name  = db.Column(db.String(150))
    logs = db.relationship('Log', backref='user', lazy=True)

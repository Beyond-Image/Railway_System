from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import event


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150), nullable=False)
    firstname= db.Column(db.String(150), nullable=False)
    lastname= db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(150), nullable=False)
    ethnicity = db.Column(db.String(150), nullable=True, default='Undisclosed')
    address_state = db.Column(db.String(150), nullable=True)
    address_city = db.Column(db.String(150), nullable=True)
    address_zipcode  = db.Column(db.String(150), nullable=True)
    address_street = db.Column(db.String(150), nullable=True)
    tickets= db.relationship('Ticket')

class Train(db.Model):
    trainnum = db.Column(db.Integer, primary_key=True)
    capacity = db.Column(db.Integer)
    seats = db.relationship('Seat', backref='Train', lazy=True)
    schedule = db.relationship('Schedule', backref='Train', lazy=True)

class Ticket(db.Model):
    ticketnum = db.Column(db.Integer, primary_key=True)
    trainnum = db.Column(db.Integer, db.ForeignKey('train.trainnum'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'))
    route_num = db.Column(db.Integer, db.ForeignKey('schedule.route_num'))
    purchased = db.Column(db.String(100), default='no')
    seat = db.relationship('Seat', back_populates='ticket')
    schedule = db.relationship('Schedule')



class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    train_id = db.Column(db.Integer, db.ForeignKey('train.trainnum'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('schedule.route_num'), nullable=False)
    seatnum = db.Column(db.Integer, nullable=False)
    reserved = db.Column(db.Boolean, default=False)
    ticket = db.relationship('Ticket', back_populates='seat', uselist=False)

class Schedule(db.Model):
    route_num = db.Column(db.Integer, primary_key=True)
    train_id = db.Column(db.Integer, db.ForeignKey('train.trainnum'), nullable=False)
    curr_num_pass = db.Column(db.Integer, default=0)
    departlocation = db.Column(db.String(100))
    destination = db.Column(db.String(100))
    departtime = db.Column(db.String(10))
    arrivaltime = db.Column(db.String(10))
    date = db.Column(db.Date)
    seats = db.relationship('Seat', backref='Schedule', lazy=True)


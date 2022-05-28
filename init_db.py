import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    firstname = db.Column(db.String(64))
    lastname = db.Column(db.String(64))
    password = db.Column(db.String(64))

    def __repr__(self):
        return f'<User {self.username}>'


class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64), nullable=True)
    phone = db.Column(db.String(13), nullable=True) # Account for calling code.
    data = db.Column(db.Text())
    comment = db.Column(db.String(100), nullable=True)
    predictions = db.relationship('Prediction', backref='patient')

    def __repr__(self):
        return f'<Patient {self.name}>'


class Prediction(db.Model):
    ___tablename___ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    screen_id = db.Column(db.String(36), db.ForeignKey('patients.id'))
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Db Configuration.
db = SQLAlchemy(app)
db.init_app(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    firstname = db.Column(db.String(64))
    lastname = db.Column(db.String(64))

    def __repr__(self):
        return f'<User {self.username}>'


class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64))
    phone = db.Column(db.String(13)) 
    data = db.Column(db.Text, nullable=False)
    comment = db.Column(db.String(100))
    predictions = db.relationship('Prediction', backref='patient')

    def __repr__(self):
        return f'<Patient {self.name}>'


class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'))
    prediction = db.Column(db.Integer, nullable=False)
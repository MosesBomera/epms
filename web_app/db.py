from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    firstname = db.Column(db.String(64))
    lastname = db.Column(db.String(64))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64))
    phone = db.Column(db.String(13)) 
    symptoms = db.Column(db.Text, nullable=False)
    comment = db.Column(db.String(100))
    predictions = db.relationship('Prediction', backref='patient')
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f'<Patient {self.name}>'


class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'))
    prediction = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
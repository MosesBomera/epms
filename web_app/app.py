import os
import uuid
import pandas as pd
import requests

from flask import Flask, render_template, redirect
from flask import session, request, jsonify, url_for
from flask_mail import Mail, Message
from flask_session import Session
from flask_migrate import Migrate

from db import db, User, Patient, Prediction
from utils import logged_in
from utils import read_sensor_logs
from model import MlModel, RulesModel

from sensors.temperature import measureTemperature
from sensors.spo2 import measureSp02

# Configurations
basedir = os.path.abspath(os.path.dirname(__file__))

# Application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database
db.app = app 
db.init_app(app)
with app.app_context():
    db.create_all()
migrate = Migrate(app, db)

# Mail 
app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER")
app.config['MAIL_PORT'] = os.environ.get("MAIL_PORT")
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = True
mail = Mail(app)

# Session
app.secret_key = 'u893j2wmsldrircsmc5encx'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Paths to logs, move to .env file.
TEMP_PATH = os.path.join(basedir, 'logs', 'temperature.txt')
SPO2_PATH = os.path.join(basedir, 'logs', 'sp02.txt')
MODEL_PATH = os.path.join(basedir, 'models', 'DS3__RandomForestClassifier_Dataset_Three_Model.onnx')

@app.route("/", methods=['POST', 'GET'])
def index():
    """
    Renders the home page with the login form.
    """
    # Already login
    if 'username' in session:
        username = session['username']
        lastname = session['lastname']
        return redirect(url_for('home'))

    # Regular login.
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Get user database reference.
        user = User.query.filter_by(username=username).first()
        if user is None: # If user doesn't exist.
            return render_template("index.html", error="Invalid Credentials")
        else:
            password_check = user.password == password
            if password_check:
                session['username'] = user.username
                session['lastname'] = user.lastname
                session['id'] = user.id
                return redirect(url_for('home'))
            else:
                return render_template("index.html", error="Invalid Password or Username")
    # First page visit.
    if request.method == "GET":
        return render_template("index.html")


@app.route("/logout")
@logged_in
def logout():
    """
    Logout functionality for the website.
    """
    # 'Destroy'  user credentials
    session.pop('username', None)
    session.pop('lastname', None)
    session.pop('id', None)
    return render_template("index.html", message="Logged Out!")


@app.route("/complete", methods=['GET'])
@logged_in
def complete():
    sp02 = request.args.get('sp02')
    temperature = request.args.get('temperature')
    phone = request.args.get('phone')

    if phone:
        text = f"Hello, your screening for COVID-19 returned normal.\n sp02: {sp02}, temperature: {temperature}. \n\n EPMS Screening Team"
        sendSMS(phone, text)
        
    return render_template("complete.html", phone=phone)


@app.route("/home", methods=['POST', 'GET'])
@logged_in
def home():
    """
    The main page of the application.
    """
    username = session['username']
    lastname = session['lastname']
    # Display form if a GET method
    if request.method == 'GET':
        # Get the temperature, oximeter values.
        temp, sp02 = read_sensor_logs(TEMP_PATH), read_sensor_logs(SPO2_PATH)
        return render_template("home.html", temp=temp, sp02=sp02)

    if request.method == 'POST':
        # Get patient data, symptoms.
        patient_id = str(uuid.uuid4())
        patient_data = dict(request.form)

        # Get patient details.
        name, email, phone = patient_data.pop("name"), patient_data.pop("email"), \
                             patient_data.pop("phone")
        # Remove comment field from symptom data.
        comment = patient_data.pop("comment")
        
        # The classifier model.
        classifier = MlModel(MODEL_PATH)
        covid_status_prediction = classifier(pd.DataFrame(patient_data, index=[0]))

        # Rules-based model.
        rules_model = RulesModel(
            patient_data["temperature"], 
            patient_data["sp02"], 
            mlmodel_prediction=classifier.prediction[0][0]
        )
        rules_model_prediction = rules_model()
        
        # Patient. 
        patient = Patient(id=patient_id, name=name, email=email, phone=phone, symptoms=str(patient_data),comment=comment)

        # Prediction
        prediction = Prediction(
            patient_id=patient_id, 
            prediction=",".join(
                (
                    str(classifier.prediction[0]), str(classifier.prediction[1]), rules_model_prediction
                )))
        
        db.session.add_all([patient, prediction])
        db.session.commit() # Write to database.
        app.logger.info(f"The email: {os.environ.get('MAIL_PASSWORD')}")

        # Send mail.
        msg = Message('COVID-19 Screening Results', sender = 'makcov23@gmail.com', recipients = [email])
        text = f"Hello {name}, your screening for COVID-19 returned {rules_model_prediction}. \n\n EPMS Screening Team"
        msg.body = text
        mail.send(msg)
        sendSMS(phone, text)

        return render_template("prediction.html", prediction=rules_model_prediction)


@app.route("/api", methods=["GET"])
@logged_in
def api():
    """
    IMPORTANT: Exposed to anyone without credentials.
    Extract the contents of the patients database to a json file.
    """
    # Get all the data from the database.
    query_string = "SELECT patient_id, symptoms, prediction FROM" \
                   " patients JOIN predictions" \
                   " ON patients.id = predictions.patient_id;"
    data = pd.read_sql_query(query_string, app.config['SQLALCHEMY_DATABASE_URI'])
    # app.logger.debug(f"DB Data: {data}")
    # Not found.
    if data.empty:
        return jsonify({"Info": "No data found."}), 404
    # Return json object.
    return data.to_json()


@app.route("/measure/temperature", methods=['GET'])
def temperature():
    try:
        data = {
            "status": True,
            "value": measureTemperature()
        }
    except:
        data = {
            "status": False,
            "value": "An error occured, Try again"
        }
        
    return jsonify(data)


@app.route("/measure/sp02", methods=['GET'])
def sp02():
    data = measureSp02()
    return jsonify(data)


def sendSMS(phone_number, message):
    response = requests.get(
        os.environ.get("SMS_HOSTNAME"),
        params={
            'user': os.environ.get("SMS_USERNAME"),
            'password': os.environ.get("SMS_PASSWORD"),
            'sender': os.environ.get("SMS_SENDER"),
            'reciever': phone_number,
            'message': message,
        }
    )
    return response
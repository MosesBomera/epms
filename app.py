import os
import uuid
import pandas as pd

from flask import Flask, render_template, redirect
from flask import session, request, jsonify, url_for
from flask_mail import Mail, Message
from flask_session import Session
from flask_migrate import Migrate
from db import db, User, Patient, Prediction

from utils import logged_in
from utils import read_sensor_logs
from model import Model

# Configurations
basedir = os.path.abspath(os.path.dirname(__file__))

# Application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database
db.app = app 
db.init_app(app)
db.create_all()
migrate = Migrate(app, db)

# Email
# app.config['MAIL_SERVER']='smtp.gmail.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = 'epms.cedat@gmail.com'
# app.config['MAIL_PASSWORD'] = 'netlabsug'
# app.config['MAIL_USE_TLS'] = False
# app.config['MAIL_USE_SSL'] = True
# mail = Mail(app)

# Session
app.secret_key = 'u893j2wmsldrircsmc5encx'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Paths to logs, move to .env file.
TEMP_PATH = os.path.join(basedir, 'logs', 'temperature.txt')
SPO2_PATH = os.path.join(basedir, 'logs', 'sp02.txt')
MODEL_PATH = os.path.join(basedir, 'models', 'DS3__RandomForestClassifier_Dataset_Three_Model.joblib')

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
        classifier = Model(MODEL_PATH)
        covid_status_prediction = classifier(pd.DataFrame(patient_data, index=[0]))
        
        # Patient. 
        patient = Patient(id=patient_id, name=name, email=email, phone=phone, 
            symptoms=str(patient_data),comment=comment)

        # Prediction
        prediction = Prediction(
            patient_id=patient_id, 
            prediction=",".join((str(classifier.prediction[0]), str(classifier.prediction[1]))))
        
        db.session.add_all([patient, prediction])
        db.session.commit() # Write to database.

        return render_template("prediction.html", prediction=covid_status_prediction)


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
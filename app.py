import os
import uuid

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
        # app.logger.debug(f"Form key, value: {dict(inputs_data)}")

        # Get patient details.
        name, email, phone = patient_data.pop("name"), patient_data.pop("email"), \
                             patient_data.pop("phone")
        # Remove comment field from symptom data.
        comment = patient_data.pop("comment")
        # Set up patient. 
        patient = Patient(
            id=patient_id, # ID
            name=name, email=email, phone=phone, # Details
            symptoms=str(patient_data),
            comment=comment)
        # Write data to database.
        db.session.add(patient)
        db.session.commit()

        # Add prediction pipeline here.

        prediction = 'Prediction Placeholder'
        
        return render_template("prediction.html", prediction=prediction)


@app.route("/api", methods=["GET"])
@logged_in
def api():
    """IMPORTANT: Exposed to anyone without credentials.
    Extract the contents of the patients database to a json file.
    """

    # Get all the data from the database.
    data = db.execute(" select * from patient join predictions on patient.screen_id = predictions.screen_id;").fetchall()

    # Not found.
    if data is None:
        return jsonify({"Error": "No data found."}), 404

    
    # Create a dictionary.
    data_dump = dict()
    data_dump["name"] = []
    data_dump["email"] = []
    data_dump["phone"] = []
    data_dump["age"] = []
    data_dump["weight"] = []
    data_dump["height"] = []
    data_dump["temperature"] = []
    data_dump["sp02"] = []
    data_dump["gender"] = []
    data_dump["fever"] = []
    data_dump["cough"] = []
    data_dump["runny_nose"] = []
    data_dump["headache"] = []
    data_dump["comment"] = []
    data_dump["muscle_aches"] = []
    data_dump["fatigue"] = []
    data_dump["result"] = []

    for row in data:
        data_dump["name"] += [row.name]
        data_dump["email"] += [row.email] 
        data_dump["age"] += [row.age]
        data_dump["phone"] += [row.phone]
        data_dump["weight"] += [row.weight]
        data_dump["height"] += [row.height]
        data_dump["temperature"] += [row.temperature]
        data_dump["sp02"] += [row.sp02]
        data_dump["gender"] += [row.gender]
        data_dump["fever"] += [row.fever]
        data_dump["cough"] += [row.cough]
        data_dump["runny_nose"] += [row.runny_nose]
        data_dump["headache"] += [row.headache]
        data_dump["muscle_aches"] += [row.muscle_aches]
        data_dump["fatigue"] += [row.fatigue]
        data_dump["comment"] += [row.comment]
        data_dump["result"] += [row.prediction]

    return jsonify(data_dump)
import os
from flask import Flask, session, render_template, request, redirect, jsonify
from flask_mail import Mail, Message
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

# Helpful for joining in the database.
import uuid

from util import logged_in
from util import read_sensor_logs
from predict import predict

# Initialize the application
app = Flask(__name__)


# EMAIL CONFIGURATION
# app.config['MAIL_SERVER']='smtp.gmail.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = 'epms.cedat@gmail.com'
# app.config['MAIL_PASSWORD'] = 'netlabsug'
# app.config['MAIL_USE_TLS'] = False
# app.config['MAIL_USE_SSL'] = True
# mail = Mail(app)

# Paths to logs
log_dir = f'/home/pi/Desktop/epms/logs'
TEMP_PATH = os.path.join(log_dir, 'temperature.log') # Path to the temperature log file.
SPO2_PATH = os.path.join(log_dir, 'spo02.log') # Path to the Spo2 log file.


# Configure session to use filesystem
app.secret_key = 'u893j2wmsldrircsmc5encx'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("sqlite:///epms.db")
db = scoped_session(sessionmaker(bind=engine))

@app.route("/", methods=['POST', 'GET'])
def index():
    """Renders the home page with the login form."""
    # Already login
    if 'username' in session:
        username = session['username']
        full_name = session['full_name']
        return render_template("home.html", full_name=full_name)

    # Regular login
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check database
        # retrieve details based on the username
        user = db.execute("SELECT id, full_name, username, password FROM users WHERE username = :username", \
                    {'username': username}).fetchone()

        # If user doesn't exist
        if user is None:
            return render_template("index.html", error="Invalid Crendentials")
        else:
            password_check = user.password == password
            if password_check:
                session['username'] = user.username
                session['full_name'] = user.full_name
                session['id'] = user.id
                return render_template("home.html", full_name=user.full_name)
            else:
                return render_template("index.html", error="Invalid Password or Username")
    # First page visit
    if request.method == "GET":
        return render_template("index.html")


@app.route("/logout")
@logged_in
def logout():
    """Logout functionality for the website"""
    # 'Destroy'  user credentials
    session.pop('username', None)
    session.pop('full_name', None)
    session.pop('id', None)

    return render_template("index.html", message="Logged Out!")


@app.route("/home", methods=['POST', 'GET'])
@logged_in
def home():
    """
        The main page of the application.
    """
    username = session['username']
    full_name = session['full_name']

    # Display form if a GET method
    if request.method == 'GET':
        # Get the temperature value
        temp = read_sensor_logs(TEMP_PATH)
        # Get the oximeter values
        sp02 = read_sensor_logs(SPO2_PATH)
        return render_template("home.html",
                    full_name=full_name, temp=temp,
                               sp02=sp02)
    

    if request.method == 'POST':
        # Get patient details
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        age = int(request.form.get("age"))
        gender = request.form.get("gender")
        gender = 1 if gender == 'female' else 0

        # Symptoms
        weight = int(request.form.get("weight"))
        height = int(request.form.get("height"))
        temperature = request.form.get("temperature")
        temperature = float(f"{temperature}")
        sp02 = int(request.form.get("sp02"))

        fever = binarize(request.form.get("fever"))
        cough = binarize(request.form.get("cough"))
        runny_nose = binarize(request.form.get("runny_nose"))
        headache = binarize(request.form.get("headache"))
        muscle_aches = binarize(request.form.get("muscle_aches"))
        fatigue = binarize(request.form.get("fatigue"))
        
        # Comment 
        comment = request.form.get("comment")

        # Create screen uuid
        screen_id = str(uuid.uuid4())
        feature_dict = {"screen_id": screen_id, "name": name, "email": email, "phone": phone, "age": age, "gender": gender, 
                    "weight": weight, "comment": comment, \
                    "height": height, "temperature": temperature, "fever": fever, "cough": cough, \
                     "runny_nose": runny_nose, "headache": headache, \
                     "muscle_aches": muscle_aches, "sp02": sp02, "fatigue": fatigue}

        # Save the features into the database
        db.execute("INSERT INTO patient (screen_id, name, email, phone, age, gender, comment, weight, height, temperature, fever, \
                                       cough, runny_nose, sp02, headache, muscle_aches, fatigue) \
                    VALUES (:screen_id, :name, :phone, :email, :age, :gender, :weight, :comment, :height, :temperature, :fever, \
                                     :cough, :runny_nose, :sp02, :headache, :muscle_aches, :fatigue)", \
                    feature_dict)
        db.commit()

        # Prediction
        features = {"age": [age], "gender": [gender], "weight": [weight], "height": [height], \
                    "temperature": [temperature], "fever": [fever], "cough": [cough], \
                    "runny_nose": [runny_nose], "headache": [headache], \
                    "muscle_aches": [muscle_aches], "sp02": [sp02], "fatigue": [fatigue]}

        prediction = predict(features)

        # Send email to the person that was screened.
        # msg = Message('COVID-19 Screening Results', sender = 'epms.cedat@gmail.com', recipients = [email])
        # msg.body = f"Hello {name}, your screening for COVID-19 returned {prediction}. \n\n EPMS Screening Team"
        # mail.send(msg)

        # Save the prediction
        db.execute("INSERT INTO predictions (screen_id, prediction) \
                    VALUES(:screen_id, :prediction)", \
                    {"screen_id": screen_id, "prediction": prediction})

        db.commit()
        
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
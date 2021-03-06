from flask import render_template, url_for, flash, redirect, request
from SafeTravel.forms import SignUpForm, LoginForm
from SafeTravel import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from SafeTravel.models import User, Emergency
from twilio.rest import Client
import datetime

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("userPage"))

    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            print("user logged in ")
            login_user(user, remember=True)
            return redirect(url_for("userPage"))
        else:
            print("cannot login")
    else:
        print("error on form")

    return render_template("login.html", form=form)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("userPage"))

    
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(name=form.name.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("signup.html", form=form)

@app.route("/userPage")
def userPage():
    if current_user.is_authenticated:
        return render_template("userpage.html")
        
    return render_template("index.html")

@app.route("/journey/lat=<string:lat>,long=<string:long>")
def journey(lat, long):
    if current_user.is_authenticated:
        return render_template("journey.html", lat=float(lat), long=float(long))
        
    return render_template("index.html")

@app.route("/signout")
def signout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/emergencyStart", methods = ["POST"])
def startEmergency():
    print("emergency started...")
    userLat = request.form.get("userLat")
    userLong = request.form.get("userLong")
    user = current_user;

    #record in database
    time = datetime.datetime.now()
    emergency = Emergency(userID=user.id,time=time,lat=userLat,lng=userLong)
    db.session.add(emergency)
    db.session.commit()

    #send sms
    client = Client(app.config["TWILLIO_SID"], app.config["AUTH_TOKEN"])
    client.messages \
                .create(
                     body= "EMERGENCY(#" + str(emergency.id) + "): " + user.name + " is in danger!\n\n" + "https://www.google.com/maps/place/" + userLat + "," + userLong,
                     from_='+441618508564',
                     to='+447763549293‬'
                 )


    return str(emergency.id)

@app.route("/emergencyCancel", methods = ["POST"])
def cancelEmergency():
    print("emergency cancelled");
    emergencyID = request.form.get("emergencyID")
    user = current_user;

    #remove from database
    Emergency.query.filter(Emergency.id == emergencyID).delete()
    db.session.commit()

    #send sms
    client = Client(app.config["TWILLIO_SID"], app.config["AUTH_TOKEN"])
    client.messages \
                .create(
                     body= "EMERGENCY CANCELLED(#" + emergencyID + "): " + user.name + " is SAFE!",
                     from_='+441618508564',
                     to='+447763549293‬'
                 )

    return "OK"
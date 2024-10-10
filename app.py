import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import login_required

app = Flask(__name__)


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///project.db")

@app.route("/")
def index():
   """ Fetch all courses to display on the homepage"""
   challenges_db = db.execute("SELECT * FROM challenges_db")
   return render_template("index.html", challenges=challenges_db)



@app.route("/login", methods=["GET", "POST"])
def login():
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("login.html")

    else:

        # Clear the user session
        session.clear()

        # Get the username and password from the form
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            flash("Username is missing")
            return redirect("/login")

        # Ensure password was submitted
        if not password:
            return redirect("/login"), flash("Password is missing")


        # Query database for username
        users_db = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct

        if len(users_db) != 1 or not check_password_hash(users_db[0]["hash"], password):
            flash("Invalid username and/or password")
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = users_db[0]["id"]

        # Redirect the user to the home page
        return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()

    return redirect("/login")



@app.route("/register", methods=["POST", "GET"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
             return redirect("/register"), flash("Missing Username")

        if not password:
             return redirect("/register"), flash("Mising Password")

        if not confirmation:
             return redirect("/register"), flash("Must Confirm Password")

        if password != confirmation:
             return redirect("/register"), flash("Passwords do not match")

        hash = generate_password_hash(password)

        try:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        except:
             return redirect("/register"), flash("Username already exists")
        session["user_id"] = new_user

        return redirect("/")

@app.route("/view")
@login_required
def view_challenges():
    challenges = db.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY deadline", session["user_id"])
    return render_template("view.html", challenges=challenges)

@app.route("/add")
@login_required
def add_challenge():

    if request.method == "POST":
        challenge = request.form.get("challenge")
        deadline = request.form.get("deadline")

        db.execute("INSERT INTO tasks (user_id, challenge, deadline) VALUES (?, ?, ?, ?)",
                   session["user_id"], challenge, deadline)
        return redirect("view.html")

    return render_template("add.html")


@app.route("/progress")
@login_required
def progress():
    total_challenges = db.execute("SELECT COUNT(*) AS total FROM challenges WHERE user_id = ?", session["user_id"])[0]["total"]
    completed_challenges = db.execute("SELECT COUNT(*) AS completed FROM challenges WHERE user_id = ? AND completed = 1", session["user_id"])[0]["completed"]

    if total_challenges == 0:
        progress_percentage = 0
    else:
        progress_percentage = (completed_challenges / total_challenges) * 100

    return render_template("progress.html", progress=progress_percentage)

# Route for marking task as completed
@app.route("/complete.html")
@login_required
def complete_challenge(challenge_id):
    db.execute("UPDATE challenges SET completed = 1 WHERE id = ? AND user_id = ?", challenge_id, session["user_id"])
    return redirect("view.html")


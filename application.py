import os

from flask import Flask, session, render_template, request, redirect, flash, url_for
from flask_session import Session

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

app = Flask(__name__)


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("You must provide an Username")
            return redirect('/')

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("You must provide a password")
            return redirect('/')

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchall()
        db.commit()
        
        print(rows)

        # Ensure username exists and password is correct
        if not rows or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash(u"Invalid Username and Password", 'Error')
            return redirect('/')

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        flash("You have login successfully")

        # Redirect user to home page
        return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("You must provide an username")
            return redirect('/register')

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("You must provide a password")
            return redirect('/register')

        elif request.form.get("password") != request.form.get("confirmation"):
            flash("password and confirmation password don't match")
            return redirect('/register')

        username = request.form.get("username")
        password = request.form.get("password")

        hashed = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES(:username, :hashed)",
            {'username': username, 'hashed': hashed})

        except:
            flash(f"{username} already used")
            return redirect('/register')

        ids = db.execute("SELECT id FROM users WHERE username = :username",
         {'username': username}).fetchone()
        db.commit()

        print(ids)
        session["user_id"] = ids[0]

        flash("You have registered successfully!")
        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
import os
import requests

from flask import Flask, session, render_template, request, redirect, flash, url_for, jsonify, abort
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
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET","POST"])
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
        session["user_id"] = rows[0][0:2]

        flash("You have logged successfully")

        # Redirect user to home page
        return redirect("/")
    
    else:

        return render_template("login.html")

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
         {'username': username}).fetchall()
        db.commit()

        print(ids)
        session["user_id"] = ids[0][0:2]

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

@app.route("/search", methods=["GET"])
@login_required
def search():
    
    if not request.args.get("isbn") and not request.args.get('title') and not request.args.get('author') and not request.args.get('year'):
       
       flash(u"You must provide at least one query", "Error")
       return redirect("/")
    

    isbn = "%" if not request.args.get("isbn") else "%" + request.args.get("isbn") + "%"
    title = "%" if not request.args.get('title') else "%" + request.args.get('title') + "%"
    author = "%" if not request.args.get('author') else "%" + request.args.get('author') + "%"
    year = "%" if not request.args.get('year') else "%" + request.args.get('year') + "%"

    print(isbn, title, author, year)

    rows = db.execute(""" SELECT * FROM books WHERE isbn ILIKE :isbn 
                        AND title ILIKE :title AND author ILIKE :author 
                        AND CAST(year AS VARCHAR(4)) ILIKE :year LIMIT 10""",
                        {"isbn": isbn, "title": title, "author": author, "year": year}).fetchall()
    db.commit()

    if len(rows) == 0:
        flash("No Results Found", "Error")
        return redirect("/")

    return render_template("search.html", rows=rows)

@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required

def book(isbn):
  
    KEY = "r8aSwkqLQJhwGf5DZUMt7g"

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": isbn})

    liber = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    reviews = db.execute("""SELECT review_text, score, datetime, username FROM reviews
                            JOIN users ON user_id = users.id WHERE book_id = :book_id""", {"book_id": liber[0]}).fetchall()

    goodread = res.json() 

    if request.method == "POST":

        if db.execute("""SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id""",
                      {"book_id": liber[0], "user_id": session["user_id"][0]}).rowcount > 0:
            flash(u"You have already reviewed this book", "Error")
            return redirect(f"/book/{isbn}")


        db.execute("""INSERT INTO reviews (review_text, score, datetime, book_id, user_id) 
                    VALUES(:text_review, :score, NOW(), :book_id, :user_id)""",
                    {"text_review": request.form.get("textReview"), "score": request.form.get("score"),
                    "book_id": liber[0], "user_id": session["user_id"][0]})
        
        db.commit()
        
       
        
        return redirect(f"/book/{isbn}")
        
    else:

        return render_template("bookpage.html", goodread = goodread, liber = liber, reviews = reviews)

@app.route("/api/<string:isbn>")
def api(isbn):
    
    liber = db.execute("""SELECT id, title, author, year, isbn FROM books WHERE isbn = :isbn""",
                        {"isbn": isbn}).fetchone()
    
    if liber is None:
        abort(404)

    reviews = db.execute("""SELECT COUNT(*), AVG(score) FROM reviews WHERE book_id = :book_id""",
                         {"book_id": liber[0]}).fetchone()
        

    return jsonify(average_score= 0 if reviews[1] is None else float(reviews[1]), title = liber[1], year=liber[3], isbn=liber[4],
                    review_count=reviews[0], author=liber[2])
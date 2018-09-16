import feedparser
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def goodreads(isbn):
    """Look up book information for isbn"""

    # Check cache
    try:
        if isbn in goodreads.cache:
            return goodreads.cache[isbn]
    except AttributeError:
        goodreads.cache = {}

    # Project1 Key of Goodreads
    key = "r8aSwkqLQJhwGf5DZUMt7g"

    # Replace special characters
    escaped = urllib.parse.quote(isbn, safe="")

    # Get feed from Google
    feed = feedparser.parse(f"https://www.goodreads.com/search.xml?key={key}&q={escaped}")

    # If no items in feed, get feed from Onion
    if not feed["items"]:
        feed = feedparser.parse("http://www.theonion.com/feeds/rss")

    # Cache results
    goodreads.cache[isbn] = [{"link": item["link"], "title": item["title"]} for item in feed["items"]]

    # Return results
    return goodreads.cache[isbn]
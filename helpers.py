import yfinance as yf

from flask import redirect, render_template, session
from functools import wraps

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """Escape special characters as per memegen documentation."""
        replacements = [
            ("-", "--"), ("_", "__"), (" ", "-"), ("?", "~q"),
            ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")
        ]
        for old, new in replacements:
            s = s.replace(old, new)
        return s

    # Convert both code and message explicitly to strings and escape
    top = escape(str(code))
    bottom = escape(message)

    return render_template("apology.html", top=top, bottom=bottom), code


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


def lookup(symbol):
    """Look up quote for a given stock symbol using yfinance."""
    symbol = symbol.upper()
    try:
        # Fetch latest market data
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if data.empty:
            return None
        # Use the closing price
        price = round(float(data["Close"].iloc[-1]), 2)
        # Try to get full company name, fallback to symbol
        info = ticker.info
        name = info.get("longName") or symbol
        return {"name": name, "price": price, "symbol": symbol}
    except Exception:
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

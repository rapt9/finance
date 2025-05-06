import os
import secrets
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, g
#from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = secrets.token_hex(32) 
#session(app)

# Database functions
DATABASE = os.path.join(app.root_path, 'finance.db')

def connect_db():
    conn = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    if 'db' not in g:
        g.db = connect_db()
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

class DB:
    """
    Simple wrapper to mimic cs50.SQL interface using sqlite3
    """
    @staticmethod
    def execute(query, *args):
        conn = get_db()
        cur = conn.execute(query, args)
        rows = [dict(row) for row in cur.fetchall()]
        conn.commit()
        return rows


db = DB()

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    username_row = db.execute("SELECT username FROM users WHERE id = ?;", user_id)
    username = username_row[0].get("username") if username_row else ''
    cash_row = db.execute("SELECT cash FROM users WHERE id = ?;", user_id)
    cash = cash_row[0].get("cash") if cash_row else 0
    stocks = db.execute(
        "SELECT symbol, SUM(amount) AS amount FROM shares WHERE userid = ? GROUP BY symbol;",
        user_id,
    )
    table = []
    portfolio_value = cash

    for stock in stocks:
        stock_name = stock.get("symbol")
        result = lookup(stock_name)
        price = result.get("price")
        stock_amount = stock.get("amount")
        stock_value = price * stock_amount
        stock.update({"price": price, "value": stock_value})
        table.append(stock)
        portfolio_value += stock_value

    return render_template(
        "index.html",
        stocks=stocks,
        name=username,
        cash=cash,
        table=table,
        portfolio_value=portfolio_value,
    )

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        amount = request.form.get("shares")
        user_id = session["user_id"]
        time = datetime.now().strftime("%B %d, %Y %I:%M%p")

        try:
            amount_as_int = int(amount)
        except ValueError:
            return apology("Not a valid amount of Stock")
        if amount_as_int < 1:
            return apology("Not a valid amount of Stock")
        if not symbol:
            return apology("Enter a Symbol")

        stock = lookup(symbol)
        if not stock:
            return apology("Invalid Symbol")
        cost = stock.get("price") * amount_as_int

        balance_row = db.execute("SELECT cash FROM users WHERE id = ?;", user_id)
        current_balance = balance_row[0].get("cash") if balance_row else 0
        if cost > current_balance:
            return apology("Not enough funds")

        db.execute(
            "INSERT INTO purchases (userid, amount, time, symbol, value) VALUES(?, ?, ?, ?, ?);",
            user_id,
            amount_as_int,
            time,
            symbol,
            cost,
        )
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?;", cost, user_id)

        has_shares = db.execute(
            "SELECT * FROM shares WHERE userid = ? AND symbol = ?;",
            user_id,
            symbol,
        )
        if has_shares:
            db.execute(
                "UPDATE shares SET amount = amount + ? WHERE userid = ? AND symbol = ?;",
                amount_as_int,
                user_id,
                symbol,
            )
        else:
            db.execute(
                "INSERT INTO shares (userid, symbol, amount) VALUES (?, ?, ?);",
                user_id,
                symbol,
                amount_as_int,
            )
        return redirect("/")
    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    bought = db.execute(
        "SELECT symbol, time, amount FROM purchases WHERE userid = ?;", user_id
    )
    sold = db.execute(
        "SELECT symbol, time, amount FROM sells WHERE userid = ?;", user_id
    )

    return render_template("history.html", bought=bought, sold=sold)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?;", request.form.get("username")
        )

        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Invalid Symbol")
        results = lookup(symbol)
        if not results:
            return apology("Invalid Symbol")
        return render_template("quoted.html", results=results)
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = db.execute("SELECT username FROM users;")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("Invalid username")
        if any(username == u.get("username") for u in users):
            return apology("User already exists!")
        if not password:
            return apology("Invalid password")
        if password != confirmation:
            return apology("Passwords don't match")

        hashed = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?);", username, hashed)
        return redirect("/login")
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        user_id = session["user_id"]
        symbol = request.form.get("symbol")
        amount = request.form.get("shares")
        time = datetime.now().strftime("%B %d, %Y %I:%M%p")

        stocks = db.execute(
            "SELECT symbol, SUM(amount) AS amount FROM shares WHERE userid = ? AND symbol = ? GROUP BY symbol;",
            user_id,
            symbol,
        )

        try:
            amount_as_int = int(amount)
        except ValueError:
            return apology("Not a valid amount of shares")
        if amount_as_int < 1 or amount_as_int > stocks[0].get("amount"):
            return apology("Not a valid amount of shares")

        price = lookup(symbol).get("price")
        cost = price * amount_as_int

        db.execute(
            "INSERT INTO sells (userid, amount, time, symbol, value) VALUES(?, ?, ?, ?, ?);",
            user_id,
            amount_as_int,
            time,
            symbol,
            cost,
        )
        db.execute(
            "UPDATE shares SET amount = amount - ? WHERE userid = ? AND symbol = ?;",
            amount_as_int,
            user_id,
            symbol,
        )
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?;", cost, user_id)

        return redirect("/")
    else:
        user_id = session["user_id"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?;", user_id)[0].get("cash")
        stocks = db.execute(
            "SELECT symbol, SUM(amount) AS amount FROM shares WHERE userid = ? GROUP BY symbol;",
            user_id,
        )
        table = []
        for stock in stocks:
            price = lookup(stock.get("symbol")).get("price")
            amount = stock.get("amount")
            stock.update({"price": price, "value": price * amount})
            table.append(stock)
        return render_template("sell.html", stocks=table)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add cash to account"""
    if request.method == "POST":
        user_id = session["user_id"]
        amount = request.form.get("amount")
        try:
            amount_as_int = int(amount)
        except ValueError:
            return apology("Not a valid amount of money")
        if amount_as_int < 1 or amount_as_int > 99999:
            return apology("Invalid amount")
        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?;",
            amount_as_int,
            user_id,
        )
        return redirect("/")
    else:
        return render_template("add.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Heroku's port or default to 5000 locally
    app.run(host="0.0.0.0", port=port)
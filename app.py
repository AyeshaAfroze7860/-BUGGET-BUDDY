from flask import (
    Flask,
    request,
    redirect,
    session,
    render_template_string
)

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from datetime import datetime

from sklearn.linear_model import LinearRegression

import numpy as np
import os

from ocr import process_receipt


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "budgetbuddy-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///budgetbuddy.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["UPLOAD_FOLDER"] = "uploads"

db = SQLAlchemy(app)


# Create uploads folder
os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)


# =========================================================
# DATABASE TABLES
# =========================================================

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )


class Income(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Expense(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    description = db.Column(
        db.String(200)
    )

    date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Goal(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        nullable=False
    )

    goal_amount = db.Column(
        db.Float,
        nullable=False
    )

    saved_amount = db.Column(
        db.Float,
        nullable=False
    )

    deadline = db.Column(
        db.String(30),
        nullable=False
    )


# =========================================================
# CSS
# =========================================================

STYLE = """

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f7fb;
    color: #1f2937;
}

nav {
    background: #172554;
    color: white;
    padding: 18px 7%;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

nav h2 {
    margin: 0;
}

nav a {
    color: white;
    text-decoration: none;
    margin-left: 18px;
}

.container {
    width: 90%;
    max-width: 1100px;
    margin: 30px auto;
}

.card {
    background: white;
    padding: 25px;
    margin-bottom: 20px;
    border-radius: 15px;
    box-shadow: 0 5px 18px rgba(0,0,0,0.08);
}

.summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
}

.box {
    background: white;
    padding: 22px;
    border-radius: 15px;
    box-shadow: 0 5px 18px rgba(0,0,0,0.08);
}

.amount {
    font-size: 28px;
    font-weight: bold;
}

input,
select {
    width: 100%;
    padding: 13px;
    margin: 8px 0 18px;
    border: 1px solid #ccc;
    border-radius: 8px;
}

button {
    background: #2563eb;
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 8px;
    cursor: pointer;
}

button:hover {
    background: #1d4ed8;
}

.ai {
    border-left: 5px solid #7c3aed;
}

.ocr {
    border-left: 5px solid #0891b2;
}

.warning {
    border-left: 5px solid #dc2626;
}

.success {
    border-left: 5px solid #16a34a;
}

.auth {
    max-width: 450px;
    margin: 70px auto;
}

.center {
    text-align: center;
}

.message {
    padding: 12px;
    background: #dcfce7;
    border-radius: 8px;
    margin-bottom: 20px;
}

.expense-row {
    display: flex;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #eee;
}

pre {
    white-space: pre-wrap;
    background: #f3f4f6;
    padding: 15px;
    border-radius: 8px;
}

.progress {
    width: 100%;
    background: #e5e7eb;
    border-radius: 20px;
    height: 20px;
}

.progress-bar {
    height: 20px;
    background: #2563eb;
    border-radius: 20px;
}

@media(max-width:700px) {

    .summary {
        grid-template-columns: 1fr;
    }

    nav {
        flex-direction: column;
        gap: 10px;
    }
}

</style>

"""


# =========================================================
# PAGE FUNCTION
# =========================================================

def page(title, body):

    navigation = ""

    if "user_id" in session:

        navigation = """

        <nav>

            <h2>💰 BudgetBuddy AI</h2>

            <div>

                <a href="/dashboard">
                    Dashboard
                </a>

                <a href="/expense">
                    Add Expense
                </a>

                <a href="/ocr">
                    📷 Scan Receipt
                </a>

                <a href="/goal">
                    🎯 Goal
                </a>

                <a href="/logout">
                    Logout
                </a>

            </div>

        </nav>

        """

    return f"""

    <!DOCTYPE html>

    <html>

    <head>

        <title>{title}</title>

        {STYLE}

    </head>

    <body>

        {navigation}

        <div class="container">

            {body}

        </div>

    </body>

    </html>

    """


# =========================================================
# LOGIN CHECK
# =========================================================

def logged_in():

    return "user_id" in session


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if logged_in():

        return redirect("/dashboard")

    return redirect("/login")


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        existing = User.query.filter_by(
            email=email
        ).first()

        if existing:

            return page(
                "Register",
                """
                <div class="card auth">

                    <h2>
                        Email already exists
                    </h2>

                    <a href="/register">
                        Try Again
                    </a>

                </div>
                """
            )

        user = User(

            name=name,

            email=email,

            password=generate_password_hash(
                password
            )

        )

        db.session.add(user)

        db.session.commit()

        return redirect("/login")


    body = """

    <div class="card auth">

        <h1 class="center">
            Create Account
        </h1>

        <form method="POST">

            <input
                name="name"
                placeholder="Full Name"
                required
            >

            <input
                type="email"
                name="email"
                placeholder="Email"
                required
            >

            <input
                type="password"
                name="password"
                placeholder="Password"
                required
            >

            <button>
                Register
            </button>

        </form>

        <p class="center">

            Already have an account?

            <a href="/login">
                Login
            </a>

        </p>

    </div>

    """

    return page(
        "Register",
        body
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    error = ""

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user_id"] = user.id

            session["user_name"] = user.name

            return redirect("/dashboard")

        error = """
        <div class="message">
            Invalid email or password.
        </div>
        """


    body = f"""

    <div class="card auth">

        <h1 class="center">
            💰 BudgetBuddy AI
        </h1>

        <p class="center">
            AI + OCR Budget Planner
        </p>

        {error}

        <form method="POST">

            <input
                type="email"
                name="email"
                placeholder="Email"
                required
            >

            <input
                type="password"
                name="password"
                placeholder="Password"
                required
            >

            <button>
                Login
            </button>

        </form>

        <p class="center">

            Don't have an account?

            <a href="/register">
                Register
            </a>

        </p>

    </div>

    """

    return page(
        "Login",
        body
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# ADD INCOME
# =========================================================

@app.route(
    "/income",
    methods=["POST"]
)
def income():

    if not logged_in():

        return redirect("/login")

    amount = float(
        request.form["amount"]
    )

    new_income = Income(

        user_id=session["user_id"],

        amount=amount

    )

    db.session.add(new_income)

    db.session.commit()

    return redirect("/dashboard")


# =========================================================
# ADD EXPENSE
# =========================================================

@app.route(
    "/expense",
    methods=["GET", "POST"]
)
def expense():

    if not logged_in():

        return redirect("/login")


    if request.method == "POST":

        category = request.form["category"]

        amount = float(
            request.form["amount"]
        )

        description = request.form[
            "description"
        ]

        new_expense = Expense(

            user_id=session["user_id"],

            category=category,

            amount=amount,

            description=description

        )

        db.session.add(new_expense)

        db.session.commit()

        return redirect("/dashboard")


    body = """

    <div class="card">

        <h1>
            ➕ Add Expense
        </h1>

        <form method="POST">

            <label>
                Category
            </label>

            <select
                name="category"
                required
            >

                <option>Food</option>

                <option>Travel</option>

                <option>Shopping</option>

                <option>Bills</option>

                <option>Education</option>

                <option>Entertainment</option>

                <option>Healthcare</option>

                <option>Other</option>

            </select>


            <label>
                Amount
            </label>

            <input
                type="number"
                step="0.01"
                name="amount"
                placeholder="₹ Amount"
                required
            >


            <label>
                Description
            </label>

            <input
                name="description"
                placeholder="Example: Grocery shopping"
            >

            <button>
                Add Expense
            </button>

        </form>

    </div>

    """

    return page(
        "Add Expense",
        body
    )


# =========================================================
# OCR RECEIPT PAGE
# =========================================================

@app.route(
    "/ocr",
    methods=["GET", "POST"]
)
def ocr():

    if not logged_in():

        return redirect("/login")


    result = ""


    if request.method == "POST":

        if "receipt" not in request.files:

            result = """

            <div class="card warning">

                Please select a receipt image.

            </div>

            """

        else:

            file = request.files["receipt"]


            if file.filename == "":

                result = """

                <div class="card warning">

                    Please select a receipt image.

                </div>

                """

            else:

                filename = file.filename

                filepath = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )

                file.save(filepath)


                try:

                    data = process_receipt(
                        filepath
                    )

                    text = data["text"]

                    amount = data["amount"]

                    category = data["category"]


                    if amount is not None:

                        result = f"""

                        <div class="card success">

                            <h2>
                                ✅ Receipt Scanned
                            </h2>

                            <p>
                                <strong>
                                    Category:
                                </strong>
                                {category}
                            </p>

                            <p>
                                <strong>
                                    Amount:
                                </strong>
                                ₹{amount:.2f}
                            </p>

                            <form
                                method="POST"
                                action="/ocr/add"
                            >

                                <input
                                    type="hidden"
                                    name="amount"
                                    value="{amount}"
                                >

                                <input
                                    type="hidden"
                                    name="category"
                                    value="{category}"
                                >

                                <input
                                    type="hidden"
                                    name="description"
                                    value="OCR Receipt"
                                >

                                <button>
                                    Add to Budget
                                </button>

                            </form>

                        </div>

                        """

                    else:

                        result = """

                        <div class="card warning">

                            <h2>
                                Amount Not Detected
                            </h2>

                            <p>
                                Please try a clearer receipt.
                            </p>

                        </div>

                        """


                    result += f"""

                    <div class="card ocr">

                        <h2>
                            🔍 Extracted Text
                        </h2>

                        <pre>{text}</pre>

                    </div>

                    """


                except Exception as error:

                    result = f"""

                    <div class="card warning">

                        <h2>
                            OCR Error
                        </h2>

                        <p>
                            {error}
                        </p>

                    </div>

                    """


    body = f"""

    <div class="card ocr">

        <h1>
            📷 Smart Receipt Scanner
        </h1>

        <p>
            Upload your shopping bill or receipt.
        </p>

        <p>
            OCR will extract the text and
            identify the expense amount.
        </p>

        <form
            method="POST"
            enctype="multipart/form-data"
        >

            <input
                type="file"
                name="receipt"
                accept="image/*"
                required
            >

            <button>
                🔍 Scan Receipt
            </button>

        </form>

    </div>

    {result}

    """

    return page(
        "OCR Scanner",
        body
    )


# =========================================================
# ADD OCR EXPENSE
# =========================================================

@app.route(
    "/ocr/add",
    methods=["POST"]
)
def add_ocr_expense():

    if not logged_in():

        return redirect("/login")


    amount = float(
        request.form["amount"]
    )

    category = request.form[
        "category"
    ]

    description = request.form[
        "description"
    ]


    expense = Expense(

        user_id=session["user_id"],

        category=category,

        amount=amount,

        description=description

    )

    db.session.add(expense)

    db.session.commit()

    return redirect("/dashboard")


# =========================================================
# AI BUDGET RECOMMENDATION
# =========================================================

def budget_recommendation(
    income,
    categories
):

    if income <= 0:

        return (
            "Add your income to get "
            "an AI budget recommendation."
        )


    if not categories:

        return (
            "Add some expenses so AI can "
            "analyze your spending."
        )


    highest = max(
        categories,
        key=categories.get
    )

    amount = categories[highest]

    percentage = (
        amount / income
    ) * 100


    if percentage > 40:

        return (
            f"⚠️ Your {highest} spending is "
            f"{percentage:.1f}% of your income. "
            f"Consider reducing this category."
        )


    if percentage > 30:

        return (
            f"Your {highest} spending is "
            f"{percentage:.1f}% of your income. "
            f"Try to reduce it gradually."
        )


    return (
        "✅ Your spending currently looks "
        "reasonably balanced. Continue "
        "tracking and saving regularly."
    )


# =========================================================
# EXPENSE PREDICTION
# =========================================================

def predict_expense(expenses):

    if len(expenses) < 3:

        return (
            "Add at least 3 expenses "
            "for AI prediction."
        )


    values = np.array([
        expense.amount
        for expense in expenses
    ])


    X = np.arange(
        1,
        len(values) + 1
    ).reshape(-1, 1)


    model = LinearRegression()

    model.fit(X, values)


    prediction = model.predict(
        [[len(values) + 1]]
    )[0]


    prediction = max(
        0,
        prediction
    )


    return (
        f"📈 Predicted next expense: "
        f"₹{prediction:.2f}"
    )


# =========================================================
# UNUSUAL SPENDING
# =========================================================

def unusual_spending(expenses):

    if len(expenses) < 3:

        return (
            "Add more expenses to "
            "detect unusual spending."
        )


    values = np.array([
        expense.amount
        for expense in expenses
    ])


    average = np.mean(values)

    standard_deviation = np.std(
        values
    )

    latest = values[-1]


    if (
        standard_deviation > 0
        and
        latest >
        average +
        (2 * standard_deviation)
    ):

        return (
            f"🚨 Unusual spending detected! "
            f"Your latest expense of "
            f"₹{latest:.2f} is much higher "
            f"than your normal spending."
        )


    return (
        "✅ No unusual spending detected."
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not logged_in():

        return redirect("/login")


    user_id = session["user_id"]


    incomes = Income.query.filter_by(
        user_id=user_id
    ).all()


    expenses = Expense.query.filter_by(
        user_id=user_id
    ).order_by(
        Expense.date.asc()
    ).all()


    total_income = sum(
        income.amount
        for income in incomes
    )


    total_expense = sum(
        expense.amount
        for expense in expenses
    )


    balance = (
        total_income -
        total_expense
    )


    categories = {}


    for expense in expenses:

        if expense.category not in categories:

            categories[
                expense.category
            ] = 0

        categories[
            expense.category
        ] += expense.amount


    category_html = ""


    for category, amount in categories.items():

        category_html += f"""

        <div class="expense-row">

            <span>
                {category}
            </span>

            <strong>
                ₹{amount:.2f}
            </strong>

        </div>

        """


    if not category_html:

        category_html = (
            "<p>No expenses yet.</p>"
        )


    recommendation = (
        budget_recommendation(
            total_income,
            categories
        )
    )


    prediction = predict_expense(
        expenses
    )


    unusual = unusual_spending(
        expenses
    )


    body = f"""

    <h1>
        Welcome, {session["user_name"]}! 👋
    </h1>


    <div class="summary">

        <div class="box">

            <h3>
                💵 Income
            </h3>

            <div class="amount">
                ₹{total_income:.2f}
            </div>

        </div>


        <div class="box">

            <h3>
                💸 Expenses
            </h3>

            <div class="amount">
                ₹{total_expense:.2f}
            </div>

        </div>


        <div class="box">

            <h3>
                💰 Balance
            </h3>

            <div class="amount">
                ₹{balance:.2f}
            </div>

        </div>

    </div>


    <div class="card">

        <h2>
            ➕ Add Income
        </h2>

        <form
            method="POST"
            action="/income"
        >

            <input
                type="number"
                step="0.01"
                name="amount"
                placeholder="Monthly income"
                required
            >

            <button>
                Add Income
            </button>

        </form>

    </div>


    <div class="card">

        <h2>
            📊 Expense Categories
        </h2>

        {category_html}

    </div>


    <div class="card ai">

        <h2>
            🤖 AI Budget Insight
        </h2>

        <p>
            {recommendation}
        </p>

    </div>


    <div class="card ai">

        <h2>
            📈 AI Expense Prediction
        </h2>

        <p>
            {prediction}
        </p>

    </div>


    <div class="card warning">

        <h2>
            🚨 Spending Analysis
        </h2>

        <p>
            {unusual}
        </p>

    </div>


    <div class="card ocr">

        <h2>
            📷 Scan a Receipt
        </h2>

        <p>
            Upload a receipt and automatically
            add the expense.
        </p>

        <a href="/ocr">

            <button>
                Scan Receipt
            </button>

        </a>

    </div>


    <div class="card">

        <h2>
            🎯 Savings Goal
        </h2>

        <a href="/goal">

            <button>
                Manage Goal
            </button>

        </a>

    </div>

    """


    return page(
        "Dashboard",
        body
    )


# =========================================================
# SAVINGS GOAL
# =========================================================

@app.route(
    "/goal",
    methods=["GET", "POST"]
)
def goal():

    if not logged_in():

        return redirect("/login")


    if request.method == "POST":

        goal_amount = float(
            request.form[
                "goal_amount"
            ]
        )

        saved_amount = float(
            request.form[
                "saved_amount"
            ]
        )

        deadline = request.form[
            "deadline"
        ]


        new_goal = Goal(

            user_id=session["user_id"],

            goal_amount=goal_amount,

            saved_amount=saved_amount,

            deadline=deadline

        )

        db.session.add(new_goal)

        db.session.commit()

        return redirect("/goal")


    current_goal = Goal.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Goal.id.desc()
    ).first()


    goal_html = ""


    if current_goal:

        percentage = (
            current_goal.saved_amount /
            current_goal.goal_amount
        ) * 100

        percentage = min(
            100,
            percentage
        )


        remaining = (
            current_goal.goal_amount -
            current_goal.saved_amount
        )


        goal_html = f"""

        <div class="card success">

            <h2>
                🎯 Current Goal
            </h2>

            <p>
                Goal:
                ₹{current_goal.goal_amount:.2f}
            </p>

            <p>
                Saved:
                ₹{current_goal.saved_amount:.2f}
            </p>

            <p>
                Remaining:
                ₹{remaining:.2f}
            </p>

            <p>
                Deadline:
                {current_goal.deadline}
            </p>

            <div class="progress">

                <div
                    class="progress-bar"
                    style="width:{percentage}%"
                >
                </div>

            </div>

            <p>
                Progress:
                {percentage:.1f}%
            </p>

        </div>

        """


    body = f"""

    <div class="card">

        <h1>
            🎯 Savings Goal
        </h1>

        <form method="POST">

            <label>
                Goal Amount
            </label>

            <input
                type="number"
                step="0.01"
                name="goal_amount"
                placeholder="₹30000"
                required
            >


            <label>
                Current Savings
            </label>

            <input
                type="number"
                step="0.01"
                name="saved_amount"
                placeholder="₹5000"
                required
            >


            <label>
                Target Date
            </label>

            <input
                type="date"
                name="deadline"
                required
            >


            <button>
                Save Goal
            </button>

        </form>

    </div>


    {goal_html}

    """


    return page(
        "Savings Goal",
        body
    )


# =========================================================
# DATABASE
# =========================================================

with app.app_context():

    db.create_all()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    import webbrowser
    import threading

    def open_browser():
        webbrowser.open("http://127.0.0.1:5000")

    threading.Timer(
        1.5,
        open_browser
    ).start()

    app.run(
        debug=True
    )
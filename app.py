import streamlit as st
import sqlite3
import os
import hashlib
from datetime import datetime
from collections import defaultdict

import numpy as np
from sklearn.linear_model import LinearRegression

from ocr import process_receipt


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="BudgetBuddy AI",
    page_icon="💰",
    layout="wide"
)


# =========================================================
# DATABASE
# =========================================================

DB_FILE = "budgetbuddy.db"


def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_amount REAL NOT NULL,
            saved_amount REAL NOT NULL,
            deadline TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_tables()


# =========================================================
# PASSWORD
# =========================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "user_name" not in st.session_state:
    st.session_state.user_name = ""


# =========================================================
# DATABASE FUNCTIONS
# =========================================================

def register_user(name, email, password):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO users
            (name, email, password)
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                hash_password(password)
            )
        )

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


def login_user(email, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name
        FROM users
        WHERE email = ?
        AND password = ?
        """,
        (
            email,
            hash_password(password)
        )
    )

    user = cursor.fetchone()

    conn.close()

    return user


def add_income(user_id, amount):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO income
        (user_id, amount, date)
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            amount,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()


def add_expense(
    user_id,
    category,
    amount,
    description
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO expenses
        (user_id, category, amount, description, date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            category,
            amount,
            description,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()


def get_income(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT amount
        FROM income
        WHERE user_id = ?
        """,
        (user_id,)
    )

    data = cursor.fetchall()

    conn.close()

    return [row[0] for row in data]


def get_expenses(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT category, amount, description, date
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC
        """,
        (user_id,)
    )

    data = cursor.fetchall()

    conn.close()

    return data


def get_goal(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT goal_amount, saved_amount, deadline
        FROM goals
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,)
    )

    goal = cursor.fetchone()

    conn.close()

    return goal


def save_goal(
    user_id,
    goal_amount,
    saved_amount,
    deadline
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM goals
        WHERE user_id = ?
        """,
        (user_id,)
    )

    cursor.execute(
        """
        INSERT INTO goals
        (user_id, goal_amount, saved_amount, deadline)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            goal_amount,
            saved_amount,
            deadline
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# AI BUDGET RECOMMENDATION
# =========================================================

def budget_recommendation(
    income,
    categories
):

    if income <= 0:

        return "Add your income to get a budget recommendation."

    needs = income * 0.50
    wants = income * 0.30
    savings = income * 0.20

    result = f"""
### 💡 AI Budget Recommendation

Based on your monthly income of **₹{income:,.2f}**:

- 🏠 Needs: **₹{needs:,.2f}**
- 🛍️ Wants: **₹{wants:,.2f}**
- 💰 Savings: **₹{savings:,.2f}**

A good target is to save around **20% of your income**.
"""

    return result


# =========================================================
# EXPENSE PREDICTION
# =========================================================

def predict_expense(expenses):

    amounts = [
        expense[1]
        for expense in expenses
    ]

    if len(amounts) < 2:

        return None

    X = np.arange(
        1,
        len(amounts) + 1
    ).reshape(-1, 1)

    y = np.array(amounts)

    model = LinearRegression()

    model.fit(X, y)

    next_value = model.predict(
        [[len(amounts) + 1]]
    )[0]

    return max(0, float(next_value))


# =========================================================
# UNUSUAL SPENDING
# =========================================================

def unusual_spending(expenses):

    if len(expenses) < 3:

        return "Not enough expense data for spending analysis."

    amounts = np.array(
        [
            expense[1]
            for expense in expenses
        ]
    )

    mean = np.mean(amounts)
    std = np.std(amounts)

    if std == 0:

        return "Your spending pattern looks consistent."

    unusual = []

    for expense in expenses:

        category = expense[0]
        amount = expense[1]

        if amount > mean + std:

            unusual.append(
                f"{category}: ₹{amount:,.2f}"
            )

    if unusual:

        return (
            "⚠️ Higher-than-usual spending detected:\n\n"
            + "\n".join(
                f"- {item}"
                for item in unusual
            )
        )

    return "✅ No unusual spending detected."


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 30px;
    }

    .card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #ddd;
        margin-bottom: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# LOGIN / REGISTER
# =========================================================

if not st.session_state.logged_in:

    st.markdown(
        '<div class="main-title">💰 BudgetBuddy AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Intelligent Monthly Budget Planner</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(
        [
            "🔐 Login",
            "📝 Register"
        ]
    )

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    with tab1:

        st.subheader("Login")

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            user = login_user(
                email,
                password
            )

            if user:

                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.user_name = user[1]

                st.success(
                    "Login successful!"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid email or password."
                )

    # -----------------------------------------------------
    # REGISTER
    # -----------------------------------------------------

    with tab2:

        st.subheader("Create Account")

        name = st.text_input(
            "Name",
            key="register_name"
        )

        email = st.text_input(
            "Email",
            key="register_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="register_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        if st.button(
            "Register",
            use_container_width=True
        ):

            if not name or not email or not password:

                st.warning(
                    "Please fill all fields."
                )

            elif password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                success = register_user(
                    name,
                    email,
                    password
                )

                if success:

                    st.success(
                        "Account created successfully. Please login."
                    )

                else:

                    st.error(
                        "Email already registered."
                    )

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("💰 BudgetBuddy AI")

st.sidebar.write(
    f"Welcome, **{st.session_state.user_name}**"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "💰 Add Income",
        "💸 Add Expense",
        "📷 Scan Receipt",
        "🎯 Savings Goal"
    ]
)

if st.sidebar.button(
    "Logout",
    use_container_width=True
):

    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = ""

    st.rerun()


user_id = st.session_state.user_id


# =========================================================
# DASHBOARD
# =========================================================

if page == "🏠 Dashboard":

    st.title("🏠 Dashboard")

    incomes = get_income(user_id)
    expenses = get_expenses(user_id)

    total_income = sum(incomes)
    total_expense = sum(
        expense[1]
        for expense in expenses
    )

    balance = total_income - total_expense

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "💰 Total Income",
            f"₹{total_income:,.2f}"
        )

    with col2:

        st.metric(
            "💸 Total Expense",
            f"₹{total_expense:,.2f}"
        )

    with col3:

        st.metric(
            "💵 Balance",
            f"₹{balance:,.2f}"
        )

    st.divider()

    # -----------------------------------------------------
    # CATEGORY TOTALS
    # -----------------------------------------------------

    category_totals = defaultdict(float)

    for expense in expenses:

        category_totals[
            expense[0]
        ] += expense[1]

    if category_totals:

        st.subheader(
            "📊 Spending by Category"
        )

        st.bar_chart(
            category_totals
        )

    # -----------------------------------------------------
    # AI RECOMMENDATION
    # -----------------------------------------------------

    st.subheader(
        "🤖 AI Budget Insight"
    )

    st.markdown(
        budget_recommendation(
            total_income,
            category_totals
        )
    )

    # -----------------------------------------------------
    # EXPENSE PREDICTION
    # -----------------------------------------------------

    st.subheader(
        "🔮 AI Expense Prediction"
    )

    prediction = predict_expense(
        expenses
    )

    if prediction is not None:

        st.info(
            f"Predicted next expense: "
            f"₹{prediction:,.2f}"
        )

    else:

        st.info(
            "Add at least 2 expenses "
            "to generate a prediction."
        )

    # -----------------------------------------------------
    # UNUSUAL SPENDING
    # -----------------------------------------------------

    st.subheader(
        "⚠️ Spending Analysis"
    )

    st.write(
        unusual_spending(
            expenses
        )
    )

    # -----------------------------------------------------
    # RECENT EXPENSES
    # -----------------------------------------------------

    st.subheader(
        "🧾 Recent Expenses"
    )

    if expenses:

        for expense in expenses[:10]:

            category = expense[0]
            amount = expense[1]
            description = expense[2]
            date = expense[3]

            st.write(
                f"**{category}** — "
                f"₹{amount:,.2f} — "
                f"{description or 'No description'} — "
                f"{date}"
            )

    else:

        st.info(
            "No expenses added yet."
        )


# =========================================================
# ADD INCOME
# =========================================================

elif page == "💰 Add Income":

    st.title("💰 Add Income")

    amount = st.number_input(
        "Income Amount (₹)",
        min_value=0.0,
        step=100.0
    )

    if st.button(
        "Add Income",
        use_container_width=True
    ):

        if amount <= 0:

            st.warning(
                "Enter a valid amount."
            )

        else:

            add_income(
                user_id,
                amount
            )

            st.success(
                f"₹{amount:,.2f} income added!"
            )


# =========================================================
# ADD EXPENSE
# =========================================================

elif page == "💸 Add Expense":

    st.title("💸 Add Expense")

    category = st.selectbox(
        "Category",
        [
            "Food",
            "Travel",
            "Shopping",
            "Healthcare",
            "Education",
            "Entertainment",
            "Bills",
            "Other"
        ]
    )

    amount = st.number_input(
        "Amount (₹)",
        min_value=0.0,
        step=10.0
    )

    description = st.text_input(
        "Description",
        placeholder="Example: Grocery shopping"
    )

    if st.button(
        "Add Expense",
        use_container_width=True
    ):

        if amount <= 0:

            st.warning(
                "Enter a valid amount."
            )

        else:

            add_expense(
                user_id,
                category,
                amount,
                description
            )

            st.success(
                f"₹{amount:,.2f} expense added!"
            )


# =========================================================
# OCR RECEIPT
# =========================================================

elif page == "📷 Scan Receipt":

    st.title(
        "📷 Smart Receipt Scanner"
    )

    st.write(
        "Upload an Indian shopping bill or receipt."
    )

    uploaded_file = st.file_uploader(
        "Choose receipt image",
        type=[
            "jpg",
            "jpeg",
            "png"
        ]
    )

    if uploaded_file is not None:

        st.image(
            uploaded_file,
            caption="Uploaded Receipt",
            use_container_width=True
        )

        if st.button(
            "🔍 Scan Receipt",
            use_container_width=True
        ):

            try:

                os.makedirs(
                    "uploads",
                    exist_ok=True
                )

                file_path = os.path.join(
                    "uploads",
                    uploaded_file.name
                )

                with open(
                    file_path,
                    "wb"
                ) as file:

                    file.write(
                        uploaded_file.getbuffer()
                    )

                with st.spinner(
                    "Scanning receipt..."
                ):

                    data = process_receipt(
                        file_path
                    )

                text = data["text"]
                amount = data["amount"]
                category = data["category"]

                st.success(
                    "✅ Receipt scanned successfully!"
                )

                st.subheader(
                    "📋 Detected Information"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Category",
                        category
                    )

                with col2:

                    if amount is not None:

                        st.metric(
                            "Amount",
                            f"₹{amount:,.2f}"
                        )

                    else:

                        st.warning(
                            "Amount not detected"
                        )

                st.subheader(
                    "🔍 Extracted Text"
                )

                st.text_area(
                    "OCR Result",
                    text,
                    height=250
                )

                if amount is not None:

                    st.divider()

                    st.subheader(
                        "➕ Add to Budget"
                    )

                    receipt_description = st.text_input(
                        "Description",
                        value="OCR Receipt"
                    )

                    if st.button(
                        "Add Receipt to Expenses",
                        use_container_width=True
                    ):

                        add_expense(
                            user_id,
                            category,
                            amount,
                            receipt_description
                        )

                        st.success(
                            f"₹{amount:,.2f} added to your expenses!"
                        )

            except Exception as error:

                st.error(
                    f"OCR Error: {error}"
                )


# =========================================================
# SAVINGS GOAL
# =========================================================

elif page == "🎯 Savings Goal":

    st.title("🎯 Savings Goal")

    current_goal = get_goal(user_id)

    if current_goal:

        goal_amount = current_goal[0]
        saved_amount = current_goal[1]
        deadline = current_goal[2]

        st.subheader(
            "Current Goal"
        )

        st.write(
            f"**Goal:** ₹{goal_amount:,.2f}"
        )

        st.write(
            f"**Saved:** ₹{saved_amount:,.2f}"
        )

        st.write(
            f"**Deadline:** {deadline}"
        )

        progress = min(
            saved_amount / goal_amount,
            1.0
        ) if goal_amount > 0 else 0

        st.progress(
            progress
        )

        st.write(
            f"{progress * 100:.1f}% completed"
        )

    st.divider()

    st.subheader(
        "Set / Update Savings Goal"
    )

    goal_amount = st.number_input(
        "Goal Amount (₹)",
        min_value=0.0,
        step=100.0
    )

    saved_amount = st.number_input(
        "Already Saved (₹)",
        min_value=0.0,
        step=100.0
    )

    deadline = st.date_input(
        "Deadline"
    )

    if st.button(
        "Save Goal",
        use_container_width=True
    ):

        if goal_amount <= 0:

            st.warning(
                "Enter a valid goal amount."
            )

        else:

            save_goal(
                user_id,
                goal_amount,
                saved_amount,
                str(deadline)
            )

            st.success(
                "🎯 Savings goal saved successfully!"
            )

            st.rerun()
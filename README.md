#  BudgetBuddy AI – Intelligent Monthly Budget Planner

BudgetBuddy AI is a smart personal finance management web application built using **Python and Streamlit**.

It helps users manage their income and expenses, analyze spending patterns, get budget recommendations, predict future expenses, detect unusual spending, scan receipts using OCR, and track savings goals.

##  Live Demo

🔗 **Live Application:**  
https://bugget-buddy.onrender.com

##  Features

###  User Authentication

- User Registration
- User Login
- Password Protection
- Session-based Authentication
- Logout Functionality

###  Dashboard

The dashboard provides an overview of the user's financial activity.

-  Total Income
-  Total Expenses
-  Remaining Balance
-  Spending by Category
-  AI Budget Insights
-  Expense Prediction
-  Unusual Spending Detection

###  Income Management

Users can add and manage their income to calculate their available balance.

###  Expense Management

Users can record expenses with:

- Amount
- Category
- Description
- Date

###  AI Budget Recommendation

BudgetBuddy AI provides budget recommendations based on the user's income and spending patterns.

The application follows the **50/30/20 budgeting concept**:

- **50% – Needs**
- **30% – Wants**
- **20% – Savings**

###  Expense Prediction

The application uses **Linear Regression** to predict potential future expenses based on previous expense records.

###  Unusual Spending Detection

The application analyzes spending patterns and identifies unusually high expenses using statistical analysis.

###  Smart Receipt Scanner

Users can upload a receipt image and extract expense information using OCR.

Technologies used:

- Pytesseract
- Tesseract OCR
- Pillow

###  Savings Goal

Users can create and track savings goals by entering:

- Goal Amount
- Current Savings
- Target Deadline

##  Technologies Used

| Technology | Purpose |
|------------|---------|
| Python | Programming |
| Streamlit | Web Application |
| SQLite | Database |
| NumPy | Data Processing |
| Scikit-learn | Machine Learning |
| Linear Regression | Expense Prediction |
| Pytesseract | OCR |
| Tesseract OCR | Receipt Text Extraction |
| Pillow | Image Processing |
| Docker | Deployment |
| Render | Cloud Hosting |
| GitHub | Version Control |

##  Project Structure

```text
BUGGET-BUDDY/
│
├── app.py
├── ocr.py
├── requirements.txt
├── Dockerfile
├── packages.txt
├── budgetbuddy.db
└── README.md
```

##  Installation

### 1. Clone the Repository

```bash
git clone https://github.com/AyeshaAfroze7860/-BUGGET-BUDDY.git
```

### 2. Navigate to the Project Folder

```bash
cd -BUGGET-BUDDY
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

For Windows:

```bash
venv\Scripts\activate
```

### 5. Install Required Packages

```bash
pip install -r requirements.txt
```

##  Run the Application

Run the following command:

```bash
python -m streamlit run app.py
```

The application will be available at:

```text
http://localhost:8501
```

##  OCR Setup

BudgetBuddy AI uses **Tesseract OCR** for receipt scanning.

### Windows

Tesseract should be installed at:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Linux / Docker

Tesseract is installed automatically through the Dockerfile at:

```text
/usr/bin/tesseract
```

The application automatically selects the appropriate Tesseract path based on the operating system.

##  Docker Deployment

The project uses **Docker** because the receipt scanner requires the **Tesseract OCR** system package.

The Dockerfile:

- Uses Python 3.11
- Installs Tesseract OCR
- Installs Python dependencies
- Copies application files
- Runs the Streamlit application

##  Deployment

The application is deployed using:

**Docker + Render**

### Live Application

🔗 https://bugget-buddy.onrender.com

##  Application Workflow

```text
User Registration
       ↓
     Login
       ↓
   Dashboard
       ↓
 ┌────────────────┐
 │ Add Income     │
 │ Add Expense    │
 │ Scan Receipt   │
 │ Savings Goal   │
 └────────────────┘
       ↓
 Financial Analysis
       ↓
 ┌──────────────────────┐
 │ Budget Recommendation│
 │ Expense Prediction   │
 │ Unusual Spending     │
 └──────────────────────┘
       ↓
Better Financial Planning
```

##  Objectives

- To simplify personal expense tracking.
- To manage income and expenses efficiently.
- To analyze spending patterns.
- To provide intelligent budget recommendations.
- To predict future expenses.
- To detect unusual spending.
- To reduce manual receipt entry using OCR.
- To help users manage savings goals.

## Future Enhancements

- Mobile Application
- Advanced Financial Analytics
- Interactive Charts and Reports
- Advanced Machine Learning Models
- Budget Limit Notifications
- Monthly Financial Reports
- Cloud Database Integration
- Bank Transaction Integration
- Improved Receipt Information Extraction
- Monthly and Yearly Financial Reports


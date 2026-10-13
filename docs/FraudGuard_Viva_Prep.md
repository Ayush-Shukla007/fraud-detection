# 🎓 FraudGuard AI - Viva Preparation Guide

This document contains everything you need to know to confidently defend your project during your viva. Read it carefully.

---

## 1. Project Overview
**What is this project?**
FraudGuard AI is an end-to-end Machine Learning web application designed to detect fraudulent credit card transactions in real-time. It takes 30 transaction features as input, processes them through a trained Random Forest ML model, predicts the probability of fraud, and logs the results in a database for auditing on a dashboard.

---

## 2. Machine Learning & Training
**The Dataset**
*   **Source:** The famous Kaggle Credit Card Fraud Detection dataset.
*   **Size:** 284,807 transactions.
*   **Features (30):** 
    *   `Time`: Seconds elapsed since the first transaction.
    *   `Amount`: Transaction amount (originally in USD).
    *   `V1` to `V28`: Principal Component Analysis (PCA) features. Because credit card data is highly confidential, banks mathematically transform (encrypt/obfuscate) the actual user data (like location, age, merchant) into random-looking numbers (V1-V28) using PCA.

**The Imbalance Problem & Solution**
*   **Problem:** Only **0.17%** of the dataset was actually fraud. If a model just blindly guessed "Legitimate" every time, it would be 99.83% accurate, but totally useless.
*   **Solution:** During training, we used `class_weight='balanced'`. This mathematically penalizes the model heavily if it gets a fraud case wrong, forcing it to pay attention to the rare fraud cases.

**Model Selection**
We trained and evaluated three models:
1. Logistic Regression
2. XGBoost
3. **Random Forest Classifier (The Winner)**

We chose Random Forest because it achieved a nearly perfect **ROC-AUC score of 0.9998**. ROC-AUC measures how well a model can distinguish between classes. 

**Preprocessing & Saving**
Before training, we used Scikit-Learn's `StandardScaler` to scale the data (so large numbers don't overpower small ones). Both the trained model and the scaler were saved to disk as `.joblib` files so the backend can load them instantly without retraining.

---

## 3. The Backend (FastAPI + SQLite)
**Why FastAPI?**
It is a modern, ultra-fast Python web framework. It supports asynchronous programming (`async def`), which means it can handle multiple users simultaneously without blocking.

**Pydantic (Data Validation)**
When the frontend sends data, FastAPI uses Pydantic to validate it. For example, if a user submits a negative amount, Pydantic throws a 422 Error before the ML model even sees it.

**Database (SQLite + SQLAlchemy)**
Every time a transaction is predicted, it is saved into a local `fraudguard.db` SQLite database using SQLAlchemy (an Object Relational Mapper). This allows the Dashboard to load historical statistics.

**The INR to USD Conversion Logic (Important!)**
Because the model was trained on USD amounts, but our frontend asks the user for Indian Rupees (INR), the backend intercepts the request in `ml_service.py`. It divides the INR amount by 96 to get the USD equivalent, scales it, and feeds it to the model. However, it explicitly saves the **INR amount** to the SQLite database so the frontend history remains in Rupees!

---

## 4. The Frontend (React + Vite)
**Tech Stack:** 
*   **React:** For building component-based, interactive user interfaces.
*   **Vite:** A build tool that is significantly faster than standard `create-react-app`.
*   **Recharts:** An SVG charting library used to draw the dynamic graphs on the Dashboard and Performance pages.
*   **Axios:** Used to make HTTP API calls (GET/POST) to the FastAPI backend.

**Design System:**
We did **not** use Tailwind or Bootstrap. The entire UI is built using custom CSS (`globals.css`) utilizing a design trend called **Glassmorphism** (translucent backgrounds with `backdrop-filter: blur`, deep gradients, and floating animations).

---

## 5. End-to-End Workflow (How a prediction happens)
If the examiner asks: *"Trace what happens when I click 'Analyze Transaction'."*

1. **Frontend:** React captures the `Amount`, `Time`, and `V1-V28` from the HTML form. It packages them into a JSON object and uses Axios to send a `POST` request to the backend.
2. **Backend Validation:** FastAPI receives the JSON. Pydantic checks if the amount is > 0 and all fields are correct.
3. **ML Service:** 
    *   Creates a UUID (Transaction ID).
    *   Divides the INR Amount by 96 to get USD.
    *   Passes the USD Amount and V-features to the `StandardScaler`.
    *   Passes the scaled array to `RandomForest.predict_proba()`.
4. **Database:** The backend takes the resulting probability, flags it as LOW, MEDIUM, or HIGH risk, and saves the original INR data + prediction to the SQLite database.
5. **Response:** FastAPI returns a JSON response to React. React updates the UI, rendering the red/green risk badge and filling the animated probability gauge.

---

## 6. Common Viva Questions & Answers

**Q1: Why did you use PCA features (V1-V28) instead of real names and locations?**
*Answer:* Credit card datasets are strictly bound by confidentiality laws. PCA (Principal Component Analysis) allows banks to anonymize the data while retaining the statistical variance needed for ML models to find fraud patterns.

**Q2: What is ROC-AUC and why use it instead of Accuracy?**
*Answer:* In a highly imbalanced dataset (99.8% legitimate), accuracy is misleading. A model that always guesses "Legitimate" has 99.8% accuracy but 0% fraud detection. ROC-AUC measures the model's true ability to separate the two classes regardless of imbalance.

**Q3: How do you handle Batch Processing (CSV uploads)?**
*Answer:* When a CSV is dropped in, the frontend sends it via `multipart/form-data`. The backend reads the rows using Pandas, loops through them, scores them individually, saves them to the DB, and yields the asyncio event loop periodically (`await asyncio.sleep(0)`) to ensure the server doesn't freeze under heavy CPU load.

**Q4: How did you design the database?**
*Answer:* We used a single `transactions` table in SQLite. It has an auto-incrementing ID, a unique UUID, the timestamp, the transaction amount, the binary prediction (1 or 0), the exact probability score (e.g. 0.98), the risk level, and a UTC creation timestamp.

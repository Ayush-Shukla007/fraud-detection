# FraudGuard Pro — Real-Time Credit Card Fraud Detection System

> A full-stack machine learning web application for real-time credit card fraud detection, transaction risk profiling, and batch transaction auditing.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2-20232A.svg?style=flat&logo=react&logoColor=61DAFB)](https://reactjs.org)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3-F7931E.svg?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [System Architecture](#system-architecture)
5. [Machine Learning Pipeline](#machine-learning-pipeline)
6. [Dataset Information](#dataset-information)
7. [Installation & Setup](#installation--setup)
8. [Authentication & Demo Accounts](#authentication--demo-accounts)
9. [Developer API Integration](#developer-api-integration)
10. [Project Structure](#project-structure)
11. [License](#license)

---

## Project Overview

**FraudGuard Pro** is an enterprise-grade credit card fraud detection platform built with Python, FastAPI, React, and Scikit-Learn. The application addresses the challenge of extreme class imbalance in financial transactions by leveraging robust tree-based classification ensembles, scalable asynchronous backend architecture, and an intuitive fintech monitoring interface.

### Highlights
* **Real-Time Classification:** Evaluates financial transactions in milliseconds with probability scoring and risk tier categorization (Low, Medium, High).
* **Role-Based Access Control (RBAC):** Built-in JWT authentication separating Administrator and Analyst Viewer permissions.
* **Batch Auditing:** High-throughput CSV processing capable of classifying thousands of transactions in bulk with exportable analytical summaries.
* **Developer API:** REST API access with scoped API key generation for programmatic fraud checks.

---

## Key Features

| Feature | Description |
|:---|:---|
| **Fintech Dashboard** | Live KPI statistics, 30-day fraud trends, transaction distribution, and priority alert banners. |
| **Single Transaction Analysis** | Interactive parameter entry for transaction amount, time, and PCA features ($V_1$–$V_{28}$) with instant risk classification. |
| **Batch Detection** | Drag-and-drop CSV upload for processing bulk transactional data with instant CSV result export. |
| **Transaction History** | Filterable, searchable, and paginated transaction audit log with single and bulk record management. |
| **Model Performance** | Confusion matrix, ROC-AUC curve visualization, precision-recall analysis, and multi-model benchmark metrics. |
| **Developer API & Docs** | Comprehensive endpoint documentation, curl/Python examples, and API key management. |

---

## Technology Stack

### Frontend
* **React 18** with functional components and modern hooks
* **React Router v6** for client-side protected routing
* **Recharts** for responsive SVG metrics and distribution charts
* **Axios** with global interceptors for Bearer token authorization
* **Lucide React** for minimalist, SVG-based interface icons
* **Vite** for rapid hot-module replacement and optimized builds

### Backend
* **FastAPI** for asynchronous REST API execution
* **SQLAlchemy 2.0 (Async)** with SQLite + `aiosqlite`
* **Pydantic v2** for rigorous payload validation
* **python-jose** and **passlib[bcrypt]** for secure JWT encryption and password hashing
* **Uvicorn** high-performance ASGI server

### Machine Learning
* **Scikit-Learn** for Random Forest classifier, feature scaling, and evaluation
* **XGBoost** for gradient-boosted decision trees
* **Pandas & NumPy** for vectorized dataset transformations
* **Joblib** for model serialization

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                           │
│  React 18 + Vite (SPA) — Dark Mode Financial Dashboard     │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON (Axios + JWT)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI APPLICATION LAYER                 │
│  ├── /api/v1/auth          (JWT Tokens & RBAC)              │
│  ├── /api/v1/predict       (Real-Time & Batch Inference)    │
│  ├── /api/v1/transactions  (History CRUD & Pagination)      │
│  ├── /api/v1/dashboard     (KPI Metrics & Daily Trends)     │
│  └── /api/v1/model         (Evaluation & Performance Data)  │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│      PERSISTENCE LAYER       │ │         ML ENGINE          │
│   SQLite (Async SQLAlchemy)  │ │   StandardScaler +         │
│   Tables: User, Transaction  │ │   RandomForest / XGBoost   │
└──────────────────────────────┘ └────────────────────────────┘
```

---

## Machine Learning Pipeline

1. **Class Imbalance Strategy:** The underlying dataset exhibits extreme imbalance (~0.17% fraud). Balanced class weights and stratified splits ensure high sensitivity toward fraudulent cases without sacrificing precision.
2. **Feature Preprocessing:** Features $V_1$ through $V_{28}$ are PCA-transformed components. Continuous attributes (such as `Time` and `Amount`) are normalized using `StandardScaler`.
3. **Model Evaluation:**
   * **Accuracy:** >99.9%
   * **ROC-AUC Score:** >0.97
   * **Recall (Fraud Detection Rate):** >80% on unseen test distributions
4. **Fallback Engine:** If pre-trained weights are not present on local disk, the backend gracefully activates a calibrated heuristic fallback engine to guarantee zero application downtime.

---

## Dataset Information

The model architecture is designed around the standard **Kaggle Credit Card Fraud Detection Dataset**:
* **Total Transactions:** 284,807
* **Fraudulent Transactions:** 492 (0.172%)
* **Features:** 30 numerical input features (`Time`, `Amount`, and $V_1$ to $V_{28}$) + binary target `Class`.
* **Sample Testing Data:** A ready-to-use sample dataset with 1,000 transactions is included in `data/demo_transactions.csv` for immediate batch upload testing.

---

## Installation & Setup

### Prerequisites
* **Python 3.10+**
* **Node.js 18+** & **npm**

### 1. Clone the Repository
```bash
git clone https://github.com/Ayush-Shukla007/fraud-detection.git
cd fraud-detection
```

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn main:app --reload --port 8000
```
Backend will be available at: **`http://127.0.0.1:8000`**  
Interactive API Docs (Swagger UI): **`http://127.0.0.1:8000/docs`**

### 3. Frontend Setup
In a new terminal:
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend will be available at: **`http://localhost:5173`**

---

## Authentication & Demo Accounts

The application automatically seeds default accounts upon first startup:

| Role | Username | Password | Access Scope |
|:---|:---|:---|:---|
| **Administrator** | `admin` | `admin` | Full system access: Dashboard, Single Check, Batch CSV Auditing, Global History, Model Benchmarks. |
| **Analyst Viewer** | `viewer` | `viewer` | Scoped access: Personal Dashboard, Single Transaction Check, Scoped History, Developer API Keys. |

---

## Developer API Integration

FraudGuard Pro offers a RESTful API for external applications to evaluate transaction risk.

### Analyze Transaction
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/predict" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2500.0,
    "time": 86400,
    "v1": -2.31,
    "v2": 1.45,
    "v3": -1.90,
    "v4": 3.80
  }'
```

### Response
```json
{
  "transaction_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "prediction": "fraud",
  "fraud_probability": 0.88,
  "risk_level": "High",
  "amount": 2500.0,
  "timestamp": "2026-10-28T11:45:00Z"
}
```

---

## Project Structure

```
fraud-detection/
├── backend/
│   ├── routers/
│   │   ├── auth.py          # JWT authentication & user management
│   │   ├── dashboard.py     # KPI summary & daily chart aggregation
│   │   ├── model.py         # Model performance & metrics endpoint
│   │   ├── predict.py       # Single & batch prediction endpoints
│   │   └── transactions.py  # Paginated transaction history & deletion
│   ├── config.py            # Environment configuration
│   ├── database.py          # SQLAlchemy async session setup
│   ├── main.py              # Application lifecycle & FastAPI root
│   ├── ml_service.py        # ML loading, scaling & inference engine
│   ├── models.py            # SQLAlchemy ORM models (User, Transaction)
│   ├── schemas.py           # Pydantic request & response schemas
│   └── requirements.txt     # Python backend dependencies
├── data/
│   ├── demo_transactions.csv# Pre-generated sample batch dataset (1,000 rows)
│   └── README.md            # Dataset documentation and download instructions
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components & layouts
│   │   ├── context/         # AuthContext with persistent JWT storage
│   │   ├── pages/           # Dashboard, CheckTransaction, Batch, History, etc.
│   │   ├── services/        # Axios API client functions
│   │   └── styles/          # Design system & dark theme variables
│   ├── index.html           # HTML entry point with SVG favicon
│   ├── package.json         # Frontend dependencies & scripts
│   └── vite.config.js       # Vite configuration
├── ml/
│   ├── demo_data_generator.py # Synthetic sample generator
│   ├── evaluate.py          # ROC curves and confusion matrix logic
│   ├── predict.py           # Standalone prediction utilities
│   ├── preprocess.py        # Feature engineering and StandardScaler helpers
│   ├── train.py             # Model training script (Random Forest / XGBoost)
│   └── metrics.json         # Evaluated model benchmark scores
└── README.md                # Project documentation
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

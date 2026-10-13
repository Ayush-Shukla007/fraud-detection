<div align="center">

# 🛡️ FraudGuard AI

### Credit Card Fraud Detection using AI/ML

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2-61DAFB.svg)](https://reactjs.org)
[![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.3-orange.svg)](https://scikit-learn.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-red.svg)](https://xgboost.readthedocs.io)

*A full-stack AI/ML web application for real-time credit card fraud detection with a professional fintech dashboard UI.*

</div>

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Features](#-features)
3. [Tech Stack](#-tech-stack)
4. [Architecture](#-architecture)
5. [Machine Learning Workflow](#-machine-learning-workflow)
6. [Dataset Information](#-dataset-information)
7. [Installation](#-installation)
8. [Training the Model](#-training-the-model)
9. [Running the Backend](#-running-the-backend)
10. [Running the Frontend](#-running-the-frontend)
11. [API Documentation](#-api-documentation)
12. [Project Structure](#-project-structure)
13. [Screenshots](#-screenshots)
14. [Future Improvements](#-future-improvements)

---

## 🎯 Project Overview

**FraudGuard AI** is an AI-powered credit card fraud detection system built as a full-stack web application. It uses machine learning models trained on real transaction data to classify transactions as **Legitimate** or **Fraudulent** in real time.

The system features:
- A **dark fintech dashboard** with real-time statistics
- **Single transaction analysis** with fraud probability scores
- **Batch CSV processing** for multiple transactions
- **Transaction history** with search, filter, and pagination
- **Model performance monitoring** with confusion matrix and ROC curves

> ⚡ **Demo Mode:** The application runs in **DEMO MODE** if no trained model is found. Real predictions activate automatically when `ml/model.joblib` is present.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 Dashboard | Real-time stats, charts, recent suspicious transactions |
| 🔍 Check Transaction | Single transaction analysis with fraud probability gauge |
| 📦 Batch Detection | CSV upload + bulk analysis + downloadable results |
| 📋 Transaction History | Searchable, filterable, paginated history |
| 📈 Model Performance | Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix |
| 🎭 Demo Mode | Fully functional without real model file |
| 🔄 Real Model Support | Drop-in replacement — just add `model.joblib` |

---

## 🛠 Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **React Router 6** | Client-side routing |
| **Recharts** | Charts and visualizations |
| **Axios** | HTTP client |
| **React Dropzone** | CSV file upload |
| **Lucide React** | Icon library |
| **Vite** | Build tool |

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | REST API framework |
| **SQLAlchemy 2.0** | ORM (async) |
| **SQLite + aiosqlite** | Database |
| **Pydantic v2** | Data validation |
| **Uvicorn** | ASGI server |

### Machine Learning
| Technology | Purpose |
|------------|---------|
| **Scikit-learn** | ML models, preprocessing, evaluation |
| **XGBoost** | Gradient boosting classifier |
| **Pandas / NumPy** | Data manipulation |
| **Joblib** | Model serialization |
| **SMOTE (optional)** | Class imbalance handling |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      BROWSER (React App)                    │
│  ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌─────────┐   │
│  │Dashboard │  │  Check Txn  │  │  Batch   │  │ History │   │
│  └──────────┘  └─────────────┘  └──────────┘  └─────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP (REST API)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Port 8000)               │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  /predict  │  │ /transactions│  │  /dashboard/stats  │   │
│  └────────────┘  └──────────────┘  └────────────────────┘   │
│         │                │                    │             │
│         ▼                ▼                    ▼             │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ ML Service │  │  SQLite DB   │  │   SQLite DB        │   │
│  └────────────┘  └──────────────┘  └────────────────────┘   │
│         │                                                   │ 
│         ▼                                                   │
│  ┌────────────────────────────────────────┐                 │
│  │         ML Module (ml/)                │                 │
│  │  model.joblib   scaler.joblib          │                 │
│  │  DEMO MODE if model not found          │                 │
│  └────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Machine Learning Workflow

```
Dataset (creditcard.csv)
        │
        ▼
1. Load & Inspect
   - Shape, dtypes, missing values
   - Class distribution (0.172% fraud)
        │
        ▼
2. Preprocessing
   - StandardScaler on Amount & Time
   - Handle NaN values
        │
        ▼
3. Handle Class Imbalance
   - class_weight='balanced'
   - Optional: SMOTE oversampling
        │
        ▼
4. Train/Test Split (80/20, stratified)
        │
        ▼
5. Model Training
   ├── Logistic Regression
   ├── Random Forest
   └── XGBoost
        │
        ▼
6. Evaluation (per model)
   - Accuracy, Precision, Recall
   - F1-Score, ROC-AUC
   - Confusion Matrix
        │
        ▼
7. Best Model Selection (by ROC-AUC)
        │
        ▼
8. Save Artifacts
   ├── model.joblib (best model)
   ├── scaler.joblib (fitted scaler)
   ├── features.json (feature names)
   └── metrics.json (evaluation results)
```

### Why Random Forest / XGBoost for Fraud Detection?

| Concern | Solution |
|---------|----------|
| Class Imbalance (0.17% fraud) | `class_weight='balanced'` + SMOTE |
| High False Negatives cost | Optimize for Recall + F1 |
| Interpretability | Feature importance from tree models |
| Performance | Ensemble methods outperform Logistic Regression |

---

## 📊 Dataset Information

**Source:** [Kaggle - Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)

| Property | Value |
|----------|-------|
| Total Samples | 284,807 |
| Features | 30 (Time, V1-V28, Amount) |
| Target | Class (0=Legitimate, 1=Fraud) |
| Fraud Rate | 0.172% |
| File Size | ~144 MB |

> **Note:** V1-V28 are PCA-transformed features (anonymized for privacy).

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **npm** or **yarn**

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd fraud-detection
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

---

## 🎓 Training the Model

### Option 1: Use the Real Dataset (Recommended)

1. Download `creditcard.csv` from Kaggle (see `data/README.md`)
2. Place it in the `data/` directory

```bash
cd ml

# Train with default (Random Forest)
python train.py --data ../data/creditcard.csv

# Train with XGBoost
python train.py --data ../data/creditcard.csv --model xgboost

# Train all and compare
python train.py --data ../data/creditcard.csv --compare
```

This saves:
- `ml/model.joblib` — trained model
- `ml/scaler.joblib` — fitted scaler
- `ml/features.json` — feature column names
- `ml/metrics.json` — evaluation results

### Option 2: Demo Mode (No Dataset Required)

```bash
cd ml
python train.py --demo
```

Generates synthetic data and trains a demo model.

---

## 🖥 Running the Backend

```bash
cd backend

# Activate virtual environment first
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Start the server
uvicorn main:app --reload --port 8000
```

The API will be available at: **http://localhost:8000**

Interactive API docs: **http://localhost:8000/docs**

> 💡 If `ml/model.joblib` exists, the backend uses the **real model**.  
> Otherwise, it automatically starts in **DEMO MODE**.

---

## 🌐 Running the Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at: **http://localhost:5173**

---

## 📡 API Documentation

### Base URL: `http://localhost:8000/api/v1`

#### Prediction

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict` | Analyze a single transaction |
| `POST` | `/predict/batch` | Upload CSV for batch analysis |

**POST /predict — Request Body:**
```json
{
  "amount": 149.62,
  "time": 0.0,
  "v1": -1.359807134,
  "v2": -0.072781173,
  "v3": 2.536346737,
  "v4": 1.378155224,
  "v5": -0.338320769,
  "v6": 0.462387778,
  "v7": 0.239598554,
  "v8": 0.098697901,
  "v9": 0.363786970,
  "v10": 0.090794172,
  "v11": -0.551599533,
  "v12": -0.617800856,
  "v13": -0.991389847,
  "v14": -0.311169354,
  "v15": 1.468176972,
  "v16": -0.470400525,
  "v17": 0.207971242,
  "v18": 0.025790997,
  "v19": 0.403992960,
  "v20": 0.251412098,
  "v21": -0.018306778,
  "v22": 0.277837576,
  "v23": -0.110473910,
  "v24": 0.066928075,
  "v25": 0.128539358,
  "v26": -0.189114844,
  "v27": 0.133558377,
  "v28": -0.021053053
}
```

**POST /predict — Response:**
```json
{
  "transaction_id": "txn_abc123",
  "prediction": "Fraud",
  "fraud_probability": 0.947,
  "risk_level": "High",
  "amount": 149.62,
  "timestamp": "2024-01-15T10:30:00"
}
```

#### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/transactions` | Get paginated history |
| `GET` | `/transactions/{id}` | Get single transaction |
| `DELETE` | `/transactions` | Clear all history |

**GET /transactions — Query Params:**
- `page` (int, default: 1)
- `page_size` (int, default: 20)
- `prediction_filter` (str: "Fraud"/"Legitimate")
- `risk_filter` (str: "High"/"Medium"/"Low")
- `search` (str: transaction ID)

#### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/stats` | Overall statistics |
| `GET` | `/dashboard/chart-data` | Time-series data for charts |

#### Model

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/model/metrics` | Model evaluation metrics |
| `GET` | `/health` | System health check |

**GET /health — Response:**
```json
{
  "status": "ok",
  "mode": "demo",
  "model_loaded": false,
  "version": "1.0.0"
}
```

---

## 📁 Project Structure

```
fraud-detection/
│
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   │   ├── Sidebar.jsx  # Navigation sidebar
│   │   │   │   ├── Header.jsx   # Top header bar
│   │   │   │   └── Layout.jsx   # Page wrapper
│   │   │   └── UI/
│   │   │       ├── Card.jsx        # Glassmorphism card
│   │   │       ├── Badge.jsx       # Status badges
│   │   │       ├── StatCard.jsx    # Metric display card
│   │   │       ├── DataTable.jsx   # Responsive table
│   │   │       ├── EmptyState.jsx  # Empty state UI
│   │   │       ├── LoadingSpinner.jsx
│   │   │       └── Toast.jsx       # Notifications
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx       # Overview dashboard
│   │   │   ├── CheckTransaction.jsx # Single transaction
│   │   │   ├── BatchDetection.jsx  # CSV batch upload
│   │   │   ├── TransactionHistory.jsx # History + search
│   │   │   └── ModelPerformance.jsx  # ML metrics
│   │   ├── services/
│   │   │   └── api.js             # Axios API service
│   │   ├── styles/
│   │   │   └── globals.css        # Global CSS + variables
│   │   ├── App.jsx                # Routes
│   │   └── main.jsx               # Entry point
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── backend/                     # FastAPI application
│   ├── routers/
│   │   ├── predict.py           # Prediction endpoints
│   │   ├── transactions.py      # History endpoints
│   │   ├── dashboard.py         # Stats endpoints
│   │   └── model.py             # Model metrics endpoints
│   ├── main.py                  # FastAPI app setup
│   ├── database.py              # SQLAlchemy + SQLite setup
│   ├── models.py                # ORM models
│   ├── schemas.py               # Pydantic schemas
│   ├── ml_service.py            # ML model loader + predictor
│   ├── config.py                # Settings management
│   └── requirements.txt
│
├── ml/                          # Machine learning pipeline
│   ├── train.py                 # Training script
│   ├── preprocess.py            # Preprocessing utilities
│   ├── evaluate.py              # Evaluation utilities
│   ├── predict.py               # Prediction utilities
│   ├── demo_data_generator.py   # Synthetic data generator
│   ├── model.joblib             # Trained model (after training)
│   ├── scaler.joblib            # Fitted scaler (after training)
│   ├── features.json            # Feature names (after training)
│   ├── metrics.json             # Evaluation results (after training)
│   └── README_ML.md             # ML-specific documentation
│
├── data/
│   └── README.md                # Dataset download instructions
│
├── .gitignore
└── README.md                    # This file
```

---

## 📸 Screenshots

> *Screenshots can be added here after running the application.*

| Page | Description |
|------|-------------|
| Dashboard | Overview with stats and charts |
| Check Transaction | Single fraud analysis form |
| Batch Detection | CSV upload and bulk results |
| Transaction History | Searchable history table |
| Model Performance | ML evaluation metrics |

---

## 🔮 Future Improvements

| Feature | Priority |
|---------|----------|
| Real-time WebSocket alerts for high-risk transactions | High |
| User authentication / multi-user support | High |
| Email/SMS alerts for fraud detection | Medium |
| Explainable AI (SHAP values for predictions) | Medium |
| Auto-retraining pipeline with new data | Medium |
| Docker containerization | Medium |
| Additional ML models (Neural Network, LightGBM) | Low |
| Mobile-responsive design | Low |
| Report generation (PDF export) | Low |
| Multi-language support | Low |

---

## 👨‍💻 Contributing

This project is built as an AI/ML portfolio project. Feel free to fork, modify, and extend it.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ using React, FastAPI, and Scikit-learn**

🛡️ FraudGuard AI — Protecting transactions with intelligence

</div>

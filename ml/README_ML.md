# FraudGuard AI — ML Pipeline Documentation

> **Complete guide to training, evaluating, and deploying the fraud detection model.**

---

## 📋 Table of Contents

1. [Dataset Format](#1-dataset-format)
2. [How to Download the Dataset](#2-how-to-download-the-dataset)
3. [Installation & Requirements](#3-installation--requirements)
4. [Running Training](#4-running-training)
5. [Model Comparison & Expected Results](#5-model-comparison--expected-results)
6. [How Models Are Saved](#6-how-models-are-saved)
7. [Connecting the Model to the Backend](#7-connecting-the-model-to-the-backend)
8. [Feature Engineering Notes](#8-feature-engineering-notes)
9. [Class Imbalance Handling](#9-class-imbalance-handling)
10. [Demo Mode](#10-demo-mode)
11. [File Structure](#11-file-structure)

---

## 1. Dataset Format

The model is trained on the **Kaggle Credit Card Fraud Detection Dataset**.

### Expected CSV columns

| Column | Type | Description |
|--------|------|-------------|
| `Time` | float | Seconds elapsed since the first transaction in the dataset |
| `V1` – `V28` | float | PCA-transformed anonymized features (28 columns) |
| `Amount` | float | Transaction amount in euros |
| `Class` | int | **Target variable** — `0` = Legitimate, `1` = Fraud |

> [!NOTE]
> V1–V28 are PCA components of the original features. The original features were anonymized for privacy reasons by the dataset authors. You cannot reverse-engineer the original features.

### Example row

```
Time,V1,V2,V3,...,V28,Amount,Class
0,-1.3598,-0.0727,2.5363,...,0.0218,149.62,0
```

### Dataset statistics (real Kaggle data)

| Metric | Value |
|--------|-------|
| Total transactions | 284,807 |
| Fraudulent | 492 (0.173%) |
| Legitimate | 284,315 (99.827%) |
| Imbalance ratio | ~578:1 |
| Time span | 2 days |

---

## 2. How to Download the Dataset

### Option A — Kaggle CLI (Recommended)

```bash
# 1. Install Kaggle CLI
pip install kaggle

# 2. Get API key from https://www.kaggle.com/settings → API → Create New Token
#    This downloads kaggle.json — move it to:
#    Windows: C:\Users\<username>\.kaggle\kaggle.json
#    Linux/Mac: ~/.kaggle/kaggle.json

# 3. Download dataset
kaggle datasets download -d mlg-ulb/creditcardfraud

# 4. Unzip
unzip creditcardfraud.zip -d data/

# 5. Verify
ls data/creditcard.csv  # Should be ~150MB
```

### Option B — Manual Download

1. Go to: [https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
2. Click **Download** (requires free Kaggle account)
3. Extract `creditcard.csv` to `fraud-detection/data/creditcard.csv`

### Option C — Use Demo Mode (No Download Needed)

```bash
# Trains on synthetic data — useful for testing the full pipeline
python ml/train.py --demo
```

---

## 3. Installation & Requirements

```bash
# Core requirements (required)
pip install scikit-learn pandas numpy joblib

# XGBoost (recommended — best performing model)
pip install xgboost

# SMOTE for advanced imbalance handling (optional)
pip install imbalanced-learn

# For plots/visualizations (optional)
pip install matplotlib

# Install all at once
pip install scikit-learn pandas numpy joblib xgboost imbalanced-learn matplotlib
```

> [!TIP]
> Use a virtual environment to avoid dependency conflicts:
> ```bash
> python -m venv venv
> venv\Scripts\activate   # Windows
> pip install -r requirements.txt
> ```

---

## 4. Running Training

### Demo Mode (No dataset needed — start here)

```bash
cd fraud-detection
python ml/train.py --demo
```

This trains on 10,000 synthetic transactions and saves real model files.

### Real Dataset Training

```bash
# Train all models and auto-select the best
python ml/train.py --data data/creditcard.csv

# Train a specific model
python ml/train.py --data data/creditcard.csv --model xgboost
python ml/train.py --data data/creditcard.csv --model random_forest
python ml/train.py --data data/creditcard.csv --model logistic
```

### Training Output

After training, these files are created in `ml/`:

```
ml/
├── model.joblib      ← Best trained model (ready for predictions)
├── scaler.joblib     ← Fitted StandardScaler (required for predictions)
├── features.json     ← Ordered list of feature names
└── metrics.json      ← Full evaluation metrics
```

---

## 5. Model Comparison & Expected Results

### On the real Kaggle dataset (284,807 transactions)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| Logistic Regression | ~99.92% | ~0.87 | ~0.74 | ~0.80 | ~0.971 |
| Random Forest | ~99.96% | ~0.96 | ~0.81 | ~0.88 | ~0.975 |
| **XGBoost** | **~99.96%** | **~0.94** | **~0.84** | **~0.89** | **~0.979** |

> [!IMPORTANT]
> **Why accuracy is misleading here:** A model that always predicts "Not Fraud" gets 99.83% accuracy. We care most about **Recall** (catching actual fraud) and **ROC-AUC** (overall discrimination).

### Interpreting the metrics

| Metric | What it means for fraud detection |
|--------|-----------------------------------|
| **Recall (Sensitivity)** | % of actual fraud cases caught. High recall = fewer missed frauds. **Most critical.** |
| **Precision** | % of fraud alerts that are real. Low precision = more customer friction. |
| **F1 Score** | Harmonic mean of precision + recall. Good single-number summary. |
| **ROC-AUC** | Threshold-independent score. AUC=1.0 is perfect, AUC=0.5 is random. Best for model selection. |

### Confusion matrix breakdown

```
                  Predicted: Legit    Predicted: Fraud
Actual: Legit          56,861              2        ← False Positives (customer friction)
Actual: Fraud              13             86        ← False Negatives (missed fraud!) ⚠️
```

### On synthetic demo data

Demo data results will be lower (synthetic data is simpler than real data):

| Model | Expected ROC-AUC |
|-------|-----------------|
| Logistic Regression | ~0.85–0.92 |
| Random Forest | ~0.92–0.97 |
| XGBoost | ~0.93–0.98 |

---

## 6. How Models Are Saved

All outputs are saved using **joblib** (Python's standard ML serialization library):

```python
import joblib

# Saving (done by train.py)
joblib.dump(model, "ml/model.joblib")
joblib.dump(scaler, "ml/scaler.joblib")

# Loading (done by Flask API)
model = joblib.load("ml/model.joblib")
scaler = joblib.load("ml/scaler.joblib")
```

### `metrics.json` format

```json
{
  "model_name": "RandomForest",
  "accuracy": 0.999560,
  "precision": 0.959596,
  "recall": 0.810345,
  "f1_score": 0.878788,
  "roc_auc": 0.975234,
  "confusion_matrix": {
    "tp": 94,
    "tn": 56861,
    "fp": 4,
    "fn": 22
  },
  "training_samples": 227845,
  "test_samples": 56962,
  "features_used": ["Time", "V1", "V2", "...", "V28", "Amount"],
  "is_demo": false,
  "all_model_results": [...]
}
```

> [!WARNING]
> **Never use `pickle` to save ML models.** Joblib is safer and more efficient for numpy arrays. Also, never load a `.joblib` file from an untrusted source (it can execute arbitrary code).

---

## 7. Connecting the Model to the Backend

The Flask API (`app.py`) loads the model at startup and uses `predict.py` functions for inference.

### In `app.py` (startup)

```python
from ml.predict import load_model, predict_single, load_feature_list

# Load once at startup — NOT on every request
model, scaler = load_model("ml/model.joblib", "ml/scaler.joblib")
feature_order = load_feature_list("ml/features.json")
```

### In the `/api/detect` endpoint

```python
from ml.preprocess import validate_transaction_input

@app.route('/api/detect', methods=['POST'])
def detect_fraud():
    data = request.get_json()
    features = data.get('features', {})

    # Step 1: Validate input
    is_valid, error, cleaned = validate_transaction_input(features, feature_order)
    if not is_valid:
        return jsonify({"error": error}), 400

    # Step 2: Predict
    result = predict_single(model, scaler, cleaned, feature_order)

    return jsonify(result), 200
```

### Retraining workflow

```
New Data → train.py → model.joblib → restart Flask → live predictions updated
```

> [!TIP]
> To update the model without downtime: save the new model to `model_new.joblib`, then atomically rename it to `model.joblib`. The Flask server can be configured to hot-reload.

---

## 8. Feature Engineering Notes

### What are V1–V28?

The original dataset authors applied **Principal Component Analysis (PCA)** to the raw transaction features for privacy. The original features included:

- Merchant ID, merchant category, merchant location
- Card type, card age, cardholder demographics
- Transaction time of day, day of week
- Historical transaction patterns (velocity, geography)
- Device fingerprint, IP address

After PCA, these become anonymous components V1–V28.

### Why keep `Time` and `Amount`?

These two features were **not** PCA-transformed (to preserve their interpretability):

- **`Time`**: Fraud patterns can be time-dependent (e.g., unusual activity at 3 AM)
- **`Amount`**: Fraud often involves atypical amounts (very small for card testing, very large for theft)

### Feature importance (typical ranking)

Based on Random Forest feature importance on the real dataset:

| Rank | Feature | Importance | Interpretation |
|------|---------|-----------|----------------|
| 1 | V14 | ~0.14 | Highly negative in fraud transactions |
| 2 | V4 | ~0.10 | Highly positive in fraud transactions |
| 3 | V12 | ~0.08 | Strongly negative in fraud |
| 4 | V10 | ~0.07 | Negative in fraud |
| 5 | V11 | ~0.06 | Positive in fraud |
| 6 | Amount | ~0.05 | Fraud amount distribution differs |
| ... | V1–V28 | varies | |
| Last | Time | ~0.01 | Weakest signal |

> [!NOTE]
> Feature importance can be extracted and displayed via:
> ```python
> import json
> import joblib
> import numpy as np
> model = joblib.load("ml/model.joblib")
> importances = model.feature_importances_  # Works for RF and XGBoost
> ```

---

## 9. Class Imbalance Handling

Credit card fraud data is severely imbalanced: **only 0.17% of transactions are fraud**.

### Why this is a problem

Without special handling, a model that **always predicts "Not Fraud"** achieves:
- Accuracy: **99.83%** ← Looks great! But catches zero fraud.
- Recall: **0%** ← Completely useless.

### Strategy 1: `class_weight='balanced'` (used by default)

Built into LogisticRegression and RandomForestClassifier.

**How it works:** Automatically adjusts the loss function to penalize misclassifying the minority (fraud) class more heavily.

```python
# Effective weight = n_samples / (n_classes * class_count)
# For fraud (n=492): weight = 284807 / (2 * 492) = 289
# For legit (n=284315): weight = 284807 / (2 * 284315) = 0.5
```

### Strategy 2: XGBoost `scale_pos_weight`

XGBoost's equivalent parameter:

```python
# scale_pos_weight = n_negative / n_positive = 284315 / 492 ≈ 578
XGBClassifier(scale_pos_weight=578)
```

### Strategy 3: SMOTE (if `imbalanced-learn` is installed)

**SMOTE** (Synthetic Minority Over-sampling Technique) creates synthetic fraud samples:

```
Before SMOTE: 227,845 legit + 394 fraud
After SMOTE:  227,845 legit + 227,845 fraud (balanced!)
```

> [!CAUTION]
> Apply SMOTE **only on training data** — never on test data. Applying SMOTE to test data causes data leakage and inflated metrics.

### Which strategy is best?

| Strategy | Pros | Cons |
|----------|------|------|
| `class_weight` | Simple, no data modification, fast | Slightly lower recall than SMOTE |
| `scale_pos_weight` | Built into XGBoost, effective | Only for XGBoost |
| SMOTE | Often highest recall, more training data | Slower, synthetic samples can introduce noise |

**Recommendation:** Start with `class_weight='balanced'`. Add SMOTE if recall is below 0.80.

---

## 10. Demo Mode

Demo mode trains on **synthetic data** generated by scikit-learn's `make_classification`.

```bash
python ml/train.py --demo
```

The demo data:
- Is NOT real financial data
- Is generated algorithmically with `random_state=42` (fully reproducible)
- Has similar statistical properties to real fraud data (imbalanced, continuous)
- Produces lower metric scores than the real dataset (simpler decision boundary)

### Generating test transactions

```bash
# Generate 1000 transactions for batch testing
python ml/demo_data_generator.py

# Generate a single fraud transaction for API testing
python ml/demo_data_generator.py --single-fraud

# Generate custom dataset
python ml/demo_data_generator.py --samples 5000 --fraud-rate 0.03
```

---

## 11. File Structure

```
fraud-detection/
├── ml/
│   ├── train.py                ← Main training script
│   ├── preprocess.py           ← Data loading & preprocessing utilities
│   ├── evaluate.py             ← Model evaluation & visualization
│   ├── predict.py              ← Inference utilities for Flask API
│   ├── demo_data_generator.py  ← Synthetic test data generator
│   ├── README_ML.md            ← This file
│   │
│   ├── model.joblib            ← [Generated] Trained model
│   ├── scaler.joblib           ← [Generated] Fitted feature scaler
│   ├── features.json           ← [Generated] Feature column order
│   └── metrics.json            ← [Generated] Evaluation metrics
│
├── data/
│   ├── creditcard.csv          ← [Download from Kaggle] Real dataset
│   └── demo_transactions.csv   ← [Generated] Synthetic test data
│
├── app.py                      ← Flask API server
├── requirements.txt            ← Python dependencies
└── README.md                   ← Project documentation
```

---

## Quick Start (TL;DR)

```bash
# 1. Install dependencies
pip install scikit-learn pandas numpy joblib xgboost matplotlib

# 2. Train demo model (no data download needed)
python ml/train.py --demo

# 3. Verify model files were created
ls ml/*.joblib ml/*.json

# 4. Start Flask API
python app.py

# 5. Test prediction
curl -X POST http://localhost:5000/api/detect \
     -H "Content-Type: application/json" \
     -d '{"features": {"Time": 0, "V1": -1.36, "V2": -0.07, ..., "Amount": 149.62}}'
```

---

*FraudGuard AI ML Pipeline — Built with scikit-learn, XGBoost, and pandas*

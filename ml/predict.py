"""
FraudGuard AI - Prediction Utilities
======================================

This module handles loading saved models and making predictions on new transactions.
It is the bridge between the trained ML model and the Flask API.

The Flask API (app.py) imports this module to:
  1. Load model.joblib and scaler.joblib at startup
  2. Validate incoming transaction features
  3. Run predictions and return fraud probability + risk level

Usage (from Flask API):
    from predict import load_model, predict_single, determine_risk_level
    model, scaler = load_model("ml/model.joblib", "ml/scaler.joblib")
    result = predict_single(model, scaler, features_dict, feature_order)
"""

import os
import sys
import json

# ---------------------------------------------------------------------------
# Safe imports
# ---------------------------------------------------------------------------

try:
    import numpy as np
except ImportError:
    print("[ERROR] numpy is required: pip install numpy")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("[ERROR] pandas is required: pip install pandas")
    sys.exit(1)

try:
    import joblib
except ImportError:
    print("[ERROR] joblib is required: pip install joblib")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Risk Level Thresholds
# ---------------------------------------------------------------------------

# These thresholds determine how we communicate risk to the frontend.
# Tune these based on your business rules:
#   - Lower MEDIUM_THRESHOLD → fewer missed frauds, more false alarms
#   - Higher HIGH_THRESHOLD  → only flag very confident fraud cases
RISK_LOW_THRESHOLD    = 0.30   # Below 30% probability → Low risk
RISK_MEDIUM_THRESHOLD = 0.70   # 30-70% probability    → Medium risk
# Above 70%                   → High risk (likely fraud)


# ---------------------------------------------------------------------------
# Function 1: Load Saved Model and Scaler
# ---------------------------------------------------------------------------

def load_model(model_path, scaler_path):
    """
    Loads the trained model and fitted scaler from disk.

    Both files are created by train.py. This function should be called ONCE
    at server startup (not on every request) for performance.

    Args:
        model_path  (str): Absolute or relative path to model.joblib
        scaler_path (str): Absolute or relative path to scaler.joblib

    Returns:
        tuple: (model, scaler) — Both are loaded sklearn objects.

    Raises:
        FileNotFoundError : If either file doesn't exist.
        ValueError        : If loaded files aren't valid sklearn objects.

    Example:
        model, scaler = load_model("ml/model.joblib", "ml/scaler.joblib")
    """
    # ---- Validate paths ----
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            f"Run 'python ml/train.py --demo' to train a model first."
        )

    if not os.path.exists(scaler_path):
        raise FileNotFoundError(
            f"Scaler file not found: {scaler_path}\n"
            f"Run 'python ml/train.py --demo' to generate the scaler."
        )

    # ---- Load joblib files ----
    try:
        model = joblib.load(model_path)
    except Exception as e:
        raise ValueError(f"Failed to load model from {model_path}: {e}")

    try:
        scaler = joblib.load(scaler_path)
    except Exception as e:
        raise ValueError(f"Failed to load scaler from {scaler_path}: {e}")

    # ---- Basic sanity checks ----
    # Check model has predict and predict_proba (required for fraud probability)
    if not hasattr(model, 'predict'):
        raise ValueError("Loaded model doesn't have a predict() method.")
    if not hasattr(model, 'predict_proba'):
        raise ValueError(
            "Loaded model doesn't have predict_proba() method. "
            "Fraud probability requires probabilistic models."
        )
    if not hasattr(scaler, 'transform'):
        raise ValueError("Loaded scaler doesn't have a transform() method.")

    model_type = type(model).__name__
    print(f"  [Model Loaded] {model_type} from {model_path}")

    return model, scaler


# ---------------------------------------------------------------------------
# Function 2: Load Feature List
# ---------------------------------------------------------------------------

def load_feature_list(features_path):
    """
    Loads the ordered list of feature names saved during training.

    The feature order is critical — features must be passed to the model
    in the EXACT same order they were in during training.

    Args:
        features_path (str): Path to features.json.

    Returns:
        list: Ordered list of feature column names.

    Example:
        feature_order = load_feature_list("ml/features.json")
        # → ['Time', 'V1', 'V2', ..., 'V28', 'Amount']
    """
    if not os.path.exists(features_path):
        raise FileNotFoundError(
            f"Features file not found: {features_path}\n"
            f"Run 'python ml/train.py --demo' to generate it."
        )

    with open(features_path, 'r') as f:
        feature_list = json.load(f)

    if not isinstance(feature_list, list) or len(feature_list) == 0:
        raise ValueError(f"features.json must contain a non-empty list. Got: {feature_list}")

    return feature_list


# ---------------------------------------------------------------------------
# Function 3: Determine Risk Level
# ---------------------------------------------------------------------------

def determine_risk_level(probability):
    """
    Converts a raw fraud probability (0.0 to 1.0) into a human-readable risk level.

    This is what the frontend displays to users and analysts.

    Args:
        probability (float): Model's fraud probability output (0.0 to 1.0).

    Returns:
        str: 'Low', 'Medium', or 'High'

    Example:
        level = determine_risk_level(0.85)  # → 'High'
        level = determine_risk_level(0.45)  # → 'Medium'
        level = determine_risk_level(0.10)  # → 'Low'
    """
    if not 0.0 <= probability <= 1.0:
        raise ValueError(f"Probability must be between 0 and 1. Got: {probability}")

    if probability >= RISK_MEDIUM_THRESHOLD:
        return "High"
    elif probability >= RISK_LOW_THRESHOLD:
        return "Medium"
    else:
        return "Low"


# ---------------------------------------------------------------------------
# Function 4: Predict a Single Transaction
# ---------------------------------------------------------------------------

def predict_single(model, scaler, features_dict, feature_order):
    """
    Predicts fraud probability for a single transaction.

    This is called by the Flask API's /api/detect endpoint for real-time detection.

    Pipeline:
      1. Extract features in correct order from the input dict
      2. Scale using the pre-fitted scaler
      3. Run model.predict() and model.predict_proba()
      4. Return structured result with risk level

    Args:
        model         : Loaded sklearn model (from load_model()).
        scaler        : Loaded StandardScaler (from load_model()).
        features_dict : dict of {feature_name: value} for the transaction.
        feature_order : list of feature names in training order.

    Returns:
        dict: {
            "prediction"       : int   (0=legit, 1=fraud),
            "fraud_probability": float (0.0 to 1.0),
            "risk_level"       : str   ("Low", "Medium", "High"),
            "is_fraud"         : bool,
        }

    Raises:
        KeyError   : If a required feature is missing from features_dict.
        ValueError : If features_dict contains non-numeric values.

    Example:
        result = predict_single(model, scaler, {"V1": 1.2, "Amount": 50.0, ...}, feature_list)
        # → {"prediction": 1, "fraud_probability": 0.87, "risk_level": "High", "is_fraud": True}
    """
    # ---- Step 1: Build ordered feature vector ----
    # We must preserve the exact column order from training
    try:
        feature_values = [float(features_dict[feat]) for feat in feature_order]
    except KeyError as e:
        raise KeyError(f"Missing required feature: {e}. Expected features: {feature_order}")
    except (TypeError, ValueError) as e:
        raise ValueError(f"All feature values must be numeric. Error: {e}")

    # ---- Step 2: Reshape for sklearn (expects 2D array) ----
    # [[v1, v2, v3, ...]] — shape (1, n_features)
    X = np.array([feature_values])

    # ---- Step 3: Scale using the pre-fitted scaler ----
    # IMPORTANT: Use transform(), never fit_transform() here.
    # fit_transform() would re-learn scaling from this single sample — wrong!
    X_scaled = scaler.transform(X)

    # ---- Step 4: Make prediction ----
    prediction = int(model.predict(X_scaled)[0])

    # Fraud probability: column 1 of predict_proba output
    # Format: [[P(legit), P(fraud)]] — we want P(fraud)
    fraud_probability = float(model.predict_proba(X_scaled)[0][1])

    # ---- Step 5: Determine risk level ----
    risk_level = determine_risk_level(fraud_probability)

    return {
        "prediction"        : prediction,
        "fraud_probability" : round(fraud_probability, 6),
        "risk_level"        : risk_level,
        "is_fraud"          : bool(prediction == 1),
    }


# ---------------------------------------------------------------------------
# Function 5: Predict a Batch of Transactions
# ---------------------------------------------------------------------------

def predict_batch(model, scaler, df, feature_order):
    """
    Predicts fraud probability for a batch of transactions (DataFrame input).

    Used for:
      - The /api/batch-detect endpoint (CSV upload feature)
      - Offline scoring of historical transaction data
      - Demo data testing

    Args:
        model        : Loaded sklearn model.
        scaler       : Loaded StandardScaler.
        df           : pd.DataFrame containing transaction features.
        feature_order: list of feature column names in training order.

    Returns:
        pd.DataFrame: Original df with 3 new columns added:
            - 'prediction'        (int)   : 0=legit, 1=fraud
            - 'fraud_probability' (float) : Fraud confidence score
            - 'risk_level'        (str)   : 'Low', 'Medium', or 'High'

    Raises:
        ValueError: If any required feature columns are missing from df.

    Example:
        import pandas as pd
        df = pd.read_csv("transactions.csv")
        results_df = predict_batch(model, scaler, df, feature_order)
        fraud_cases = results_df[results_df['prediction'] == 1]
    """
    # ---- Validate all required columns are present ----
    missing_cols = [f for f in feature_order if f not in df.columns]
    if missing_cols:
        raise ValueError(
            f"DataFrame is missing required feature columns: {missing_cols}\n"
            f"Expected columns: {feature_order}"
        )

    # ---- Extract features in correct order ----
    X = df[feature_order].values.astype(float)

    # ---- Scale features ----
    X_scaled = scaler.transform(X)

    # ---- Batch predict ----
    predictions = model.predict(X_scaled)

    # predict_proba returns [[P(legit), P(fraud)], ...]
    # We take the second column for all rows: probabilities of fraud
    fraud_probs = model.predict_proba(X_scaled)[:, 1]

    # ---- Add results to a copy of the dataframe ----
    result_df = df.copy()
    result_df['prediction']         = predictions.astype(int)
    result_df['fraud_probability']  = np.round(fraud_probs, 6)
    result_df['risk_level']         = [determine_risk_level(p) for p in fraud_probs]

    # ---- Print summary ----
    n_total = len(result_df)
    n_fraud = result_df['prediction'].sum()
    n_high_risk = (result_df['risk_level'] == 'High').sum()

    print(f"  Batch Prediction Complete:")
    print(f"    Total transactions : {n_total:,}")
    print(f"    Predicted fraud    : {n_fraud:,}  ({n_fraud/n_total*100:.2f}%)")
    print(f"    High risk flagged  : {n_high_risk:,}")

    return result_df


# ---------------------------------------------------------------------------
# Function 6: Format Prediction for API Response
# ---------------------------------------------------------------------------

def format_api_response(prediction_result, transaction_id=None, amount=None):
    """
    Formats a prediction result dict into a clean API response object.

    This ensures consistent response format across all API endpoints.

    Args:
        prediction_result (dict): Output from predict_single().
        transaction_id    (str) : Optional transaction ID from request.
        amount            (float): Optional transaction amount.

    Returns:
        dict: Structured API response ready for JSON serialization.

    Example:
        response = format_api_response(result, transaction_id="TXN-001", amount=250.0)
    """
    response = {
        "status"            : "success",
        "prediction"        : prediction_result["prediction"],
        "is_fraud"          : prediction_result["is_fraud"],
        "fraud_probability" : prediction_result["fraud_probability"],
        "fraud_percentage"  : round(prediction_result["fraud_probability"] * 100, 2),
        "risk_level"        : prediction_result["risk_level"],
        "risk_color"        : {
            "Low"    : "#22c55e",   # Green
            "Medium" : "#f59e0b",   # Amber
            "High"   : "#ef4444",   # Red
        }.get(prediction_result["risk_level"], "#6b7280"),
        "message"           : (
            "⚠️  Fraudulent transaction detected — review required!"
            if prediction_result["is_fraud"]
            else "✅ Transaction appears legitimate."
        ),
    }

    # Add optional fields if provided
    if transaction_id:
        response["transaction_id"] = transaction_id
    if amount is not None:
        response["amount"] = amount

    return response


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    """
    Standalone test: Tests all functions with a dummy transaction.
    Requires model.joblib, scaler.joblib, and features.json to exist.
    Run 'python train.py --demo' first.
    """
    print("FraudGuard AI - Prediction Module Test")
    print("="*45)

    # Paths (assumes running from ml/ directory)
    MODEL_PATH   = os.path.join(os.path.dirname(__file__), "model.joblib")
    SCALER_PATH  = os.path.join(os.path.dirname(__file__), "scaler.joblib")
    FEATURES_PATH = os.path.join(os.path.dirname(__file__), "features.json")

    # Check if models exist
    if not all(os.path.exists(p) for p in [MODEL_PATH, SCALER_PATH, FEATURES_PATH]):
        print("\n[ERROR] Model files not found.")
        print("  Please run: python train.py --demo")
        print("  Then re-run this test.")
        sys.exit(1)

    # Load everything
    model, scaler = load_model(MODEL_PATH, SCALER_PATH)
    feature_order = load_feature_list(FEATURES_PATH)

    print(f"  Feature count: {len(feature_order)}")
    print(f"  Features: {feature_order[:5]}...{feature_order[-2:]}")

    # Create a dummy transaction with all features set to 0
    dummy_transaction = {feat: 0.0 for feat in feature_order}
    dummy_transaction['Amount'] = 150.0  # Set a realistic amount

    # Run prediction
    print("\n  Running prediction on dummy transaction...")
    result = predict_single(model, scaler, dummy_transaction, feature_order)

    print(f"\n  Prediction Result:")
    for key, val in result.items():
        print(f"    {key}: {val}")

    # Test risk levels
    print("\n  Risk Level Tests:")
    for prob in [0.05, 0.35, 0.75, 0.95]:
        level = determine_risk_level(prob)
        print(f"    P={prob:.2f} → {level}")

    print("\n  Module working correctly ✓")

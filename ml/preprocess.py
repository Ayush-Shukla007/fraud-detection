"""
FraudGuard AI - Preprocessing Utilities
=========================================

This module provides reusable preprocessing functions used during:
  - Training     : fit_scaler=True to learn scaling parameters
  - Inference    : fit_scaler=False to only transform using saved scaler
  - Validation   : validate_transaction_input() checks API payloads

These functions are imported by train.py and the Flask API (app.py).
"""

import os
import sys
import json

# ---------------------------------------------------------------------------
# Safe imports
# ---------------------------------------------------------------------------

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("[ERROR] pandas and numpy are required: pip install pandas numpy")
    sys.exit(1)

try:
    from sklearn.preprocessing import StandardScaler
except ImportError:
    print("[ERROR] scikit-learn is required: pip install scikit-learn")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Function 1: Load and Inspect Dataset
# ---------------------------------------------------------------------------

def load_and_inspect(filepath):
    """
    Loads a CSV dataset and prints a detailed inspection report.

    This is a diagnostic function — use it first to understand your data
    before preprocessing or training.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded DataFrame, or None if file not found.

    Example:
        df = load_and_inspect("../data/creditcard.csv")
    """
    print("\n" + "="*55)
    print("  Dataset Inspection")
    print("="*55)

    # Check file existence before attempting to load
    if not os.path.exists(filepath):
        print(f"  [ERROR] File not found: {filepath}")
        return None

    # Load CSV into DataFrame
    df = pd.read_csv(filepath)

    # ---- Basic info ----
    print(f"  File          : {filepath}")
    print(f"  Shape         : {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Memory usage  : {df.memory_usage(deep=True).sum() / 1e6:.2f} MB")

    # ---- Column types ----
    print(f"\n  Column Data Types:")
    type_counts = df.dtypes.value_counts()
    for dtype, count in type_counts.items():
        print(f"    {str(dtype):<12}: {count} columns")

    # ---- Missing values ----
    print(f"\n  Missing Values:")
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]
    if len(missing_cols) == 0:
        print("    None ✓")
    else:
        for col, count in missing_cols.items():
            print(f"    {col}: {count} missing ({count/len(df)*100:.2f}%)")

    # ---- Class distribution (if 'Class' column exists) ----
    if 'Class' in df.columns:
        print(f"\n  Class Distribution (Target Column):")
        counts = df['Class'].value_counts().sort_index()
        for cls, count in counts.items():
            label = "Legitimate" if cls == 0 else "Fraud"
            pct = count / len(df) * 100
            print(f"    Class {cls} ({label:>10}): {count:>8,}  ({pct:.4f}%)")
    else:
        print("\n  [WARNING] No 'Class' column found — is this labelled data?")

    # ---- Feature statistics (sample) ----
    print(f"\n  Numeric Feature Statistics (first 5 features):")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    sample_cols = numeric_cols[:5]
    stats = df[sample_cols].describe().round(4)
    print(stats.to_string(col_space=12))

    print("\n" + "="*55)

    return df


# ---------------------------------------------------------------------------
# Function 2: Preprocess Features
# ---------------------------------------------------------------------------

def preprocess_features(df, feature_columns, scaler=None, fit_scaler=False):
    """
    Extracts feature columns and applies StandardScaler normalization.

    WHY StandardScaler?
    - It removes the mean and scales to unit variance.
    - 'Time' ranges 0–172,792 seconds; 'Amount' ranges 0–25,691.
    - V1-V28 are already PCA-transformed (mostly normalized), but scaling still helps.
    - Logistic Regression and neural networks require scaled input.
    - Tree models (RF, XGBoost) are less sensitive but can still benefit.

    Args:
        df              (pd.DataFrame) : Input DataFrame.
        feature_columns (list)         : List of column names to use as features.
        scaler          (StandardScaler or None): Pre-fitted scaler. If None, one is created.
        fit_scaler      (bool)         : If True, fit the scaler on this data (training mode).
                                         If False, only transform (inference mode).

    Returns:
        tuple: (X_scaled np.array, fitted_scaler StandardScaler)

    Example (training):
        X_scaled, scaler = preprocess_features(df_train, cols, fit_scaler=True)

    Example (inference):
        X_scaled, _ = preprocess_features(df_new, cols, scaler=loaded_scaler, fit_scaler=False)
    """
    # Validate all expected columns exist in the dataframe
    missing_cols = [c for c in feature_columns if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing columns in DataFrame: {missing_cols}\n"
            f"Available columns: {list(df.columns)}"
        )

    # Extract feature matrix
    X = df[feature_columns].values

    # Create a new scaler if none provided
    if scaler is None:
        scaler = StandardScaler()

    if fit_scaler:
        # Training mode: learn scaling parameters from this data
        X_scaled = scaler.fit_transform(X)
    else:
        # Inference mode: apply pre-learned parameters only
        # This prevents data leakage from test/live data
        X_scaled = scaler.transform(X)

    return X_scaled, scaler


# ---------------------------------------------------------------------------
# Function 3: Validate Single Transaction Input
# ---------------------------------------------------------------------------

def validate_transaction_input(features_dict, expected_features):
    """
    Validates a single transaction's feature dictionary before prediction.

    This is the FIRST check run when the API receives a prediction request.
    It ensures the input has all required fields and reasonable numeric values.

    Args:
        features_dict    (dict): Input from API/user, e.g. {"V1": 1.2, "Amount": 50.0, ...}
        expected_features (list): Ordered list of expected feature names (from features.json).

    Returns:
        tuple: (is_valid: bool, error_message: str or None, cleaned_dict: dict or None)

    Example:
        is_valid, error, cleaned = validate_transaction_input(data, feature_list)
        if not is_valid:
            return {"error": error}, 400
    """
    errors = []
    cleaned = {}

    # ---- Check for missing features ----
    missing = [f for f in expected_features if f not in features_dict]
    if missing:
        errors.append(f"Missing required features: {missing}")

    # ---- Check for extra/unexpected features (warn, don't fail) ----
    extra = [f for f in features_dict if f not in expected_features]
    # We don't error on extra fields — just ignore them silently

    # ---- Validate each expected feature ----
    for feature in expected_features:
        if feature not in features_dict:
            continue  # Already captured in missing list above

        value = features_dict[feature]

        # Must be numeric (int or float, not string)
        if not isinstance(value, (int, float)):
            try:
                value = float(value)  # Try to coerce string numbers
            except (TypeError, ValueError):
                errors.append(f"Feature '{feature}' must be numeric, got: {type(value).__name__}")
                continue

        # Check for NaN/Infinity
        if not np.isfinite(value):
            errors.append(f"Feature '{feature}' contains non-finite value: {value}")
            continue

        # Sanity check for Amount (must be non-negative)
        if feature == 'Amount' and value < 0:
            errors.append(f"'Amount' cannot be negative, got: {value}")
            continue

        # Sanity check for Time (must be non-negative)
        if feature == 'Time' and value < 0:
            errors.append(f"'Time' cannot be negative, got: {value}")
            continue

        cleaned[feature] = float(value)

    if errors:
        return False, " | ".join(errors), None

    return True, None, cleaned


# ---------------------------------------------------------------------------
# Function 4: Get Feature Columns
# ---------------------------------------------------------------------------

def get_feature_columns(df):
    """
    Returns the list of feature column names (all columns except 'Class').

    This works for both the real Kaggle dataset (Time, V1-V28, Amount)
    and the synthetic demo dataset.

    Args:
        df (pd.DataFrame): The full dataset including target column.

    Returns:
        list: Ordered list of feature column names.

    Example:
        feature_cols = get_feature_columns(df)
        # → ['Time', 'V1', 'V2', ..., 'V28', 'Amount']
    """
    # Exclude 'Class' (target) and any other non-feature columns
    non_feature_cols = {'Class', 'class', 'label', 'Label', 'target', 'Target'}
    feature_columns = [col for col in df.columns if col not in non_feature_cols]

    return feature_columns


# ---------------------------------------------------------------------------
# Function 5: Convert Single Dict to DataFrame Row
# ---------------------------------------------------------------------------

def dict_to_dataframe(features_dict, feature_order):
    """
    Converts a single prediction request dictionary into a properly ordered DataFrame row.

    WHY: The model expects features in the exact same order they were trained on.
    This function guarantees the correct column ordering regardless of dict key order.

    Args:
        features_dict (dict): Feature name → value mapping.
        feature_order (list): Exact ordered list of feature names.

    Returns:
        pd.DataFrame: Single-row DataFrame ready for model.predict().

    Example:
        df_row = dict_to_dataframe({"Amount": 50.0, "V1": 1.2, ...}, feature_list)
    """
    # Create a single-row DataFrame with columns in training order
    row = {feature: [features_dict.get(feature, 0.0)] for feature in feature_order}
    return pd.DataFrame(row)


# ---------------------------------------------------------------------------
# Standalone usage: print info if run directly
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("FraudGuard AI - Preprocessing Module")
    print("This module is designed to be imported, not run directly.")
    print()
    print("Available functions:")
    print("  load_and_inspect(filepath)")
    print("  preprocess_features(df, feature_columns, scaler, fit_scaler)")
    print("  validate_transaction_input(features_dict, expected_features)")
    print("  get_feature_columns(df)")
    print("  dict_to_dataframe(features_dict, feature_order)")
    print()
    print("Example:")
    print("  from preprocess import load_and_inspect, get_feature_columns")
    print("  df = load_and_inspect('../data/creditcard.csv')")
    print("  cols = get_feature_columns(df)")

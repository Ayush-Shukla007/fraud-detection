"""
FraudGuard AI - Model Training Script
======================================

This script trains a Credit Card Fraud Detection model using multiple algorithms
and automatically selects the best-performing one based on ROC-AUC score.

Dataset expected: CSV with columns [Time, V1-V28, Amount, Class]
(Standard Kaggle Credit Card Fraud Detection dataset format)
Download: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

Usage:
    python train.py --data ../data/creditcard.csv
    python train.py --data ../data/creditcard.csv --model xgboost
    python train.py --demo  # Creates a demo model with synthetic data

Outputs (saved to ml/ directory):
    model.joblib    - The best trained model
    scaler.joblib   - Fitted StandardScaler for feature normalization
    features.json   - Ordered list of feature column names
    metrics.json    - Full evaluation metrics of the best model
"""

import os
import sys
import json
import argparse
import warnings
import numpy as np

warnings.filterwarnings("ignore")  # Suppress sklearn convergence warnings for cleaner output

# ---------------------------------------------------------------------------
# Safe imports with fallback messages
# ---------------------------------------------------------------------------

try:
    import pandas as pd
except ImportError:
    print("[ERROR] pandas is required. Install it with: pip install pandas")
    sys.exit(1)

try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score,
        f1_score, roc_auc_score, confusion_matrix
    )
    from sklearn.datasets import make_classification
except ImportError:
    print("[ERROR] scikit-learn is required. Install it with: pip install scikit-learn")
    sys.exit(1)

try:
    import joblib
except ImportError:
    print("[ERROR] joblib is required. Install it with: pip install joblib")
    sys.exit(1)

# XGBoost is optional — we gracefully fall back to Random Forest if not available
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("[WARNING] XGBoost not installed. XGBoost option will fall back to Random Forest.")
    print("          To install: pip install xgboost")

# SMOTE is optional — we use class_weight='balanced' if not available
try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False
    # This is fine — we handle imbalance via class_weight instead


# ---------------------------------------------------------------------------
# Utility: Pretty print a separator
# ---------------------------------------------------------------------------

def print_section(title):
    """Prints a clean section separator for console output."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# Step 1: Data Loading
# ---------------------------------------------------------------------------

def load_data(filepath):
    """
    Loads the CSV dataset and performs basic inspection.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded dataset.
    """
    print_section("Loading Dataset")

    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        print("        Run with --demo to train on synthetic data instead.")
        sys.exit(1)

    print(f"  Reading: {filepath}")
    df = pd.read_csv(filepath)

    print(f"  Shape:   {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Memory:  {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

    # Check for missing values
    missing = df.isnull().sum().sum()
    if missing > 0:
        print(f"  [WARNING] Found {missing} missing values — will drop those rows.")
        df = df.dropna()
    else:
        print("  Missing values: None ✓")

    # Verify required 'Class' column exists
    if 'Class' not in df.columns:
        print("[ERROR] Dataset must contain a 'Class' column (0=legitimate, 1=fraud).")
        sys.exit(1)

    return df


# ---------------------------------------------------------------------------
# Step 2: Class Distribution Analysis
# ---------------------------------------------------------------------------

def show_class_distribution(y):
    """
    Displays the class distribution, which is critical for fraud datasets.
    Credit card fraud data is highly imbalanced (~0.17% fraud).

    Args:
        y (pd.Series): Target column.
    """
    print_section("Class Distribution")

    counts = y.value_counts().sort_index()
    total = len(y)

    for cls, count in counts.items():
        label = "Legitimate" if cls == 0 else "Fraud    "
        pct = count / total * 100
        bar = "█" * int(pct / 2)  # Visual bar (max 50 chars for 100%)
        print(f"  Class {cls} ({label}): {count:>7,}  ({pct:5.2f}%)  {bar}")

    # Calculate imbalance ratio — useful for setting scale_pos_weight in XGBoost
    fraud_count = counts.get(1, 0)
    legit_count = counts.get(0, 0)
    if fraud_count > 0:
        ratio = legit_count / fraud_count
        print(f"\n  Imbalance ratio (legit:fraud): {ratio:.0f}:1")
        print(f"  scale_pos_weight for XGBoost : {ratio:.1f}")

    return counts


# ---------------------------------------------------------------------------
# Step 3: Feature Preparation
# ---------------------------------------------------------------------------

def prepare_features(df):
    """
    Separates features (X) and target (y), and returns feature column names.

    The standard Kaggle dataset has 30 features: Time, V1-V28, Amount.
    All of them are kept — PCA-transformed V1-V28 are already anonymized.

    Args:
        df (pd.DataFrame): Full dataset.

    Returns:
        tuple: (X, y, feature_columns)
    """
    print_section("Feature Preparation")

    # All columns except 'Class' are features
    feature_columns = [col for col in df.columns if col != 'Class']
    X = df[feature_columns].values
    y = df['Class'].values

    print(f"  Features : {len(feature_columns)} columns")
    print(f"  Samples  : {X.shape[0]:,}")
    print(f"  Feature list: {feature_columns[:5]}...{feature_columns[-2:]}")

    return X, y, feature_columns


# ---------------------------------------------------------------------------
# Step 4: Feature Scaling
# ---------------------------------------------------------------------------

def scale_features(X_train, X_test, save_path="scaler.joblib"):
    """
    Applies StandardScaler to normalize features.

    WHY: Models like Logistic Regression are sensitive to feature scale.
    Even tree-based models can benefit from scaling in some cases.
    We fit ONLY on training data to prevent data leakage.

    Args:
        X_train (np.array): Training features.
        X_test  (np.array): Test features.
        save_path (str)   : Where to save the fitted scaler.

    Returns:
        tuple: (X_train_scaled, X_test_scaled, scaler)
    """
    print_section("Feature Scaling")

    scaler = StandardScaler()

    # Fit on training data only — never fit on test data (data leakage!)
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)  # Only transform, don't re-fit

    # Save scaler so the API can use it for live predictions
    joblib.dump(scaler, save_path)
    print(f"  Scaler fitted and saved → {save_path}")
    print(f"  Mean range : [{scaler.mean_.min():.3f}, {scaler.mean_.max():.3f}]")

    return X_train_scaled, X_test_scaled, scaler


# ---------------------------------------------------------------------------
# Step 5: Handle Class Imbalance
# ---------------------------------------------------------------------------

def handle_imbalance(X_train, y_train, method="class_weight"):
    """
    Handles class imbalance in the training set.

    WHY: Fraud data is severely imbalanced (~0.17% fraud). Without handling
    this, models learn to just predict 'not fraud' and get 99.8% accuracy
    while being completely useless at catching fraud.

    Methods:
      - class_weight (default): Handled inside model constructors — simpler.
      - smote: Synthetic Minority Over-sampling Technique — generates synthetic
               fraud samples to balance the dataset before training.

    Args:
        X_train (np.array): Training features.
        y_train (np.array): Training labels.
        method  (str)     : 'class_weight' or 'smote'.

    Returns:
        tuple: (X_resampled, y_resampled)
    """
    print_section("Class Imbalance Handling")

    if method == "smote" and SMOTE_AVAILABLE:
        print("  Using SMOTE to oversample minority (fraud) class...")
        smote = SMOTE(random_state=42, k_neighbors=5)
        X_res, y_res = smote.fit_resample(X_train, y_train)
        new_counts = np.bincount(y_res)
        print(f"  After SMOTE — Legit: {new_counts[0]:,} | Fraud: {new_counts[1]:,}")
        return X_res, y_res
    else:
        if method == "smote" and not SMOTE_AVAILABLE:
            print("  SMOTE requested but imbalanced-learn not installed.")
            print("  Falling back to class_weight='balanced' inside models.")
        else:
            print("  Using class_weight='balanced' (built into model constructors).")
        print("  This approach penalizes misclassifying the minority class more heavily.")
        return X_train, y_train  # No resampling — weights handled in models


# ---------------------------------------------------------------------------
# Step 6: Model Definitions
# ---------------------------------------------------------------------------

def build_models(imbalance_ratio=578):
    """
    Builds a dictionary of models to train and compare.

    WHY these 3 models?
    - LogisticRegression : Fast baseline, interpretable, works well on scaled data.
    - RandomForest        : Ensemble of trees, robust to outliers, handles non-linearity.
    - XGBoost             : Gradient boosted trees, state-of-the-art for tabular data.

    Args:
        imbalance_ratio (float): ratio of legit:fraud (for XGBoost scale_pos_weight).

    Returns:
        dict: Model name → model object.
    """
    models = {
        "LogisticRegression": LogisticRegression(
            class_weight='balanced',   # Upweights fraud samples in loss function
            max_iter=1000,             # Ensure convergence on scaled data
            solver='lbfgs',
            random_state=42
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=100,          # 100 decision trees in the ensemble
            class_weight='balanced',   # Each tree respects class weights
            random_state=42,
            n_jobs=-1                  # Use all CPU cores for speed
        ),
    }

    # Add XGBoost if available, otherwise use a second Random Forest config
    if XGBOOST_AVAILABLE:
        models["XGBoost"] = XGBClassifier(
            n_estimators=100,
            scale_pos_weight=imbalance_ratio,  # Key param for imbalanced data
            learning_rate=0.1,
            max_depth=6,
            random_state=42,
            eval_metric='logloss',
            verbosity=0               # Suppress XGBoost training output
        )
    else:
        print("  [INFO] XGBoost unavailable — using GradientBoosting placeholder entry.")

    return models


# ---------------------------------------------------------------------------
# Step 7: Evaluation
# ---------------------------------------------------------------------------

def evaluate_model(model, X_test, y_test, model_name="Model"):
    """
    Evaluates a trained model using multiple metrics.

    WHY multiple metrics?
    - Accuracy alone is misleading on imbalanced data (99.8% by just predicting 'legit').
    - Precision: Of predicted frauds, how many are real?
    - Recall   : Of actual frauds, how many did we catch? (MOST IMPORTANT for fraud)
    - F1       : Harmonic mean of precision + recall.
    - ROC-AUC  : Overall discrimination ability — best for model comparison.

    Args:
        model     : Trained sklearn-compatible model.
        X_test    : Test features.
        y_test    : True labels.
        model_name: Display name for printing.

    Returns:
        dict: All evaluation metrics.
    """
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]  # Probability of fraud (class 1)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    results = {
        "model_name"      : model_name,
        "accuracy"        : round(accuracy_score(y_test, y_pred), 6),
        "precision"       : round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall"          : round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score"        : round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc"         : round(roc_auc_score(y_test, y_prob), 6),
        "confusion_matrix": {"tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn)},
    }

    return results


# ---------------------------------------------------------------------------
# Step 8: Results Display
# ---------------------------------------------------------------------------

def print_results_table(all_results):
    """
    Prints a clean comparison table of all trained models.

    Args:
        all_results (list): List of evaluation result dicts.
    """
    print_section("Model Comparison Results")

    header = f"  {'Model':<22} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>8} {'ROC-AUC':>9}"
    print(header)
    print("  " + "-" * 70)

    for r in all_results:
        row = (
            f"  {r['model_name']:<22}"
            f" {r['accuracy']:>9.4f}"
            f" {r['precision']:>10.4f}"
            f" {r['recall']:>8.4f}"
            f" {r['f1_score']:>8.4f}"
            f" {r['roc_auc']:>9.6f}"
        )
        print(row)

    # Highlight best model
    best = max(all_results, key=lambda r: r['roc_auc'])
    print(f"\n  ✓ Best model by ROC-AUC: {best['model_name']} ({best['roc_auc']:.6f})")


# ---------------------------------------------------------------------------
# Demo Mode: Synthetic Data Generator
# ---------------------------------------------------------------------------

def generate_demo_data(n_samples=10000, fraud_fraction=0.02):
    """
    Generates synthetic fraud-like data using sklearn's make_classification.

    WHY: Allows the full pipeline to be tested without downloading the Kaggle dataset.
    The synthetic data mimics the statistical properties of real fraud data (imbalanced,
    continuous features) but is NOT real financial data.

    Args:
        n_samples       (int)  : Total number of synthetic transactions.
        fraud_fraction  (float): Fraction of fraudulent transactions (~2%).

    Returns:
        tuple: (X, y, feature_columns)
    """
    print_section("Demo Mode — Generating Synthetic Data")

    n_fraud = int(n_samples * fraud_fraction)
    n_legit = n_samples - n_fraud

    print(f"  Generating {n_samples:,} transactions:")
    print(f"    Legitimate : {n_legit:,}")
    print(f"    Fraud      : {n_fraud:,}")

    # make_classification creates a realistic multi-feature classification dataset
    # weights parameter controls class imbalance ratio
    X, y = make_classification(
        n_samples=n_samples,
        n_features=30,          # Matches real dataset (Time + V1-V28 + Amount)
        n_informative=15,       # 15 features actually carry signal
        n_redundant=5,          # 5 are linear combos of informative features
        n_repeated=0,
        n_classes=2,
        weights=[1 - fraud_fraction, fraud_fraction],  # Class imbalance
        flip_y=0.01,            # 1% label noise (realistic)
        random_state=42
    )

    # Create column names matching the real dataset structure
    feature_columns = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount']

    print(f"  Synthetic data generated ✓  Shape: {X.shape}")
    print("  NOTE: This is synthetic data for demo purposes only.")
    print("        For production accuracy, use the real Kaggle dataset.")

    return X, y, feature_columns


# ---------------------------------------------------------------------------
# Main Training Pipeline
# ---------------------------------------------------------------------------

def train_pipeline(args):
    """
    Main orchestration function — runs the full training pipeline.

    Args:
        args: Parsed argparse arguments.
    """
    is_demo = args.demo
    output_dir = os.path.dirname(os.path.abspath(__file__))  # Save to ml/ directory

    print_section("FraudGuard AI - Training Pipeline")
    print(f"  Mode  : {'DEMO (synthetic data)' if is_demo else 'REAL DATA'}")
    print(f"  Model : {args.model.upper() if not is_demo else 'ALL (best selected)'}")
    print(f"  Output: {output_dir}")

    # ---- Data Loading ----
    if is_demo:
        X, y, feature_columns = generate_demo_data(n_samples=10000)
        training_samples = len(X)
    else:
        df = load_data(args.data)
        X, y, feature_columns = prepare_features(df)
        training_samples = len(X)

    # ---- Class Distribution ----
    y_series = pd.Series(y)
    counts = show_class_distribution(y_series)

    fraud_count = counts.get(1, 1)
    legit_count = counts.get(0, 1)
    imbalance_ratio = legit_count / fraud_count

    # ---- Train/Test Split ----
    print_section("Train / Test Split")

    # stratify=y ensures both splits have the same fraud ratio — critical for imbalanced data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y          # Preserves class ratio in both splits
    )

    print(f"  Training set : {X_train.shape[0]:,} samples")
    print(f"  Test set     : {X_test.shape[0]:,} samples")
    print(f"  Fraud in test: {y_test.sum():,} ({y_test.mean()*100:.2f}%)")

    # ---- Feature Scaling ----
    scaler_path = os.path.join(output_dir, "scaler.joblib")
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test, scaler_path)

    # ---- Imbalance Handling ----
    X_train_final, y_train_final = handle_imbalance(
        X_train_scaled, y_train,
        method="smote" if SMOTE_AVAILABLE else "class_weight"
    )

    # ---- Build Models ----
    print_section("Training Models")
    models = build_models(imbalance_ratio=imbalance_ratio)

    # If user requested a specific model, only train that one (+ always include RF as fallback)
    if not is_demo and args.model != "all":
        model_map = {
            "logistic"      : "LogisticRegression",
            "random_forest" : "RandomForest",
            "xgboost"       : "XGBoost" if XGBOOST_AVAILABLE else "RandomForest"
        }
        selected = model_map.get(args.model, "RandomForest")
        models = {selected: models[selected]}

    # ---- Train & Evaluate All Models ----
    all_results = []

    for name, model in models.items():
        print(f"\n  Training {name}...")
        model.fit(X_train_final, y_train_final)
        print(f"  Evaluating {name}...")
        result = evaluate_model(model, X_test_scaled, y_test, model_name=name)
        result['_model_object'] = model  # Temporarily store model object for selection
        all_results.append(result)
        print(f"    ROC-AUC: {result['roc_auc']:.4f}  |  Recall: {result['recall']:.4f}  |  F1: {result['f1_score']:.4f}")

    # ---- Results Table ----
    display_results = [{k: v for k, v in r.items() if k != '_model_object'} for r in all_results]
    print_results_table(display_results)

    # ---- Select Best Model by ROC-AUC ----
    best_result = max(all_results, key=lambda r: r['roc_auc'])
    best_model = best_result.pop('_model_object')  # Extract model object

    # Clean up model objects from other results too
    for r in all_results:
        r.pop('_model_object', None)

    # ---- Save Best Model ----
    print_section("Saving Outputs")

    model_path = os.path.join(output_dir, "model.joblib")
    joblib.dump(best_model, model_path)
    print(f"  Best model saved   → {model_path}")

    # ---- Save Features List ----
    features_path = os.path.join(output_dir, "features.json")
    with open(features_path, 'w') as f:
        json.dump(feature_columns, f, indent=2)
    print(f"  Feature list saved → {features_path}")

    # ---- Build & Save Metrics ----
    metrics = {
        **best_result,
        "training_samples" : int(X_train.shape[0]),
        "test_samples"     : int(X_test.shape[0]),
        "features_used"    : feature_columns,
        "is_demo"          : is_demo,
        "all_model_results": display_results
    }

    metrics_path = os.path.join(output_dir, "metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"  Metrics saved      → {metrics_path}")

    # ---- Final Summary ----
    print_section("Training Complete ✓")
    print(f"  Best Model : {best_result['model_name']}")
    print(f"  ROC-AUC    : {best_result['roc_auc']:.6f}")
    print(f"  Recall     : {best_result['recall']:.4f}  (fraud detection rate)")
    print(f"  Precision  : {best_result['precision']:.4f}  (of flagged, how many are real fraud)")
    print(f"  F1 Score   : {best_result['f1_score']:.4f}")
    print()
    print(f"  Files saved to: {output_dir}")
    print(f"    model.joblib   → {model_path}")
    print(f"    scaler.joblib  → {scaler_path}")
    print(f"    features.json  → {features_path}")
    print(f"    metrics.json   → {metrics_path}")
    print()
    if is_demo:
        print("  [NOTE] This model was trained on SYNTHETIC data.")
        print("         For production use, train with the real Kaggle dataset.")
    print()

    return metrics


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="FraudGuard AI — Credit Card Fraud Detection Training Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python train.py --demo
  python train.py --data ../data/creditcard.csv
  python train.py --data ../data/creditcard.csv --model xgboost
  python train.py --data ../data/creditcard.csv --model logistic
        """
    )

    parser.add_argument(
        '--data',
        type=str,
        default=None,
        help='Path to the CSV dataset (required unless --demo is used)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='all',
        choices=['logistic', 'random_forest', 'xgboost', 'all'],
        help='Model to train (default: all — trains all and picks best)'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode with synthetic data (no dataset needed)'
    )

    args = parser.parse_args()

    # Validate: either --demo or --data must be provided
    if not args.demo and args.data is None:
        print("[ERROR] You must provide either --demo or --data <path_to_csv>")
        print("        Run: python train.py --help  for usage details.")
        sys.exit(1)

    train_pipeline(args)


if __name__ == '__main__':
    main()

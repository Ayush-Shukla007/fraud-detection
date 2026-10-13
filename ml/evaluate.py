"""
FraudGuard AI - Evaluation Utilities
======================================

This module provides functions to evaluate and compare ML models for fraud detection.
All functions return results as dictionaries so they can be used both for display
and for saving to metrics.json.

Imported by train.py. Can also be used standalone for re-evaluating saved models.

Usage:
    from evaluate import evaluate_model, compare_models, plot_confusion_matrix
"""

import os
import sys
import json
import warnings

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Safe imports
# ---------------------------------------------------------------------------

try:
    import numpy as np
except ImportError:
    print("[ERROR] numpy is required: pip install numpy")
    sys.exit(1)

try:
    from sklearn.metrics import (
        accuracy_score,
        precision_score,
        recall_score,
        f1_score,
        roc_auc_score,
        confusion_matrix,
        classification_report,
        roc_curve,
        auc,
    )
except ImportError:
    print("[ERROR] scikit-learn is required: pip install scikit-learn")
    sys.exit(1)

# Matplotlib is optional — skip plotting if not installed or no display
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend: works in headless environments (servers)
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("[INFO] matplotlib not installed — plots will be skipped.")
    print("       To enable plots: pip install matplotlib")


# ---------------------------------------------------------------------------
# Function 1: Evaluate a Single Model
# ---------------------------------------------------------------------------

def evaluate_model(model, X_test, y_test, model_name="Model"):
    """
    Evaluates a trained model on test data using comprehensive metrics.

    For fraud detection, we care most about:
    - Recall    : Are we catching the actual fraud cases? (False Negatives are costly)
    - Precision : Are our fraud alerts accurate? (False Positives annoy customers)
    - ROC-AUC   : Overall discrimination power (threshold-independent)
    - F1 Score  : Balance between precision and recall

    Args:
        model      : Any trained sklearn-compatible model with predict() and predict_proba().
        X_test     : Test feature matrix (already scaled).
        y_test     : True labels (0=legit, 1=fraud).
        model_name : Human-readable name for display.

    Returns:
        dict: {
            "model_name", "accuracy", "precision", "recall", "f1_score",
            "roc_auc", "confusion_matrix": {"tp", "tn", "fp", "fn"}
        }

    Example:
        results = evaluate_model(rf_model, X_test, y_test, "RandomForest")
        print(f"Recall: {results['recall']}")
    """
    # Generate predictions and probabilities
    y_pred = model.predict(X_test)

    # predict_proba returns [[P(class0), P(class1)], ...]
    # We take [:, 1] for the fraud probability — used for ROC-AUC calculation
    y_prob = model.predict_proba(X_test)[:, 1]

    # Compute confusion matrix components
    # Layout: [[TN, FP], [FN, TP]]  (sklearn convention)
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    results = {
        "model_name"       : model_name,
        "accuracy"         : round(float(accuracy_score(y_test, y_pred)), 6),
        "precision"        : round(float(precision_score(y_test, y_pred, zero_division=0)), 6),
        "recall"           : round(float(recall_score(y_test, y_pred, zero_division=0)), 6),
        "f1_score"         : round(float(f1_score(y_test, y_pred, zero_division=0)), 6),
        "roc_auc"          : round(float(roc_auc_score(y_test, y_prob)), 6),
        "confusion_matrix" : {
            "tp": int(tp),  # True Positives  — Fraud correctly detected
            "tn": int(tn),  # True Negatives  — Legit correctly passed
            "fp": int(fp),  # False Positives — Legit incorrectly flagged (customer friction)
            "fn": int(fn),  # False Negatives — Fraud missed! (most dangerous)
        },
    }

    return results


# ---------------------------------------------------------------------------
# Function 2: Print Detailed Classification Report
# ---------------------------------------------------------------------------

def print_detailed_report(model, X_test, y_test, model_name="Model"):
    """
    Prints sklearn's full classification report including per-class metrics.

    Useful for a deeper dive into model performance beyond summary metrics.

    Args:
        model      : Trained model.
        X_test     : Test features.
        y_test     : True labels.
        model_name : Model name for display.
    """
    y_pred = model.predict(X_test)

    print(f"\n  Classification Report — {model_name}")
    print("  " + "-"*55)

    report = classification_report(
        y_test, y_pred,
        target_names=["Legitimate (0)", "Fraud (1)"],
        zero_division=0
    )

    # Indent each line for cleaner console output
    for line in report.split('\n'):
        print(f"    {line}")

    # Confusion matrix in readable format
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    print(f"\n  Confusion Matrix:")
    print(f"    {'':30} Predicted Legit  Predicted Fraud")
    print(f"    {'Actual Legit':30}  {tn:>14,}  {fp:>14,}")
    print(f"    {'Actual Fraud':30}  {fn:>14,}  {tp:>14,}")
    print()
    print(f"    → Fraud Caught (True Positives)  : {tp:,}")
    print(f"    → Fraud Missed (False Negatives) : {fn:,}  ← Most costly!")
    print(f"    → False Alarms (False Positives) : {fp:,}  ← Customer friction")


# ---------------------------------------------------------------------------
# Function 3: Plot Confusion Matrix
# ---------------------------------------------------------------------------

def plot_confusion_matrix(cm, save_path, model_name="Model"):
    """
    Creates and saves a visual confusion matrix heatmap.

    Skips gracefully if matplotlib is not available or running headless.

    Args:
        cm         : Confusion matrix array (from sklearn.metrics.confusion_matrix).
                     Can also be the dict format {"tp", "tn", "fp", "fn"}.
        save_path  : Absolute path where the PNG image should be saved.
        model_name : Used in the plot title.

    Returns:
        bool: True if saved successfully, False if skipped.

    Example:
        cm = confusion_matrix(y_test, y_pred)
        plot_confusion_matrix(cm, "ml/confusion_matrix.png", "RandomForest")
    """
    if not MATPLOTLIB_AVAILABLE:
        print("  [SKIP] Confusion matrix plot skipped — matplotlib not installed.")
        return False

    try:
        # Handle both numpy array and dict formats
        if isinstance(cm, dict):
            tn, fp = cm['tn'], cm['fp']
            fn, tp = cm['fn'], cm['tp']
            cm_array = np.array([[tn, fp], [fn, tp]])
        else:
            cm_array = np.array(cm)
            tn, fp, fn, tp = cm_array.ravel()

        fig, ax = plt.subplots(figsize=(6, 5))

        # Use a diverging colormap — high values in corners, low in anti-diagonal
        im = ax.imshow(cm_array, interpolation='nearest', cmap=plt.cm.Blues)
        plt.colorbar(im, ax=ax)

        # Labels
        classes = ['Legitimate (0)', 'Fraud (1)']
        tick_marks = np.arange(len(classes))
        ax.set_xticks(tick_marks)
        ax.set_xticklabels(classes, rotation=30, ha='right')
        ax.set_yticks(tick_marks)
        ax.set_yticklabels(classes)

        # Add text annotations inside each cell
        thresh = cm_array.max() / 2.0
        for i in range(cm_array.shape[0]):
            for j in range(cm_array.shape[1]):
                value = cm_array[i, j]
                ax.text(
                    j, i, f"{value:,}",
                    ha='center', va='center',
                    color='white' if value > thresh else 'black',
                    fontsize=12, fontweight='bold'
                )

        ax.set_ylabel('Actual Label', fontsize=12)
        ax.set_xlabel('Predicted Label', fontsize=12)
        ax.set_title(f'Confusion Matrix — {model_name}', fontsize=13, pad=15)

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"  Confusion matrix saved → {save_path}")
        return True

    except Exception as e:
        print(f"  [WARNING] Could not save confusion matrix: {e}")
        return False


# ---------------------------------------------------------------------------
# Function 4: Plot ROC Curve
# ---------------------------------------------------------------------------

def plot_roc_curve(model, X_test, y_test, save_path, model_name="Model"):
    """
    Creates and saves a ROC (Receiver Operating Characteristic) curve plot.

    WHY ROC-AUC matters for fraud:
    The ROC curve plots True Positive Rate (recall) vs. False Positive Rate at every
    possible threshold. AUC = 1.0 is perfect; AUC = 0.5 is random guessing.
    It's threshold-independent, making it ideal for comparing models on imbalanced data.

    Args:
        model      : Trained model with predict_proba().
        X_test     : Test feature matrix.
        y_test     : True labels.
        save_path  : Path to save the PNG.
        model_name : Used in plot title and legend.

    Returns:
        bool: True if saved, False if skipped.

    Example:
        plot_roc_curve(rf_model, X_test, y_test, "ml/roc_curve.png", "RandomForest")
    """
    if not MATPLOTLIB_AVAILABLE:
        print("  [SKIP] ROC curve plot skipped — matplotlib not installed.")
        return False

    try:
        # Get fraud probabilities
        y_prob = model.predict_proba(X_test)[:, 1]

        # Calculate ROC curve points at every threshold
        fpr, tpr, thresholds = roc_curve(y_test, y_prob)
        roc_auc_val = auc(fpr, tpr)

        fig, ax = plt.subplots(figsize=(7, 5))

        # Plot the ROC curve
        ax.plot(
            fpr, tpr,
            color='#2563EB',     # Blue
            lw=2.5,
            label=f'{model_name} (AUC = {roc_auc_val:.4f})'
        )

        # Random classifier baseline (AUC = 0.5)
        ax.plot([0, 1], [0, 1], color='gray', lw=1.5, linestyle='--', label='Random Guess (AUC = 0.50)')

        # Formatting
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate (Legitimate → Flagged)', fontsize=11)
        ax.set_ylabel('True Positive Rate (Fraud → Detected)', fontsize=11)
        ax.set_title(f'ROC Curve — {model_name}', fontsize=13)
        ax.legend(loc='lower right', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Add AUC text annotation
        ax.text(
            0.6, 0.15,
            f'AUC = {roc_auc_val:.4f}',
            fontsize=14, fontweight='bold',
            color='#2563EB',
            transform=ax.transAxes
        )

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"  ROC curve saved → {save_path}")
        return True

    except Exception as e:
        print(f"  [WARNING] Could not save ROC curve: {e}")
        return False


# ---------------------------------------------------------------------------
# Function 5: Compare Multiple Models
# ---------------------------------------------------------------------------

def compare_models(results_dict):
    """
    Prints a formatted comparison table of multiple model evaluation results.

    Args:
        results_dict (dict or list):
            - dict: {model_name: metrics_dict, ...}
            - list: [metrics_dict, ...] where each dict has "model_name" key.

    Example:
        compare_models({
            "LogisticRegression": {"accuracy": 0.99, "roc_auc": 0.97, ...},
            "RandomForest"       : {"accuracy": 0.9995, "roc_auc": 0.979, ...},
        })
    """
    # Normalize input to list format
    if isinstance(results_dict, dict):
        results_list = [{"model_name": k, **v} for k, v in results_dict.items()]
    else:
        results_list = results_dict

    if not results_list:
        print("  [WARNING] No results to compare.")
        return

    print("\n" + "="*75)
    print("  MODEL COMPARISON TABLE")
    print("="*75)

    # Header
    print(f"  {'Model':<22} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>8} {'ROC-AUC':>9} {'Best?':>6}")
    print("  " + "-"*73)

    # Find best model by ROC-AUC
    best_roc = max(r.get('roc_auc', 0) for r in results_list)

    for r in results_list:
        is_best = "✓" if r.get('roc_auc', 0) == best_roc else ""
        row = (
            f"  {r.get('model_name', 'Unknown'):<22}"
            f" {r.get('accuracy', 0):>9.4f}"
            f" {r.get('precision', 0):>10.4f}"
            f" {r.get('recall', 0):>8.4f}"
            f" {r.get('f1_score', 0):>8.4f}"
            f" {r.get('roc_auc', 0):>9.6f}"
            f" {is_best:>6}"
        )
        print(row)

    print("="*75)
    best = max(results_list, key=lambda r: r.get('roc_auc', 0))
    print(f"\n  Recommended model: {best.get('model_name')} (ROC-AUC: {best.get('roc_auc', 0):.6f})")
    print()

    # Interpretation tips
    print("  Quick Interpretation:")
    print("  - Recall > 0.80 : Good — catching most fraud cases")
    print("  - Precision > 0.90: Good — fewer false alarms for customers")
    print("  - ROC-AUC > 0.95  : Excellent discrimination ability")
    print()


# ---------------------------------------------------------------------------
# Standalone: Re-evaluate a saved model
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    """
    Standalone mode: Re-evaluate a saved model against test data.

    Usage:
        python evaluate.py  (runs a quick self-test with random data)
    """
    print("FraudGuard AI - Evaluation Module")
    print("Running quick self-test with dummy data...\n")

    try:
        import pandas as pd
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_classification
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler

        # Generate tiny test dataset
        X, y = make_classification(
            n_samples=500, n_features=10,
            weights=[0.97, 0.03], random_state=42
        )
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        # Train a quick model
        rf = RandomForestClassifier(n_estimators=20, class_weight='balanced', random_state=42)
        rf.fit(X_train, y_train)

        # Evaluate
        results = evaluate_model(rf, X_test, y_test, "TestRandomForest")
        print("  Evaluation results:")
        for key, val in results.items():
            print(f"    {key}: {val}")

        print("\n  Module working correctly ✓")

    except Exception as e:
        print(f"  [ERROR] Self-test failed: {e}")

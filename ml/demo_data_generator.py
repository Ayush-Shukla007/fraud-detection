"""
FraudGuard AI - Demo Data Generator
======================================

Generates realistic synthetic transaction data for testing the fraud detection pipeline.

This script creates:
  - 950 legitimate transactions (normal spending patterns)
  - 50 fraudulent transactions (anomalous patterns)
  - Saves to ../data/demo_transactions.csv

The format matches the Kaggle Credit Card Fraud dataset so the same model
can process both real and demo data seamlessly.

Usage:
    python demo_data_generator.py
    python demo_data_generator.py --output ../data/my_test_data.csv
    python demo_data_generator.py --samples 5000 --fraud-rate 0.03
"""

import os
import sys
import json
import argparse

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


# ---------------------------------------------------------------------------
# Core Generator Functions
# ---------------------------------------------------------------------------

def generate_legitimate_transaction(rng, transaction_id, time_offset):
    """
    Generates a single realistic legitimate transaction.

    Legitimate transactions have:
    - Normal V1-V28 PCA features centered around 0 with small variance
    - Amount following a log-normal distribution (most purchases are small)
    - Time following a sequential pattern (seconds since start of dataset)

    Args:
        rng           : numpy random Generator (seeded for reproducibility)
        transaction_id: Integer index for this transaction
        time_offset   : Time in seconds since dataset start

    Returns:
        dict: One row of transaction data
    """
    transaction = {
        'Time'  : float(time_offset),
        'Amount': float(np.clip(rng.lognormal(mean=3.5, sigma=1.5), 0.5, 5000))
        # lognormal produces right-skewed amounts (most are small, some are large)
    }

    # V1-V28 are PCA-transformed features in the real dataset.
    # For legitimate transactions, they follow roughly normal distributions.
    # We add slight correlations to simulate real PCA structure.
    for i in range(1, 29):
        # Each feature has slightly different variance (mimicking PCA component variance)
        std = max(0.1, 2.0 - i * 0.05)  # Earlier components have higher variance
        transaction[f'V{i}'] = float(rng.normal(0, std))

    # Legitimate transactions have Class = 0
    transaction['Class'] = 0

    return transaction


def generate_fraudulent_transaction(rng, transaction_id, time_offset):
    """
    Generates a single realistic fraudulent transaction.

    Fraudulent transactions have:
    - Anomalous V1-V28 values (shifted means, different distributions)
    - Often unusual amounts (very small for card testing, or very large)
    - Can happen at any time (fraud doesn't follow business hours)

    The real Kaggle dataset shows that V14, V12, V10, V4, V11 are the
    most discriminative features — we bias those for fraud realism.

    Args:
        rng           : numpy random Generator
        transaction_id: Integer index
        time_offset   : Seconds since dataset start

    Returns:
        dict: One fraudulent transaction row
    """
    transaction = {
        'Time': float(time_offset),
    }

    # Fraudulent amounts: often either very small (card testing <$5)
    # or very large (one big purchase before card is blocked)
    fraud_type = rng.choice(['small', 'large'], p=[0.4, 0.6])
    if fraud_type == 'small':
        transaction['Amount'] = float(rng.uniform(0.01, 10.0))
    else:
        transaction['Amount'] = float(rng.lognormal(mean=5.0, sigma=1.0))

    # V1-V28 for fraud: shifted distributions based on real dataset patterns
    # V14 is highly negative for fraud, V4 is positive, etc.
    # These biases are learned from the real Kaggle dataset's feature importances
    fraud_biases = {
        'V1' : -3.0, 'V2' :  2.5, 'V3' : -2.0, 'V4' :  2.0,
        'V5' : -1.5, 'V6' :  0.5, 'V7' : -2.5, 'V8' :  1.0,
        'V9' : -1.0, 'V10': -2.0, 'V11':  2.0, 'V12': -2.5,
        'V13':  0.5, 'V14': -4.5, 'V15':  0.2, 'V16': -1.5,
        'V17': -2.0, 'V18': -1.0, 'V19':  0.5, 'V20':  0.3,
        'V21':  0.8, 'V22':  0.5, 'V23':  0.2, 'V24': -0.3,
        'V25':  0.1, 'V26':  0.2, 'V27':  1.5, 'V28':  0.8,
    }

    for i in range(1, 29):
        bias = fraud_biases.get(f'V{i}', 0.0)
        std = max(0.1, 2.0 - i * 0.05)
        # Fraud features are shifted from the legitimate distribution
        transaction[f'V{i}'] = float(rng.normal(bias, std * 1.5))

    # Fraudulent transactions have Class = 1
    transaction['Class'] = 1

    return transaction


# ---------------------------------------------------------------------------
# Main Generator
# ---------------------------------------------------------------------------

def generate_demo_dataset(
    n_samples=1000,
    fraud_fraction=0.05,
    output_path=None,
    seed=42
):
    """
    Generates a complete demo dataset of synthetic transactions.

    Args:
        n_samples      (int)  : Total number of transactions to generate.
        fraud_fraction (float): Fraction of fraudulent transactions (0.0 to 1.0).
        output_path    (str)  : Where to save the CSV. None = auto-generate path.
        seed           (int)  : Random seed for reproducibility.

    Returns:
        pd.DataFrame: The complete dataset (also saved to CSV).
    """
    print("\n" + "="*55)
    print("  FraudGuard AI - Demo Data Generator")
    print("="*55)

    # Initialize seeded random generator for reproducibility
    rng = np.random.default_rng(seed)

    # Calculate split
    n_fraud = max(1, int(n_samples * fraud_fraction))
    n_legit = n_samples - n_fraud

    print(f"\n  Generating {n_samples:,} synthetic transactions:")
    print(f"    Legitimate : {n_legit:,}  ({(n_legit/n_samples*100):.1f}%)")
    print(f"    Fraudulent : {n_fraud:,}  ({(n_fraud/n_samples*100):.1f}%)")
    print(f"    Random seed: {seed}")

    rows = []

    # ---- Generate legitimate transactions ----
    print(f"\n  Generating legitimate transactions...")
    time_cursor = 0.0
    for i in range(n_legit):
        # Time advances by a random amount (seconds between transactions)
        time_cursor += rng.exponential(scale=10.0)  # Average 10 seconds between transactions
        row = generate_legitimate_transaction(rng, i, time_cursor)
        rows.append(row)

        if (i + 1) % 200 == 0:
            print(f"    Progress: {i+1:,}/{n_legit:,}")

    # ---- Generate fraudulent transactions ----
    print(f"  Generating fraudulent transactions...")
    for i in range(n_fraud):
        # Fraud can happen at any random time
        fraud_time = rng.uniform(0, time_cursor)
        row = generate_fraudulent_transaction(rng, i, fraud_time)
        rows.append(row)

    # ---- Build DataFrame ----
    df = pd.DataFrame(rows)

    # Shuffle rows so fraud isn't all at the end
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    # Ensure correct column order (Time, V1-V28, Amount, Class)
    columns = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount', 'Class']
    df = df[columns]

    # Round to 6 decimal places (matches Kaggle dataset format)
    df = df.round(6)

    # ---- Summary statistics ----
    print(f"\n  Dataset Summary:")
    print(f"    Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"    Classes : {df['Class'].value_counts().to_dict()}")
    print(f"    Amount  : min={df['Amount'].min():.2f}, max={df['Amount'].max():.2f}, mean={df['Amount'].mean():.2f}")

    # ---- Determine output path ----
    if output_path is None:
        # Default: save relative to this script's location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        output_path = os.path.join(data_dir, 'demo_transactions.csv')

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # ---- Save CSV ----
    df.to_csv(output_path, index=False)

    abs_path = os.path.abspath(output_path)
    print(f"\n  Saved to: {abs_path}")
    print(f"  File size: {os.path.getsize(abs_path) / 1024:.1f} KB")

    return df


# ---------------------------------------------------------------------------
# Bonus: Generate a single test transaction dict (useful for API testing)
# ---------------------------------------------------------------------------

def generate_single_transaction(is_fraud=False, seed=None):
    """
    Generates a single transaction as a Python dictionary.

    Useful for testing the /api/detect endpoint manually.

    Args:
        is_fraud (bool): Whether to generate a fraudulent transaction.
        seed     (int) : Optional random seed.

    Returns:
        dict: Single transaction with all feature values (no 'Class' column).

    Example:
        transaction = generate_single_transaction(is_fraud=True)
        # → {"Time": 45231.0, "V1": -3.2, ..., "Amount": 250.50}
    """
    rng = np.random.default_rng(seed)

    if is_fraud:
        row = generate_fraudulent_transaction(rng, 0, rng.uniform(0, 100000))
    else:
        row = generate_legitimate_transaction(rng, 0, rng.uniform(0, 100000))

    # Remove 'Class' — this is for prediction input (no label)
    row.pop('Class', None)

    return row


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="FraudGuard AI — Demo Transaction Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_data_generator.py
  python demo_data_generator.py --output ../data/test.csv
  python demo_data_generator.py --samples 5000 --fraud-rate 0.03
  python demo_data_generator.py --single-fraud    # Print one fraud transaction dict
        """
    )

    parser.add_argument(
        '--samples',
        type=int,
        default=1000,
        help='Total number of transactions to generate (default: 1000)'
    )
    parser.add_argument(
        '--fraud-rate',
        type=float,
        default=0.05,
        help='Fraction of transactions that are fraud (default: 0.05 = 5%%)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output CSV file path (default: ../data/demo_transactions.csv)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--single-fraud',
        action='store_true',
        help='Print a single fraudulent transaction dict (for API testing) and exit'
    )
    parser.add_argument(
        '--single-legit',
        action='store_true',
        help='Print a single legitimate transaction dict (for API testing) and exit'
    )

    args = parser.parse_args()

    # Handle single-transaction mode (useful for curl/API testing)
    if args.single_fraud:
        transaction = generate_single_transaction(is_fraud=True, seed=args.seed)
        print("\nSingle FRAUDULENT transaction (JSON format for API testing):")
        print(json.dumps(transaction, indent=2))
        print("\nUse this with:")
        print('  curl -X POST http://localhost:5000/api/detect \\')
        print('       -H "Content-Type: application/json" \\')
        print('       -d \'{"features": <paste above JSON>}\'')
        return

    if args.single_legit:
        transaction = generate_single_transaction(is_fraud=False, seed=args.seed)
        print("\nSingle LEGITIMATE transaction (JSON format for API testing):")
        print(json.dumps(transaction, indent=2))
        return

    # Validate fraud rate
    if not 0.001 <= args.fraud_rate <= 0.5:
        print("[ERROR] --fraud-rate must be between 0.001 and 0.5")
        sys.exit(1)

    # Validate sample count
    if args.samples < 10:
        print("[ERROR] --samples must be at least 10")
        sys.exit(1)

    # Generate the dataset
    df = generate_demo_dataset(
        n_samples=args.samples,
        fraud_fraction=args.fraud_rate,
        output_path=args.output,
        seed=args.seed
    )

    print()
    print("  Next steps:")
    print("  1. Train a model on this data:")
    print("       python train.py --data ../data/demo_transactions.csv")
    print("  2. Or run in demo mode (uses sklearn's make_classification):")
    print("       python train.py --demo")
    print("  3. Test batch detection with this file via the API:")
    print("       POST /api/batch-detect (upload the CSV)")
    print()


if __name__ == '__main__':
    main()

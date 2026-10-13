"""
ml_service.py — Machine-learning inference service for FraudGuard AI.

Behaviour
---------
* On startup, attempts to load model.joblib + scaler.joblib from the paths
  configured in settings.
* If the files are missing (e.g. first run, CI environment), the service
  falls back to DEMO MODE and logs a clear warning.
* DEMO MODE uses a hand-crafted scoring function that produces realistic,
  varying fraud probabilities based on the amount and V-features so the
  UI is fully interactive without a trained model.
* REAL MODE loads the joblib artefacts, scales the feature vector, and
  calls model.predict_proba() to obtain a calibrated probability.
* get_metrics() returns either real metrics from metrics.json or synthetic
  demo metrics, always setting is_demo correctly.
"""

from __future__ import annotations

import json
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default ordered feature list (matches typical Kaggle credit-card dataset)
DEFAULT_FEATURES: List[str] = (
    ["time"]
    + [f"v{i}" for i in range(1, 29)]
    + ["amount"]
)

# ── Demo scoring function ─────────────────────────────────────────────────────

def _demo_predict(features: Dict[str, float]) -> float:
    """
    Deterministic but realistic fraud probability for demo mode.

    Logic mirrors patterns found in the real credit-card fraud dataset:
    - Large amounts raise the base score.
    - Very negative V1 is a strong fraud indicator.
    - Elevated V4 is associated with fraud.
    - V3 modulates in the opposite direction.

    Returns a float in (0.01, 0.99).
    """
    amount = features.get("amount", 0.0)
    v1 = features.get("v1", 0.0)
    v3 = features.get("v3", 0.0)
    v4 = features.get("v4", 0.0)
    v14 = features.get("v14", 0.0)
    v17 = features.get("v17", 0.0)

    score = 0.05  # low base probability — most transactions are legitimate

    # Amount-based risk
    if amount > 500:
        score += 0.15
    if amount > 1000:
        score += 0.15   # cumulative: +0.30 for >1000
    if amount > 5000:
        score += 0.20   # cumulative: +0.50 for >5000

    # V1: strongly negative → fraud signal
    if v1 < -3:
        score += 0.30
    elif v1 < -1:
        score += 0.10

    # V4: positive → fraud signal
    if v4 > 3:
        score += 0.20
    elif v4 > 1:
        score += 0.05

    # V14: strongly negative → fraud signal (well-known in literature)
    if v14 < -5:
        score += 0.25
    elif v14 < -2:
        score += 0.10

    # V17: negative → slight fraud signal
    if v17 < -3:
        score += 0.15

    # V3: high positive slightly reduces fraud probability
    if v3 > 3:
        score -= 0.10

    # Clamp to a realistic range
    return max(0.01, min(0.99, score))


# ── Risk bucketing ────────────────────────────────────────────────────────────

def _risk_level(probability: float) -> str:
    """Map a probability score to a human-readable risk tier."""
    if probability >= 0.70:
        return "HIGH"
    if probability >= 0.30:
        return "MEDIUM"
    return "LOW"


# ── Service class ─────────────────────────────────────────────────────────────

class MLService:
    """
    Singleton service that encapsulates all ML inference logic.

    Attributes
    ----------
    is_demo       : True when running without real model artefacts.
    model_loaded  : True when a real scikit-learn / XGBoost model is loaded.
    _model        : The loaded model object (or None in demo mode).
    _scaler       : The loaded StandardScaler object (or None in demo mode).
    _features     : Ordered list of feature names expected by the model.
    """

    def __init__(self) -> None:
        self.is_demo: bool = True
        self.model_loaded: bool = False
        self._model: Optional[Any] = None
        self._scaler: Optional[Any] = None
        self._features: List[str] = DEFAULT_FEATURES[:]

    # ── Startup ───────────────────────────────────────────────────────────────

    def load(
        self,
        model_path: str,
        scaler_path: str,
        features_path: str,
        force_demo: bool = False,
    ) -> None:
        """
        Attempt to load ML artefacts from disk.

        Parameters
        ----------
        model_path    : Path to model.joblib.
        scaler_path   : Path to scaler.joblib.
        features_path : Path to features.json  (optional).
        force_demo    : If True, skip loading even if files exist.
        """
        if force_demo:
            logger.warning(
                "DEMO_MODE=true in config — running with mock predictions."
            )
            return

        # Try loading features list first (non-critical — fall back to default)
        if os.path.exists(features_path):
            try:
                with open(features_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    # Accept either a plain list or {"features": [...]}
                    raw_features = data if isinstance(data, list) else data.get(
                        "features", DEFAULT_FEATURES
                    )
                    self._features = [str(f).lower() for f in raw_features]
                logger.info("Loaded %d features from %s", len(self._features), features_path)
            except Exception as exc:
                logger.warning("Could not parse features.json: %s — using defaults.", exc)
        else:
            logger.info("features.json not found at %s — using default feature list.", features_path)

        # Attempt to load the model and scaler
        model_exists = os.path.exists(model_path)
        scaler_exists = os.path.exists(scaler_path)

        if not model_exists or not scaler_exists:
            logger.warning(
                "⚠️  ML artefacts not found (model=%s scaler=%s). "
                "Falling back to DEMO MODE.  Place model.joblib and scaler.joblib "
                "in the ml/ directory to enable real predictions.",
                model_path,
                scaler_path,
            )
            return

        try:
            import joblib  # noqa: PLC0415

            self._model = joblib.load(model_path)
            self._scaler = joblib.load(scaler_path)
            self.is_demo = False
            self.model_loaded = True
            logger.info(
                "[OK] Real ML model loaded from %s - REAL MODE active.", model_path
            )
        except Exception as exc:
            logger.error(
                "Failed to load ML artefacts (%s). Falling back to DEMO MODE.", exc
            )

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Run fraud detection on a single feature dictionary.

        Parameters
        ----------
        features : Dict mapping feature names (lowercase) to float values (in INR).

        Returns
        -------
        Dict with keys: prediction (int), fraud_probability (float), risk_level (str).
        """
        # Define exchange rate once
        USD_TO_INR = 96.0
        
        # Create a copy so we don't mutate the original dict which is saved to the DB
        features_for_ml = features.copy()
        
        # Convert INR amount to USD for the ML model
        if "amount" in features_for_ml:
            features_for_ml["amount"] = features_for_ml["amount"] / USD_TO_INR

        if self.is_demo or not self.model_loaded:
            return self._demo_inference(features_for_ml)
        return self._real_inference(features_for_ml)

    def _demo_inference(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Fake inference using the deterministic scoring function."""
        prob = _demo_predict(features)
        pred = 1 if prob >= 0.5 else 0
        return {
            "prediction": pred,
            "fraud_probability": round(prob, 6),
            "risk_level": _risk_level(prob),
        }

    def _real_inference(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Real inference with the loaded scikit-learn / XGBoost model.

        Constructs a feature vector in the same column order the model was
        trained on, scales it, then calls predict_proba().
        """
        import numpy as np  # noqa: PLC0415

        try:
            # Build ordered feature vector
            vector = [features.get(f, 0.0) for f in self._features]
            X = np.array(vector, dtype=float).reshape(1, -1)

            # Scale if a scaler is available
            if self._scaler is not None:
                X = self._scaler.transform(X)

            # Predict
            proba = self._model.predict_proba(X)[0]
            # proba[1] is the probability of class 1 (fraud)
            prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
            pred = 1 if prob >= 0.5 else 0

            return {
                "prediction": pred,
                "fraud_probability": round(prob, 6),
                "risk_level": _risk_level(prob),
            }
        except Exception as exc:
            logger.error("Real inference failed (%s) — falling back to demo.", exc)
            return self._demo_inference(features)

    # ── Metrics ───────────────────────────────────────────────────────────────

    def get_metrics(self, metrics_path: str = "../ml/metrics.json") -> Dict[str, Any]:
        """
        Return model performance metrics.

        Tries to load metrics.json from disk; if unavailable returns
        plausible demo metrics so the UI renders correctly.
        """
        if not self.is_demo and os.path.exists(metrics_path):
            try:
                with open(metrics_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                data["is_demo"] = False
                data.setdefault("features_used", self._features)
                return data
            except Exception as exc:
                logger.warning("Could not load metrics.json: %s", exc)

        # ── Demo metrics ──────────────────────────────────────────────────────
        # These are realistic numbers for a well-trained fraud-detection model.
        return {
            "accuracy": 0.9994,
            "precision": 0.9412,
            "recall": 0.7755,
            "f1_score": 0.8503,
            "roc_auc": 0.9822,
            "confusion_matrix": {
                "TP": 114,
                "TN": 56_854,
                "FP": 7,
                "FN": 33,
            },
            "model_name": "XGBoost (Demo)",
            "training_samples": 227_451,
            "test_samples": 57_008,
            "features_used": self._features,
            "is_demo": True,
        }

    # ── Feature list ──────────────────────────────────────────────────────────

    @property
    def features(self) -> List[str]:
        return self._features


# ── Module-level singleton ────────────────────────────────────────────────────
ml_service = MLService()

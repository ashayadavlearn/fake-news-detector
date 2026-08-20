"""
predict.py
Loads the trained model + vectorizer once (module-level cache) and
exposes predict_news() for app.py to call on every /detector submission.

Pipeline:  raw text -> clean_text() -> vectorizer.transform() -> model.predict()
           -> confidence score (predict_proba if available, else a
              decision_function-based fallback for PassiveAggressiveClassifier)
"""

import os

import joblib
import numpy as np

from config import Config
from utils import clean_text

_model = None
_vectorizer = None
_metadata = None


class ModelNotTrainedError(RuntimeError):
    """Raised when predict_news() is called before train_model.py has been run."""


def _load_artifacts():
    global _model, _vectorizer, _metadata

    if _model is not None and _vectorizer is not None:
        return

    if not (os.path.exists(Config.MODEL_PATH) and os.path.exists(Config.VECTORIZER_PATH)):
        raise ModelNotTrainedError(
            "Model artifacts not found. Run 'python train_model.py' first to train "
            "and save model.pkl / vectorizer.pkl."
        )

    _model = joblib.load(Config.MODEL_PATH)
    _vectorizer = joblib.load(Config.VECTORIZER_PATH)
    if os.path.exists(Config.METADATA_PATH):
        _metadata = joblib.load(Config.METADATA_PATH)
    else:
        _metadata = {"best_model_name": type(_model).__name__, "supports_proba": hasattr(_model, "predict_proba")}


def get_metadata() -> dict:
    _load_artifacts()
    return _metadata or {}


def predict_news(raw_text: str) -> dict:
    """
    Returns:
        {
            "label": "REAL" | "FAKE",
            "confidence": float 0-100,
            "model_used": str,
        }
    """
    _load_artifacts()

    cleaned = clean_text(raw_text)
    if not cleaned:
        # Nothing meaningful left after preprocessing (e.g. pure punctuation/numbers)
        return {"label": "REAL", "confidence": 50.0, "model_used": _metadata.get("best_model_name", "model")}

    vec = _vectorizer.transform([cleaned])
    label = _model.predict(vec)[0]

    confidence = _confidence_score(vec, label)

    return {
        "label": label,
        "confidence": round(confidence, 1),
        "model_used": _metadata.get("best_model_name", type(_model).__name__),
    }


def _confidence_score(vec, predicted_label) -> float:
    """Best-effort confidence score across all four candidate model types."""
    if hasattr(_model, "predict_proba"):
        proba = _model.predict_proba(vec)[0]
        classes = list(_model.classes_)
        idx = classes.index(predicted_label)
        return float(proba[idx]) * 100.0

    if hasattr(_model, "decision_function"):
        # PassiveAggressiveClassifier: turn the raw margin into a pseudo-probability
        # via a sigmoid so the UI always has a 0-100% confidence number.
        margin = _model.decision_function(vec)
        margin = margin[0] if np.ndim(margin) else margin
        prob = 1.0 / (1.0 + np.exp(-abs(margin)))
        return float(prob) * 100.0

    # Absolute fallback
    return 75.0

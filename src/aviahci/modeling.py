"""Reusable classification models and evaluation metrics."""

import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


SUPPORTED_MODELS = ("logistic_regression", "random_forest")


def build_model(model_name="logistic_regression", random_state=42,
                n_estimators=500):
    """Build a supported classifier with explicit reproducibility settings."""
    if model_name == "logistic_regression":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(
                max_iter=2000,
                random_state=random_state,
            )),
        ])

    if model_name == "random_forest":
        if n_estimators < 1:
            raise ValueError("n_estimators must be at least 1.")

        return RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1,
        )

    raise ValueError(
        f"Unsupported model: {model_name!r}. "
        f"Choose from {SUPPORTED_MODELS}."
    )


def fit_model(X_train, y_train, model_name="logistic_regression",
              random_state=42, n_estimators=500):
    """Fit a classifier using training data only."""
    y = np.asarray(y_train)

    if y.ndim != 1 or len(y) == 0:
        raise ValueError("y_train must be a non-empty one-dimensional array.")

    if set(np.unique(y)) != {0, 1}:
        raise ValueError("Training labels must contain both 0 and 1.")

    model = build_model(
        model_name=model_name,
        random_state=random_state,
        n_estimators=n_estimators,
    )
    model.fit(X_train, y)
    return model


def evaluate_model(model, X_test, y_test, threshold=0.5):
    """Evaluate a fitted binary classifier at an explicit threshold.

    Scores and metrics describe presence-versus-background discrimination.
    They are not calibrated occupancy probabilities.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1.")

    y_true = np.asarray(y_test)

    if y_true.ndim != 1 or len(y_true) == 0:
        raise ValueError("y_test must be a non-empty one-dimensional array.")

    if set(np.unique(y_true)) != {0, 1}:
        raise ValueError("Test labels must contain both 0 and 1.")

    classes = np.asarray(model.classes_)
    positive_indices = np.flatnonzero(classes == 1)

    if len(positive_indices) != 1:
        raise ValueError("Fitted model must have a class labelled 1.")

    scores = model.predict_proba(X_test)[:, positive_indices[0]]
    predictions = (scores >= threshold).astype(int)
    matrix = confusion_matrix(y_true, predictions, labels=[0, 1])

    return {
        "threshold": float(threshold),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "average_precision": float(average_precision_score(y_true, scores)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
        "precision": float(precision_score(
            y_true, predictions, zero_division=0
        )),
        "recall": float(recall_score(
            y_true, predictions, zero_division=0
        )),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "confusion_matrix": matrix.tolist(),
        "n_test": int(len(y_true)),
        "predicted_presence": int(predictions.sum()),
    }

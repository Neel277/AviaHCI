import numpy as np
import pandas as pd
import pytest

from aviahci.modeling import build_model, fit_model, evaluate_model


@pytest.fixture
def sample_data():
    X = pd.DataFrame({
        "elevation": [100, 150, 200, 250, 800, 850, 900, 950,
                      120, 180, 220, 280, 820, 880, 920, 980],
        "temperature": [20, 19, 18, 17, 5, 4, 3, 2,
                        21, 18, 17, 16, 6, 4, 2, 1],
    })
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1,
                  0, 0, 1, 1, 0, 0, 1, 1])
    return X, y


@pytest.mark.parametrize(
    "model_name",
    ["logistic_regression", "random_forest"],
)
def test_models_fit_and_evaluate(sample_data, model_name):
    X, y = sample_data
    model = fit_model(
        X.iloc[:12], y[:12],
        model_name=model_name,
        random_state=42,
        n_estimators=50,
    )
    metrics = evaluate_model(model, X.iloc[12:], y[12:])

    assert 0 <= metrics["roc_auc"] <= 1
    assert 0 <= metrics["average_precision"] <= 1
    assert 0 <= metrics["balanced_accuracy"] <= 1
    assert metrics["n_test"] == 4
    assert metrics["predicted_presence"] in range(5)
    assert len(metrics["confusion_matrix"]) == 2


def test_threshold_changes_classification(sample_data):
    X, y = sample_data
    model = fit_model(
        X.iloc[:12], y[:12],
        model_name="logistic_regression",
    )
    low = evaluate_model(model, X.iloc[12:], y[12:], threshold=0.3)
    high = evaluate_model(model, X.iloc[12:], y[12:], threshold=0.7)

    assert low["threshold"] == 0.3
    assert high["threshold"] == 0.7


def test_unsupported_model_is_rejected():
    with pytest.raises(ValueError, match="Unsupported model"):
        build_model("unknown_model")


def test_invalid_threshold_is_rejected(sample_data):
    X, y = sample_data
    model = fit_model(X.iloc[:12], y[:12])

    with pytest.raises(ValueError, match="threshold"):
        evaluate_model(model, X.iloc[12:], y[12:], threshold=1.5)


def test_training_requires_both_classes(sample_data):
    X, y = sample_data

    with pytest.raises(ValueError, match="both 0 and 1"):
        fit_model(X.iloc[:4], np.zeros(4, dtype=int))

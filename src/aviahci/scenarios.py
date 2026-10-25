"""Robustness, scenario, and extrapolation diagnostics."""

import numpy as np
import pandas as pd


def threshold_sensitivity(model, X, y, thresholds=None):
    """Evaluate discrimination metrics over explicit decision thresholds."""
    from aviahci.modeling import evaluate_model

    if thresholds is None:
        thresholds = np.arange(0.1, 1.0, 0.1)

    thresholds = [float(t) for t in thresholds]
    if not thresholds:
        raise ValueError("At least one threshold is required.")
    if any(not np.isfinite(t) or t < 0 or t > 1 for t in thresholds):
        raise ValueError("Thresholds must be finite values between 0 and 1.")

    rows = []
    for threshold in thresholds:
        metrics = evaluate_model(model, X, y, threshold=threshold)
        rows.append({
            "threshold": threshold,
            "roc_auc": metrics["roc_auc"],
            "average_precision": metrics["average_precision"],
            "balanced_accuracy": metrics["balanced_accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
            "predicted_presence": metrics["predicted_presence"],
        })

    return pd.DataFrame(rows)


def predictor_range_diagnostics(X_train, X_target):
    """Flag target predictor values outside observed training ranges.

    This identifies univariate range extrapolation only. It does not detect
    all multivariate novelty or prove ecological extrapolation.
    """
    if not hasattr(X_train, "columns") or not hasattr(X_target, "columns"):
        raise ValueError("X_train and X_target must be pandas DataFrames.")
    if X_train.empty or X_target.empty:
        raise ValueError("Training and target predictor data must not be empty.")

    missing = set(X_train.columns) - set(X_target.columns)
    if missing:
        raise ValueError(
            f"Target data is missing training predictors: {sorted(missing)}"
        )

    rows = []
    for column in X_train.columns:
        train_values = pd.to_numeric(X_train[column], errors="coerce")
        target_values = pd.to_numeric(X_target[column], errors="coerce")

        valid_train = train_values[np.isfinite(train_values)]
        if valid_train.empty:
            raise ValueError(
                f"Training predictor {column!r} has no finite numeric values."
            )

        lower = float(valid_train.min())
        upper = float(valid_train.max())
        finite_target = np.isfinite(target_values)
        below = finite_target & (target_values < lower)
        above = finite_target & (target_values > upper)
        outside = below | above
        n_finite = int(finite_target.sum())

        rows.append({
            "predictor": column,
            "training_min": lower,
            "training_max": upper,
            "target_n": int(len(target_values)),
            "target_finite_n": n_finite,
            "below_training_min_n": int(below.sum()),
            "above_training_max_n": int(above.sum()),
            "outside_training_range_n": int(outside.sum()),
            "outside_training_range_fraction": (
                float(outside.sum() / n_finite) if n_finite else float("nan")
            ),
            "target_nonfinite_n": int((~finite_target).sum()),
        })

    return pd.DataFrame(rows)


def temperature_perturbation(model, X, temperature_col, deltas):
    """Compare predicted scores under explicit additive temperature shifts.

    Deltas use the same units as temperature_col. The input DataFrame is
    copied; it is never modified. Returned scores are model scores, not
    calibrated occupancy probabilities.
    """
    if temperature_col not in X.columns:
        raise ValueError(
            f"Temperature predictor {temperature_col!r} is missing from X."
        )

    deltas = [float(delta) for delta in deltas]
    if not deltas:
        raise ValueError("At least one temperature delta is required.")
    if any(not np.isfinite(delta) for delta in deltas):
        raise ValueError("Temperature deltas must be finite.")

    if not hasattr(model, "predict_proba"):
        raise ValueError("Model must support predict_proba.")

    classes = np.asarray(model.classes_)
    positive_indices = np.flatnonzero(classes == 1)
    if len(positive_indices) != 1:
        raise ValueError("Fitted model must have a class labelled 1.")

    positive_index = int(positive_indices[0])
    rows = []

    for delta in deltas:
        scenario_X = X.copy()
        scenario_X[temperature_col] = (
            pd.to_numeric(scenario_X[temperature_col], errors="raise") + delta
        )
        scores = model.predict_proba(scenario_X)[:, positive_index]

        rows.append({
            "temperature_delta": delta,
            "mean_score": float(np.mean(scores)),
            "median_score": float(np.median(scores)),
            "min_score": float(np.min(scores)),
            "max_score": float(np.max(scores)),
            "n_rows": int(len(scores)),
            "scores": scores.tolist(),
        })

    return pd.DataFrame(rows)


def _run_spatial_evaluation(
    data,
    predictor_cols,
    target_col,
    model_name,
    test_size,
    random_state,
    block_degrees,
    n_estimators,
):
    """Fit and evaluate one spatially separated train/test split."""
    from aviahci.modeling import build_model, evaluate_model, fit_model
    from aviahci.sampling import spatial_train_test_split

    required = set(predictor_cols) | {target_col, "longitude", "latitude"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Data is missing required columns: {sorted(missing)}")

    split_labels = spatial_train_test_split(
        data,
        test_size=test_size,
        random_state=random_state,
        block_degrees=block_degrees,
        longitude_col="longitude",
        latitude_col="latitude",
    )
    train_mask = split_labels == "train"
    test_mask = split_labels == "test"

    X_train = data.loc[train_mask, predictor_cols]
    y_train = data.loc[train_mask, target_col].astype(int)
    X_test = data.loc[test_mask, predictor_cols]
    y_test = data.loc[test_mask, target_col].astype(int)

    model = fit_model(
        X_train,
        y_train,
        model_name=model_name,
        random_state=random_state,
        n_estimators=n_estimators,
    )
    metrics = evaluate_model(model, X_test, y_test)

    return {
        "random_state": int(random_state),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        **metrics,
    }


def repeated_spatial_validation(
    data,
    predictor_cols,
    target_col="label",
    model_name="logistic_regression",
    repeats=10,
    test_size=0.2,
    block_degrees=0.2,
    random_state=42,
    n_estimators=500,
):
    """Evaluate a model across repeated spatially separated splits.

    Data must contain binary labels, predictor columns, and longitude/latitude.
    Coordinate columns are used for splitting and are not automatically predictors.
    A split that cannot support fitting or evaluation raises an informative error.
    """
    import pandas as pd

    if repeats < 1:
        raise ValueError("repeats must be at least 1.")
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1.")
    if block_degrees <= 0:
        raise ValueError("block_degrees must be positive.")
    if not predictor_cols:
        raise ValueError("At least one predictor column is required.")
    if target_col not in data.columns:
        raise ValueError(f"Target column {target_col!r} is missing.")
    if data[target_col].isna().any():
        raise ValueError("Target labels must not contain missing values.")
    if not set(data[target_col].unique()).issubset({0, 1}):
        raise ValueError("Target labels must be binary: 0 (background), 1 (presence).")

    rows = []
    for repeat in range(repeats):
        seed = int(random_state + repeat)
        try:
            row = _run_spatial_evaluation(
                data=data,
                predictor_cols=list(predictor_cols),
                target_col=target_col,
                model_name=model_name,
                test_size=test_size,
                random_state=seed,
                block_degrees=block_degrees,
                n_estimators=n_estimators,
            )
        except ValueError as exc:
            raise ValueError(
                f"Spatial validation failed on repeat {repeat + 1} "
                f"(seed={seed}): {exc}"
            ) from exc

        row["repeat"] = repeat + 1
        rows.append(row)

    return pd.DataFrame(rows)


def background_sampling_sensitivity(
    X_presence,
    X_background,
    predictor_cols,
    n_background_values,
    repeats=5,
    model_name="logistic_regression",
    test_size=0.2,
    block_degrees=0.2,
    random_state=42,
    n_estimators=500,
):
    """Measure model performance across background sample sizes and draws.

    Both input DataFrames must contain predictor columns plus longitude and
    latitude. Presence rows receive label 1; background rows receive label 0.
    Background rows are sampled without replacement within each draw.
    Spatially separated evaluation is used for every draw.

    This measures sensitivity to background sample size and selection, not
    sensitivity to every possible background-generation method.
    """
    import pandas as pd

    if not predictor_cols:
        raise ValueError("At least one predictor column is required.")
    if X_presence.empty or X_background.empty:
        raise ValueError("Presence and background data must both be non-empty.")
    if repeats < 1:
        raise ValueError("repeats must be at least 1.")

    required = set(predictor_cols) | {"longitude", "latitude"}
    for name, frame in (
        ("X_presence", X_presence),
        ("X_background", X_background),
    ):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{name} is missing columns: {sorted(missing)}")

    sizes = [int(value) for value in n_background_values]
    if not sizes or any(size < 1 for size in sizes):
        raise ValueError("Background sample sizes must be positive integers.")
    if any(size > len(X_background) for size in sizes):
        raise ValueError(
            "A requested background sample size exceeds available background rows."
        )

    rows = []
    for size_index, size in enumerate(sizes):
        for repeat in range(repeats):
            seed = int(random_state + size_index * repeats + repeat)
            sampled_background = X_background.sample(
                n=size,
                replace=False,
                random_state=seed,
            )

            presence = X_presence.copy()
            background = sampled_background.copy()
            presence["label"] = 1
            background["label"] = 0
            combined = pd.concat(
                [presence, background],
                ignore_index=True,
            )

            try:
                result = _run_spatial_evaluation(
                    data=combined,
                    predictor_cols=list(predictor_cols),
                    target_col="label",
                    model_name=model_name,
                    test_size=test_size,
                    random_state=seed,
                    block_degrees=block_degrees,
                    n_estimators=n_estimators,
                )
            except ValueError as exc:
                raise ValueError(
                    f"Background sensitivity failed for n_background={size}, "
                    f"repeat={repeat + 1}, seed={seed}: {exc}"
                ) from exc

            result["n_background"] = size
            result["repeat"] = repeat + 1
            rows.append(result)

    return pd.DataFrame(rows)

import pandas as pd

from aviahci.validation import validate_occurrence_csv


def test_valid_occurrence_coordinates(tmp_path):
    path = tmp_path / "valid.csv"
    pd.DataFrame({
        "longitude": [7.4, 8.1],
        "latitude": [46.0, 47.0],
    }).to_csv(path, index=False)

    report = validate_occurrence_csv(path)

    assert report.valid
    assert report.details["rows"] == 2
    assert report.details["unique_coordinate_pairs"] == 2


def test_missing_coordinate_columns(tmp_path):
    path = tmp_path / "missing_columns.csv"
    pd.DataFrame({"x": [7.4], "y": [46.0]}).to_csv(path, index=False)

    report = validate_occurrence_csv(path)

    assert not report.valid
    assert report.errors


def test_invalid_coordinate_values(tmp_path):
    path = tmp_path / "invalid_coordinates.csv"
    pd.DataFrame({
        "longitude": [181, "not-a-number"],
        "latitude": [46.0, 47.0],
    }).to_csv(path, index=False)

    report = validate_occurrence_csv(path)

    assert not report.valid
    assert report.details["missing_or_non_numeric_coordinate_rows"] >= 1
    assert report.details["out_of_range_coordinate_rows"] >= 1


def test_duplicate_coordinate_pairs_are_reported(tmp_path):
    path = tmp_path / "duplicates.csv"
    pd.DataFrame({
        "longitude": [7.4, 7.4],
        "latitude": [46.0, 46.0],
    }).to_csv(path, index=False)

    report = validate_occurrence_csv(path)

    assert report.valid
    assert report.details["unique_coordinate_pairs"] == 1
    assert report.details["duplicate_coordinate_rows"] == 1

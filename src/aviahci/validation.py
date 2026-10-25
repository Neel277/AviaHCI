"""Input validation for AviaHCI.

Validation reports identify potential data-quality issues. They do not
prove that data are ecologically appropriate for a particular study.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class ValidationReport:
    """Structured result returned by AviaHCI input checks."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary suitable for JSON/reporting."""
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "details": dict(self.details),
        }


def validate_occurrence_csv(
    path: str | Path,
    longitude_col: str = "longitude",
    latitude_col: str = "latitude",
    date_col: str | None = None,
    species_col: str | None = None,
) -> ValidationReport:
    """Validate an occurrence table without modifying the source file.

    Required columns default to longitude and latitude. Optional date and
    species columns are checked only when their names are provided.
    """
    source = Path(path)
    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"path": str(source)}

    if not source.is_file():
        return ValidationReport(
            valid=False,
            errors=[f"Occurrence file does not exist: {source}"],
            details=details,
        )

    try:
        # sep=None allows common comma- and tab-delimited files to be detected.
        table = pd.read_csv(source, sep=None, engine="python")
    except Exception as exc:
        return ValidationReport(
            valid=False,
            errors=[f"Could not read occurrence table: {exc}"],
            details=details,
        )

    table.columns = [str(column).strip() for column in table.columns]
    details["rows"] = int(len(table))
    details["columns"] = list(table.columns)

    if table.empty:
        errors.append("Occurrence table contains no data rows.")

    required = [longitude_col, latitude_col]
    missing = [name for name in required if name not in table.columns]
    if missing:
        errors.append(
            "Missing required coordinate column(s): " + ", ".join(missing)
        )
        return ValidationReport(
            valid=False,
            errors=errors,
            warnings=warnings,
            details=details,
        )

    longitude = pd.to_numeric(table[longitude_col], errors="coerce")
    latitude = pd.to_numeric(table[latitude_col], errors="coerce")

    missing_coordinates = longitude.isna() | latitude.isna()
    out_of_range = (
        longitude.notna()
        & latitude.notna()
        & (
            ~longitude.between(-180, 180)
            | ~latitude.between(-90, 90)
        )
    )

    details["missing_or_non_numeric_coordinate_rows"] = int(
        missing_coordinates.sum()
    )
    details["out_of_range_coordinate_rows"] = int(out_of_range.sum())
    details["unique_coordinate_pairs"] = int(
        table.loc[
            ~missing_coordinates & ~out_of_range,
            [longitude_col, latitude_col],
        ].drop_duplicates().shape[0]
    )

    if missing_coordinates.any():
        warnings.append(
            f"{int(missing_coordinates.sum())} row(s) have missing or "
            "non-numeric coordinates."
        )

    if out_of_range.any():
        errors.append(
            f"{int(out_of_range.sum())} row(s) have coordinates outside "
            "valid longitude/latitude ranges."
        )

    duplicate_rows = int(
        table.duplicated(subset=[longitude_col, latitude_col]).sum()
    )
    details["duplicate_coordinate_rows"] = duplicate_rows
    if duplicate_rows:
        warnings.append(
            f"{duplicate_rows} row(s) repeat a coordinate pair; duplicates "
            "may be legitimate repeated observations and require review."
        )

    for optional_col, label in (
        (date_col, "date"),
        (species_col, "species"),
    ):
        if optional_col is not None:
            if optional_col not in table.columns:
                warnings.append(
                    f"Configured {label} column '{optional_col}' was not found."
                )
            else:
                missing_count = int(table[optional_col].isna().sum())
                details[f"missing_{label}_values"] = missing_count
                if missing_count:
                    warnings.append(
                        f"{missing_count} row(s) have missing {label} values."
                    )

    details["coordinate_columns"] = {
        "longitude": longitude_col,
        "latitude": latitude_col,
    }

    return ValidationReport(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        details=details,
    )


def validate_raster_paths(
    paths: list[str | Path],
) -> ValidationReport:
    """Check that raster paths exist and are files.

    This function does not yet inspect raster CRS, resolution, alignment,
    NoData values, or temporal compatibility.
    """
    errors: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []
    missing: list[str] = []

    if not paths:
        errors.append("No raster paths were supplied.")

    for item in paths:
        path = Path(item)
        checked.append(str(path))
        if not path.is_file():
            missing.append(str(path))

    if missing:
        errors.append(
            "Raster file(s) not found: " + ", ".join(missing)
        )

    return ValidationReport(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        details={
            "checked_paths": checked,
            "missing_paths": missing,
            "count_checked": len(checked),
        },
    )

"""Read-only raster metadata and alignment checks."""

from pathlib import Path
from typing import Any

from aviahci.validation import ValidationReport


def inspect_raster(path: str | Path) -> dict[str, Any]:
    """Return basic metadata for a readable raster dataset.

    Requires the optional geospatial dependencies.
    No raster data are changed.
    """
    try:
        import rasterio
    except ImportError as exc:
        raise ImportError(
            "Raster inspection requires rasterio. Install AviaHCI with "
            'its geospatial extras: pip install -e ".[geospatial]"'
        ) from exc

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Raster file not found: {source}")

    with rasterio.open(source) as dataset:
        transform = dataset.transform
        return {
            "path": str(source),
            "width": int(dataset.width),
            "height": int(dataset.height),
            "band_count": int(dataset.count),
            "crs": str(dataset.crs) if dataset.crs else None,
            "bounds": {
                "left": float(dataset.bounds.left),
                "bottom": float(dataset.bounds.bottom),
                "right": float(dataset.bounds.right),
                "top": float(dataset.bounds.top),
            },
            "resolution": [
                float(transform.a),
                float(transform.e),
            ],
            "transform": [
                float(value) for value in transform[:6]
            ],
            "dtypes": list(dataset.dtypes),
            "nodata_values": [
                None if value is None else float(value)
                for value in dataset.nodatavals
            ],
        }


def validate_raster_alignment(
    paths: list[str | Path],
    *,
    require_same_crs: bool = True,
    require_same_dimensions: bool = True,
    require_same_transform: bool = True,
) -> ValidationReport:
    """Inspect multiple rasters and report grid mismatches.

    Exact transform comparison is intentional for strict grid alignment.
    This checks metadata, not whether the raster values are ecologically
    comparable or temporally compatible.
    """
    errors: list[str] = []
    warnings: list[str] = []
    metadata: list[dict[str, Any]] = []

    if not paths:
        return ValidationReport(
            valid=False,
            errors=["No raster paths were supplied."],
        )

    for item in paths:
        try:
            metadata.append(inspect_raster(item))
        except Exception as exc:
            errors.append(f"{item}: {exc}")

    if errors:
        return ValidationReport(
            valid=False,
            errors=errors,
            warnings=warnings,
            details={"rasters_inspected": len(metadata)},
        )

    reference = metadata[0]

    for current in metadata[1:]:
        name = current["path"]
        if require_same_crs and current["crs"] != reference["crs"]:
            errors.append(
                f"CRS mismatch: {name} has {current['crs']!r}; "
                f"reference has {reference['crs']!r}."
            )

        if require_same_dimensions and (
            current["width"] != reference["width"]
            or current["height"] != reference["height"]
        ):
            errors.append(
                f"Dimension mismatch: {name} is "
                f"{current['width']}x{current['height']}; reference is "
                f"{reference['width']}x{reference['height']}."
            )

        if require_same_transform and (
            current["transform"] != reference["transform"]
        ):
            errors.append(
                f"Grid transform mismatch: {name} does not match "
                "the reference raster."
            )

        if current["crs"] is None:
            warnings.append(f"CRS is missing for {name}.")

    for item in metadata:
        if item["crs"] is None:
            warning = f"CRS is missing for {item['path']}."
            if warning not in warnings:
                warnings.append(warning)

    return ValidationReport(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        details={
            "rasters_inspected": len(metadata),
            "reference_raster": reference["path"],
            "metadata": metadata,
            "alignment_checks": {
                "same_crs": require_same_crs,
                "same_dimensions": require_same_dimensions,
                "same_transform": require_same_transform,
            },
        },
    )

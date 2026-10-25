
"""Reusable raster-based occurrence and spatial sampling utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


def map_occurrences_to_cells(
    occurrences,
    transform,
    valid_mask,
    *,
    longitude_col="decimalLongitude",
    latitude_col="decimalLatitude",
):
    """Map occurrences to valid raster cells, deduplicated by cell."""
    from rasterio.transform import rowcol, xy

    valid_mask = np.asarray(valid_mask, dtype=bool)
    if valid_mask.ndim != 2:
        raise ValueError("valid_mask must be 2-D.")

    missing = {
        longitude_col, latitude_col
    } - set(occurrences.columns)
    if missing:
        raise ValueError(f"Missing coordinate columns: {sorted(missing)}")

    coords = occurrences[[longitude_col, latitude_col]].copy()
    coords[longitude_col] = pd.to_numeric(
        coords[longitude_col], errors="coerce"
    )
    coords[latitude_col] = pd.to_numeric(
        coords[latitude_col], errors="coerce"
    )
    coords = coords.replace([np.inf, -np.inf], np.nan).dropna()
    coords = coords[
        coords[longitude_col].between(-180, 180)
        & coords[latitude_col].between(-90, 90)
    ]

    if coords.empty:
        return pd.DataFrame(
            columns=["row", "col", "longitude", "latitude"]
        )

    rows, cols = rowcol(
        transform,
        coords[longitude_col].to_numpy(),
        coords[latitude_col].to_numpy(),
    )
    coords["row"] = np.asarray(rows, dtype=int)
    coords["col"] = np.asarray(cols, dtype=int)

    height, width = valid_mask.shape
    inside = (
        coords["row"].between(0, height - 1)
        & coords["col"].between(0, width - 1)
    )
    coords = coords.loc[inside].copy()

    if coords.empty:
        return pd.DataFrame(
            columns=["row", "col", "longitude", "latitude"]
        )

    usable = valid_mask[
        coords["row"].to_numpy(), coords["col"].to_numpy()
    ]
    coords = coords.loc[usable].drop_duplicates(
        subset=["row", "col"]
    )

    if coords.empty:
        return pd.DataFrame(
            columns=["row", "col", "longitude", "latitude"]
        )

    centre_x, centre_y = xy(
        transform,
        coords["row"].to_numpy(),
        coords["col"].to_numpy(),
        offset="center",
    )

    return pd.DataFrame({
        "row": coords["row"].to_numpy(dtype=int),
        "col": coords["col"].to_numpy(dtype=int),
        "longitude": np.asarray(centre_x, dtype=float),
        "latitude": np.asarray(centre_y, dtype=float),
    }).reset_index(drop=True)


def sample_background_cells(
    valid_mask,
    presence_cells,
    *,
    n_background=2000,
    random_state=42,
):
    """Sample valid cells excluding presence cells, without replacement.

    Sampling is uniform by raster cell, not area-weighted.
    Background cells are not confirmed absences.
    """
    valid_mask = np.asarray(valid_mask, dtype=bool)
    if valid_mask.ndim != 2:
        raise ValueError("valid_mask must be 2-D.")
    if n_background < 1:
        raise ValueError("n_background must be positive.")
    if not {"row", "col"}.issubset(presence_cells.columns):
        raise ValueError("presence_cells needs row and col columns.")

    eligible = valid_mask.copy()
    height, width = eligible.shape

    if not presence_cells.empty:
        rows = presence_cells["row"].to_numpy(dtype=int)
        cols = presence_cells["col"].to_numpy(dtype=int)
        inside = (
            (rows >= 0) & (rows < height)
            & (cols >= 0) & (cols < width)
        )
        eligible[rows[inside], cols[inside]] = False

    candidates = np.flatnonzero(eligible.ravel())
    if n_background > len(candidates):
        raise ValueError(
            f"Requested {n_background} background cells; "
            f"only {len(candidates)} eligible cells exist."
        )

    rng = np.random.default_rng(random_state)
    selected = rng.choice(candidates, n_background, replace=False)
    rows, cols = np.unravel_index(selected, eligible.shape)

    return pd.DataFrame({
        "row": rows.astype(int),
        "col": cols.astype(int),
    })


def assign_spatial_blocks(
    longitude,
    latitude,
    *,
    block_degrees=0.2,
):
    """Assign coordinates to deterministic degree-based spatial blocks."""
    if not np.isfinite(block_degrees) or block_degrees <= 0:
        raise ValueError("block_degrees must be positive and finite.")

    lon = np.asarray(longitude, dtype=float)
    lat = np.asarray(latitude, dtype=float)

    if lon.shape != lat.shape:
        raise ValueError("Longitude and latitude shapes differ.")
    if not np.isfinite(lon).all() or not np.isfinite(lat).all():
        raise ValueError("Coordinates must be finite.")
    if ((lon < -180) | (lon > 180)).any():
        raise ValueError("Longitude outside [-180, 180].")
    if ((lat < -90) | (lat > 90)).any():
        raise ValueError("Latitude outside [-90, 90].")

    return pd.DataFrame({
        "block_x": np.floor(lon / block_degrees).astype(int),
        "block_y": np.floor(lat / block_degrees).astype(int),
    })


def spatial_train_test_split(
    data,
    *,
    test_size=0.2,
    random_state=42,
    block_degrees=0.2,
    longitude_col="longitude",
    latitude_col="latitude",
):
    """Return train/test labels while keeping spatial blocks separate."""
    from sklearn.model_selection import GroupShuffleSplit

    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1.")

    missing = {
        longitude_col, latitude_col
    } - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if len(data) < 2:
        raise ValueError("At least two rows are required.")

    blocks = assign_spatial_blocks(
        data[longitude_col].to_numpy(),
        data[latitude_col].to_numpy(),
        block_degrees=block_degrees,
    )
    groups = (
        blocks["block_x"].astype(str)
        + "_"
        + blocks["block_y"].astype(str)
    ).to_numpy()

    if len(np.unique(groups)) < 2:
        raise ValueError("At least two distinct spatial blocks are required.")

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=test_size,
        random_state=random_state,
    )
    train_idx, test_idx = next(
        splitter.split(np.zeros(len(data)), groups=groups)
    )

    if set(groups[train_idx]) & set(groups[test_idx]):
        raise RuntimeError("Spatial block leakage detected.")

    result = pd.Series(index=data.index, dtype="object", name="split")
    result.iloc[train_idx] = "train"
    result.iloc[test_idx] = "test"
    return result

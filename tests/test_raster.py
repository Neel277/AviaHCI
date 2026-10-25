import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_origin

from aviahci.raster import validate_raster_alignment


def create_raster(path, transform=None, width=4, height=3, crs="EPSG:4326"):
    if transform is None:
        transform = from_origin(5.0, 48.0, 0.01, 0.01)

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=width,
        height=height,
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=-9999.0,
    ) as dst:
        dst.write(np.ones((height, width), dtype=np.float32), 1)


def test_matching_rasters_pass_alignment(tmp_path):
    raster_a = tmp_path / "a.tif"
    raster_b = tmp_path / "b.tif"

    create_raster(raster_a)
    create_raster(raster_b)

    report = validate_raster_alignment([raster_a, raster_b])

    assert report.valid, report.errors


def test_mismatched_transform_fails_alignment(tmp_path):
    raster_a = tmp_path / "a.tif"
    raster_b = tmp_path / "b.tif"

    create_raster(raster_a)
    create_raster(
        raster_b,
        transform=from_origin(5.01, 48.0, 0.01, 0.01),
    )

    report = validate_raster_alignment([raster_a, raster_b])

    assert not report.valid
    assert report.errors


def test_mismatched_dimensions_fail_alignment(tmp_path):
    raster_a = tmp_path / "a.tif"
    raster_b = tmp_path / "b.tif"

    create_raster(raster_a)
    create_raster(raster_b, width=5)

    report = validate_raster_alignment([raster_a, raster_b])

    assert not report.valid
    assert report.errors


def test_empty_raster_list_is_handled():
    report = validate_raster_alignment([])

    assert not report.valid
    assert report.errors

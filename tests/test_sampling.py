
import numpy as np
import pandas as pd
import pytest
from rasterio.transform import from_origin

from aviahci.sampling import (
    map_occurrences_to_cells,
    sample_background_cells,
    assign_spatial_blocks,
    spatial_train_test_split,
)


def test_occurrences_map_to_unique_valid_cells():
    transform = from_origin(0, 2, 1, 1)
    mask = np.array([[True, True], [True, False]])
    records = pd.DataFrame({
        "lon": [0.5, 0.6, 1.5, 1.5, 5.0],
        "lat": [1.5, 1.4, 1.5, 0.5, 1.5],
    })
    result = map_occurrences_to_cells(
        records, transform, mask,
        longitude_col="lon", latitude_col="lat",
    )
    assert set(zip(result.row, result.col)) == {(0, 0), (0, 1)}


def test_background_is_reproducible_and_excludes_presence():
    mask = np.ones((10, 10), dtype=bool)
    presence = pd.DataFrame({"row": [0, 1], "col": [0, 1]})
    a = sample_background_cells(
        mask, presence, n_background=20, random_state=7
    )
    b = sample_background_cells(
        mask, presence, n_background=20, random_state=7
    )
    assert a.equals(b)
    assert len(a.drop_duplicates()) == 20
    assert not set(map(tuple, a.to_numpy())) & set(map(tuple, presence.to_numpy()))


def test_background_rejects_insufficient_eligible_cells():
    mask = np.array([[True, False]])
    presence = pd.DataFrame({"row": [0], "col": [0]})
    with pytest.raises(ValueError, match="eligible cells"):
        sample_background_cells(mask, presence, n_background=1)


def test_spatial_split_has_no_block_overlap():
    data = pd.DataFrame({
        "longitude": [0.1, 0.2, 1.1, 1.2, 2.1, 2.2, 3.1, 3.2],
        "latitude":  [0.1, 0.2, 1.1, 1.2, 2.1, 2.2, 3.1, 3.2],
    })
    split = spatial_train_test_split(
        data, test_size=0.25, random_state=42, block_degrees=0.2
    )
    train, test = data[split == "train"], data[split == "test"]
    train_blocks = assign_spatial_blocks(
        train.longitude, train.latitude
    )
    test_blocks = assign_spatial_blocks(
        test.longitude, test.latitude
    )
    assert set(map(tuple, train_blocks.to_numpy())).isdisjoint(
        set(map(tuple, test_blocks.to_numpy()))
    )
    assert set(split) == {"train", "test"}

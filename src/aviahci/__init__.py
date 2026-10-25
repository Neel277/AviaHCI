"""AviaHCI: reproducible habitat-change analysis tools."""

__version__ = "0.1.0"

from aviahci.raster import inspect_raster, validate_raster_alignment
from aviahci.validation import (
    ValidationReport,
    validate_occurrence_csv,
    validate_raster_paths,
)
from aviahci.sampling import (
    assign_spatial_blocks,
    map_occurrences_to_cells,
    sample_background_cells,
    spatial_train_test_split,
)
from aviahci.modeling import build_model, evaluate_model, fit_model

__all__ = [
    "__version__",
    "ValidationReport",
    "inspect_raster",
    "validate_occurrence_csv",
    "validate_raster_alignment",
    "validate_raster_paths",
    "assign_spatial_blocks",
    "map_occurrences_to_cells",
    "sample_background_cells",
    "spatial_train_test_split",
    "build_model",
    "evaluate_model",
    "fit_model",
]

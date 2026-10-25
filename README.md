# AviaHCI

**Reproducible, local-first tools for raster-based habitat analysis.**

AviaHCI provides utilities for validating occurrence data and raster inputs,
sampling presence/background locations, fitting habitat-discrimination models,
evaluating models with spatially separated splits, and documenting analysis
provenance.

The initial benchmark is Alpine Rock Ptarmigan in the Swiss Alps. This regional
case study does not, by itself, establish transferability to other species or
geographic regions.

## Current capabilities

- Occurrence CSV and raster validation.
- Raster inspection and alignment checks.
- Mapping occurrences to valid raster cells.
- Reproducible background-cell sampling.
- Geographic spatial-block assignment and spatial train/test splitting.
- Logistic Regression and Random Forest models.
- Discrimination and threshold-based evaluation metrics.
- Threshold sensitivity, predictor-range diagnostics, and temperature
  perturbation scenarios.
- Repeated spatial validation and background-sample-size sensitivity.
- JSON provenance sidecars containing input hashes and analysis settings.

## Installation

Use Python 3.10 or newer and work from the repository root.

Install the package and its modelling dependencies into the active environment:

```bash
python -m pip install -e ".[modeling]"
```

For raster functionality, install the geospatial extra as well:

```bash
python -m pip install -e ".[geospatial]"
```

For development tools:

```bash
python -m pip install -e ".[dev]"
```

If both modelling and geospatial features are required, install both extras:

```bash
python -m pip install -e ".[modeling,geospatial,dev]"
```

On Windows, use the project's `.venv` interpreter for commands if that is the
environment configured for this repository.

## Existing data-validation CLI

Inspect available commands with:

```bash
aviahci --help
```

Validate an occurrence CSV:

```bash
aviahci check-occurrences path/to/occurrences.csv
```

Inspect a raster:

```bash
aviahci inspect-raster path/to/predictor.tif
```

Check raster alignment:

```bash
aviahci check-rasters path/to/predictor_a.tif path/to/predictor_b.tif
```

Use `--help` on an individual command to see its supported options.

## Modelling CLI

Inspect modelling commands with:

```bash
aviahci-analysis --help
```

### Repeated spatial validation

Prepare a CSV containing:
- `longitude` and `latitude` in geographic decimal degrees;
- a binary target column, defaulting to `label` (`1` = presence, `0` = background);
- the numeric predictors specified through `--predictors`.

Example:

```bash
aviahci-analysis spatial-validation data/model_table.csv \
  --predictors temperature precipitation elevation \
  --target label \
  --model logistic_regression \
  --repeats 10 \
  --block-degrees 0.2 \
  --seed 42 \
  --output outputs/spatial_validation.csv
```

### Background-sampling sensitivity

Provide a presence CSV and a background-candidate CSV. Both must contain
longitude, latitude, and every requested predictor.

```bash
aviahci-analysis background-sensitivity \
  data/presences.csv data/background_candidates.csv \
  --predictors temperature precipitation elevation \
  --background-sizes 500 1000 2000 \
  --repeats 5 \
  --seed 42 \
  --output outputs/background_sensitivity.csv
```

The predictor names and sample sizes above are illustrative. Replace them with
columns and sample sizes appropriate to your prepared data.

## Outputs and provenance

Each successful modelling command writes a results CSV and a companion
`.provenance.json` sidecar. The provenance record includes the software and
Python versions, UTC creation time, input paths, input sizes, SHA-256 hashes,
analysis parameters, and output path.

Keep the results CSV and provenance sidecar together. File paths are specific
to the environment in which the run occurred.

## Scientific interpretation and limitations

- Presence-background discrimination is not equivalent to calibrated occupancy
  probability or confirmed species absence.
- Background-sampling strategy and candidate-pool composition can influence
  results.
- Spatial block size should be justified for the study region and sampling
  design. Geographic degree blocks have latitude-dependent physical dimensions.
- Predictor-range diagnostics identify univariate range exceedance; they do not
  detect every type of multivariate novelty.
- Temperature perturbation is a model-input scenario, not a climate projection.
- A regional Alpine Rock Ptarmigan benchmark does not demonstrate global
  transferability.

## Project status

The reusable components and CLI workflows are being integrated and will be
evaluated end to end against the real study data before the workflow is
considered validated. Capabilities listed here describe implemented modules,
not a claim that every combination has already been verified on the benchmark.

## Development

Run the development checks from the repository root using the project's
virtual environment:

```bash
python -m pytest
```

Final release checks should include an end-to-end run with real study inputs,
inspection of generated CSV and provenance files, and review of the Git diff
before committing or pushing.

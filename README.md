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

## Data Sources and Attribution

AviaHCI's Alpine Rock Ptarmigan research benchmark uses environmental datasets from external providers. These datasets are separate from the AviaHCI software and retain their respective attribution requirements and terms of use.

### ERA5-Land

Climate data used in the research workflow were sourced from **ERA5-Land**, provided by the Copernicus Climate Change Service (C3S).

**Dataset reference:**

Muñoz Sabater, J. et al. (2021). ERA5-Land: A state-of-the-art global reanalysis dataset for land applications. *Earth System Science Data*, 13, 4349–4383.

https://doi.org/10.5194/essd-13-4349-2021

Climate Data Store dataset: https://doi.org/10.24381/cds.e2161bac

**Attribution:** Contains modified Copernicus Climate Change Service information. Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.

### Shuttle Radar Topography Mission (SRTM)

Elevation data used in the research workflow were sourced from the **Shuttle Radar Topography Mission (SRTM)**.

For the NASA SRTM Global 1 arc-second Version 003 product:

NASA JPL (2013). *NASA Shuttle Radar Topography Mission Global 1 arc second*. NASA Land Processes Distributed Active Archive Center.

https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003

*Note: Confirm the exact SRTM product and version used in the benchmark before finalizing this citation.*

### Dataset and Software Licensing

The AviaHCI software licence applies to the software, subject to the rights and terms applicable to the included materials. It does not replace or override the terms governing external datasets.

External datasets are not included with the software unless explicitly stated. Users should obtain data from the respective providers and comply with applicable attribution, citation, and usage requirements.


Final release checks should include an end-to-end run with real study inputs,
inspection of generated CSV and provenance files, and review of the Git diff
before committing or pushing.

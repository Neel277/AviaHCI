# AviaHCI example workflows

These commands illustrate the CLI. Replace placeholder paths and predictor
names with columns that actually exist in your prepared CSV files.

## 1. Repeated spatial validation

The input CSV must contain:
- `longitude` and `latitude` in geographic decimal degrees;
- a binary target column, default name `label` (1 = presence, 0 = background);
- the numeric predictor columns passed to `--predictors`.

Run from the repository root after installing AviaHCI in the active environment:

```bash
aviahci-analysis spatial-validation data/model_table.csv ^
  --predictors temperature precipitation elevation ^
  --target label ^
  --model logistic_regression ^
  --repeats 10 ^
  --block-degrees 0.2 ^
  --seed 42 ^
  --output outputs/spatial_validation.csv
```

On macOS/Linux, replace the Windows `^` line continuations with `\`.

## 2. Background-sampling sensitivity

The presence and background CSV files must each contain longitude, latitude,
and all specified predictor columns. The background file is the candidate pool
from which rows are sampled.

```bash
aviahci-analysis background-sensitivity data/presences.csv data/background_candidates.csv ^
  --predictors temperature precipitation elevation ^
  --background-sizes 500 1000 2000 ^
  --repeats 5 ^
  --seed 42 ^
  --output outputs/background_sensitivity.csv
```

Each successful run writes a results CSV and a corresponding
`.provenance.json` file.

## Scientific cautions

- Example predictor names and sample sizes are placeholders.
- Spatial block size should be justified by study geography and sampling design.
- Presence-background discrimination is not equivalent to calibrated occupancy.
- Background selection influences results and should be documented.
- A regional Alpine Rock Ptarmigan benchmark does not establish global
  transferability.

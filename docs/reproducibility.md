# Reproducibility and interpretation

## Recorded provenance

The analysis CLI writes a JSON sidecar alongside each results CSV. It records
the AviaHCI version, Python version, platform, UTC creation time, input file
paths, input file sizes, SHA-256 hashes, analysis parameters, and output path.

Input hashes allow a researcher to verify whether the input files are identical
to those used in a recorded run. Paths describe the original execution
environment and may need to be updated when reproducing on another machine.

## Spatial validation

AviaHCI supports repeated spatially separated train/test splits. Report the
configured block size, split fraction, random seeds, predictors, and model
settings. Geographic degree blocks have latitude-dependent physical dimensions;
the block scale must be justified for the study area.

## Presence-background interpretation

A presence-background model distinguishes observed presences from sampled
background locations. Its output scores should not automatically be described
as calibrated occupancy probabilities or proof of species absence.

Results depend on occurrence-data quality, background-pool construction,
predictor resolution, sampling bias, spatial validation design, and threshold
choice.

## Extrapolation and scenarios

Univariate predictor-range diagnostics flag values outside training ranges.
They do not detect every form of multivariate novelty or establish ecological
validity.

Temperature perturbation is a specified model-input scenario, not a climate
projection. Interpret results only within the perturbation range and assumptions
used.

## Benchmark scope

The Alpine Rock Ptarmigan analysis is a regional benchmark for developing and
evaluating the workflow. It does not by itself demonstrate transferability to
other species, ecosystems, or countries.

## Before publishing results

1. Record the occurrence source, download date, filters, and coordinate checks.
2. Record predictor source, resolution, units, time period, and preprocessing.
3. Justify the background sampling strategy and spatial block scale.
4. Report repeated-split variability as well as average metrics.
5. Keep the results CSV and provenance JSON together.
6. Distinguish measured results from assumptions and proposed future extensions.

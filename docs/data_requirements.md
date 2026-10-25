# Data requirements

AviaHCI is being developed as a local-first toolkit for reproducible
habitat-change analysis. Input validation is an early step; passing
validation does not establish ecological suitability or model validity.

## 1. Occurrence table

Provide a CSV or tab-delimited text file with:

- Longitude: numeric decimal degrees, from -180 to 180.
- Latitude: numeric decimal degrees, from -90 to 90.

Recommended fields include observation date or year and a species identifier.
If configured, their column names must match the names in the source table.

AviaHCI currently checks coordinate columns, missing or non-numeric
coordinates, coordinate ranges, repeated coordinate pairs, and configured
optional columns. Repeated coordinates are flagged rather than automatically
removed because they may represent legitimate observations.

Coordinate-range checks do not verify the coordinate reference system,
positional accuracy, or whether a point is located in the intended study area.

## 2. Environmental rasters

Environmental predictors should be supplied as readable raster files,
commonly GeoTIFFs.

For a multi-raster analysis, inspect and document:

- Coordinate reference system (CRS).
- Raster width and height.
- Grid transform and pixel resolution.
- Spatial bounds.
- NoData conventions.
- Temporal reference period and units of each predictor.

AviaHCI currently provides metadata inspection and strict grid-alignment
checks. These checks do not reproject, resample, harmonize NoData masks,
or determine temporal compatibility.

## 3. Study boundary

A study boundary is recommended for restricting analysis and documenting
the intended geographic extent. Boundary ingestion and geometry validation
are not yet implemented in this initial validation layer.

## 4. Privacy and reproducibility

Keep raw occurrence coordinates and source datasets local unless sharing
is intentional and permitted by the data license and applicable rules.
Do not assume occurrence data may be redistributed publicly.

Record data sources, licenses, temporal coverage, coordinate reference
systems, preprocessing choices, model settings, and software versions.
Do not publish sensitive location data in reports by default.

## 5. Interpretation

Occurrence records and background points do not establish confirmed
absences. Scores from presence-background classification must not be
described as calibrated occupancy probabilities without suitable
calibration and validation.

Passing technical input checks does not demonstrate transferability to
other species, regions, time periods, or environmental conditions.

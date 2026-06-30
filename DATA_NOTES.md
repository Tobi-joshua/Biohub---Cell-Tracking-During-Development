# Data notes

## Training data

- `.zarr` image volumes
- Paired `.geff` graph annotations (sparse centroid labels)

## Test data

- `.zarr` image volumes only

## Volume format

- Shape: `(T, Z, Y, X)`
- One timepoint per Zarr chunk
- Physical voxel scale:
  - Z = 1.625 µm/voxel
  - Y = 0.40625 µm/voxel
  - X = 0.40625 µm/voxel

## Ground truth

- Nodes contain centroid coordinates `(t, z, y, x)`
- Edges link cells across time
- Labels are sparse — a missing label does not imply absence of a cell

## Lineage export format

- **Node rows:** `node_id`, `t`, `z`, `y`, `x` (coordinates ≥ 0)
- **Edge rows:** `source_id`, `target_id` (node coordinates set to −1)
- Combined CSV with `row_type` column (`node` or `edge`)

See `src/biohub/export.py` and `src/biohub/submission.py` for writers.

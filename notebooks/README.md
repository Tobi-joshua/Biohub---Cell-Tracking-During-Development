# Submission notebook

## Generate (local)

From the repo root:

```bash
python scripts/build_notebook.py
```

Creates: `notebooks/biohub-cell-tracking-submission.ipynb` (self-contained, current pipeline).

## Use in a hosted notebook environment

### Option A — Update an existing notebook

1. Run `python scripts/build_notebook.py` locally.
2. Upload `notebooks/biohub-cell-tracking-submission.ipynb` to your notebook platform.
3. Attach the Biohub dataset as read-only input (train + test splits).
4. Run all cells → produces `submission.csv`.

### Option B — New notebook

1. Generate the notebook locally (above).
2. Create a new notebook on your platform and upload the `.ipynb`.
3. Add the dataset, run all cells, download or submit `submission.csv`.

## Settings to tune (config cell)

```python
CFG = CFG.copy_with(
    thresh_rel=0.30,
    max_link_dist_um=11.0,
    gap_close_enabled=True,
    gap_close_dist_um=15.0,
    prune_soft_neighbors=True,
    run_hyperparameter_search=False,
)
```

## Output

- `submission.csv` with `node` and `edge` rows
- Automatic format validation when test data paths are available

`Config.resolve_paths()` auto-detects common hosted input directory layouts.

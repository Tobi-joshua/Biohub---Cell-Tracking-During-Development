# Submission notebook

## Generate (local)

From the repo root:

```bash
python scripts/build_notebook.py
```

Creates: `notebooks/biohub-cell-tracking-submission.ipynb` (self-contained, pipeline v1.5).

## Use on Kaggle

### Option A — Update your existing notebook (fastest)

1. `git pull` the latest repo (or copy cells from the generated `.ipynb`).
2. On Kaggle, open **biohub-cell-tracking-submission_by_tobi_joshua**.
3. **File → Upload notebook** and replace with the new `.ipynb`,  
   **or** paste updated code cells from the generated notebook into your current one.
4. **Add data** → competition dataset **Biohub - Cell Tracking During Development**.
5. **Save Version → Save & Run All (Commit)**.
6. When finished, **Submit** from the notebook output.

### Option B — New notebook from GitHub

1. Generate locally: `python scripts/build_notebook.py`
2. Kaggle → **New Notebook** → **File → Upload notebook**
3. Upload `notebooks/biohub-cell-tracking-submission.ipynb`
4. Add competition dataset, run all, submit.

## Settings to tune (last code cell before run)

```python
CFG = CFG.copy_with(
    thresh_rel=0.30,           # detection sensitivity
    max_link_dist_um=11.0,
    gap_close_enabled=True,
    gap_close_dist_um=15.0,
    prune_soft_neighbors=True,
    run_hyperparameter_search=False,  # True = slow train grid search
)
```

## Output

- `/kaggle/working/submission.csv` on Kaggle
- Validated automatically if `validate_submission` passes

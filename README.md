# Biohub - Cell Tracking During Development

Kaggle competition workspace. **Current public score: 0.607** (classical baseline).

## Quick start

1. Open `notebooks/biohub-cell-tracking-submission.ipynb` on Kaggle
2. Add competition data, run all cells
3. Submit `submission.csv`

## Pipeline versions

| Version | Module | What changed |
|---------|--------|--------------|
| **v1.1** | `detection.py` | Dense-cluster second peak pass, adaptive frame threshold, `min_z_hard`, intensity sampling |
| **v1.2** | `tracking.py` | Link cost = distance + motion + intensity + kNN neighborhood signature |
| **v1.3** | `tracking.py` | Division midpoint gate, `div_min_count_gain=0`, wider sister distance |
| **v1.4** | `tuning.py` | Grid search on train recall/edge/division proxies |
| **v2.0** | `detector.py` | `LearnedDetector` scaffold for Cellpose / StarDist / 3D U-Net weights |

## Layout

```
notebooks/biohub-cell-tracking-submission.ipynb   # Kaggle notebook
src/biohub/                                         # pipeline source
scripts/build_notebook.py                           # regenerate notebook
```

## Regenerate notebook

```bash
python scripts/build_notebook.py
```

## Tuning on Kaggle

```python
CFG.run_hyperparameter_search = True   # ~5-10 min extra on train
CFG.run_hyperparameter_search = False  # fast submit (~2 min)
```

## v2.0 learned detector (next)

Attach public weights as a Kaggle dataset, subclass `LearnedDetector`, set:

```python
CFG.detector_backend = "learned"
```

Keep the tracking module unchanged.

## References

- van der Walt et al., scikit-image, PeerJ 2014
- Kuhn, The Hungarian Method, Naval Research Logistics 1955

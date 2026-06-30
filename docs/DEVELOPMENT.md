# Development notes

Engineering notes for pipeline tuning and evaluation. For end users, see `README.md`.

## Sprint 2 (competition track)

See **`EXPERIMENTS.md`** for V4/V5 regression analysis and V6 submission workflow.  
Full Sprint 2 report: **`docs/SPRINT2_ENGINEERING_REPORT.md`**

```bash
python scripts/build_notebook.py          # v6 notebook, v4 preset
python scripts/run_diagnostics.py --synthetic --preset v4
python scripts/run_hyperparameter_search.py --train-dir /path/to/train
```

## Pipeline versions

| Version | Highlights |
|---------|------------|
| v1.6 | Competition preset = v4 baseline; v1.5 experiments opt-in |
| v1.0 | Publication release — app, paper, batch export |

## Tuning

```bash
python scripts/run_hyperparameter_search.py --train-dir /path/to/train
python scripts/run_validation.py --train-dir /path/to/train
```

Outputs land in `results/`.

## Known limitations

- Classical peak detection in dense clusters
- Greedy frame-to-frame linking (no multi-frame ILP)
- Sparse training labels limit offline metric fidelity

## Future work

- Learned detector integration (`LearnedDetector` scaffold exists)
- Marker-controlled watershed for dense peaks
- Multi-frame track linking

See `CHANGELOG.md` for version history.

# Development notes

Engineering notes for pipeline tuning and evaluation. For end users, see `README.md`.

## Pipeline versions

| Version | Highlights |
|---------|------------|
| v1.0 | Publication release — app, paper, batch export, validation |
| v1.5 | Gap closing, soft prune, adaptive threshold fix, tuning scripts |

## Evaluation baseline

Internal batch benchmark reference score: **0.659** (sparse-label proxy on development data).

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

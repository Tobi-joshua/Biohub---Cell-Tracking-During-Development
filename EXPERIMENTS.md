# Experiments & Engineering Report

**Baseline:** pipeline v1.4, public leaderboard **0.659** (Kaggle notebook v4).  
**Target:** incremental gains without replacing the classical architecture.

---

## Phase 1 — Repository audit

### Strengths
- Anisotropy-aware detection (XY downsample + physical NMS)
- Dense-cluster second pass for overlapping cells
- Rich Hungarian linking (distance + motion + intensity + neighborhood)
- Streaming Zarr I/O, modular `biohub` package, Streamlit + batch export
- Density calibration on train metadata

### Weaknesses / bottlenecks
| Issue | Metric impact |
|-------|----------------|
| Peak detection (no segmentation) | Node recall/precision in dense clusters |
| Greedy frame-to-frame linking | Edge Jaccard, identity switches |
| No gap closing | Broken trajectories → lost nodes after prune |
| Hard isolated-node prune | Node recall when linking fails |
| Adaptive threshold bug (v1.4) | Unstable per-frame counts |
| Heuristic divisions | Division Jaccard false pos/neg |
| Sparse train labels | Limits tuning fidelity |

---

## Phase 2 — Error analysis

### Detection
| Failure | Why it hurts score |
|---------|-------------------|
| False positives | Extra nodes dilute matching; bad edges |
| False negatives | Missing nodes → missing edges/divisions |
| Merged peaks | One node for two cells |
| Border artifacts | Spurious nodes near tissue edge |
| Threshold sensitivity | Frame-to-frame count drift |

### Tracking
| Failure | Why it hurts score |
|---------|-------------------|
| Broken trajectories | Edge recall drops |
| Identity switches | Wrong edge topology |
| No gap closing | Cells lost for 1 frame → isolated prune |
| Excessive link distance | Wrong assignments in dense regions |

### Divisions
| Failure | Why it hurts score |
|---------|-------------------|
| Missed mitosis | Division metric recall |
| False mitosis | Division precision |
| Asymmetric daughters | Parent ambiguity |

---

## Phase 3 — Improvement roadmap

### High impact (implemented in v1.5)
| Change | Difficulty | Expected gain | Runtime |
|--------|------------|---------------|---------|
| Fix adaptive threshold | Low | Low–medium | +0–5% per retry frame |
| Gap closing (1 frame) | Medium | Medium | +5–10% linking pass |
| Soft orphan pruning | Low | Medium (node recall) | Negligible |
| Division symmetry gate | Low | Low–medium | Negligible |
| Expanded hyperparameter search | Low | Medium (with train data) | Offline only |

### Medium impact (future)
| Change | Difficulty | Expected gain |
|--------|------------|---------------|
| Marker-controlled watershed on dense peaks | Medium | Medium–high |
| 2-frame gap / ILP linking | High | High |
| Learned detector (Cellpose/StarDist) | High | Very high |
| Train spatial recall tuning (not just count) | Medium | Medium |

### Low impact
| Change | Notes |
|--------|-------|
| `xy_ds=2` | Better separation, slower |
| Vectorized intensity sampling | Speed only |

---

## Phase 7 — Hyperparameter search

```bash
python scripts/run_hyperparameter_search.py --train-dir /path/to/train
```

Output: `results/hyperparameter_search.csv` with parameters, `mean_score`, `runtime_s`, per-sample recall/edge proxy.

Grid (v1.5): `thresh_rel` × `max_link_dist_um` × `div_parent` × `div_sister` × `nms_radius_um` → 144 combinations (default 3 samples × 4 frames).

Enable in batch pipeline:

```python
cfg = Config(run_hyperparameter_search=True, train_dir=Path(".../train"))
```

---

## Phase 8 — Local validation

```bash
python scripts/run_validation.py --train-dir /path/to/train
```

Writes:
- `results/validation_proxy.csv` — sparse-label proxy per sample
- `results/validation_summary.csv` — nodes, edges, divisions, link distances, runtimes

---

## Recommended next experiment (Kaggle notebook)

1. Sync notebook config from repo v1.5 defaults.
2. Run with `gap_close_enabled=True`, `prune_soft_neighbors=True`.
3. Enable hyperparameter search on train (or manually set best row from CSV).
4. Compare node/edge/division counts vs v4 (0.659) on one test volume.
5. Submit as v5; select best of v4/v5 on leaderboard.

### Parameters to A/B on Kaggle (manual)
```
thresh_rel:        0.28 – 0.32
max_link_dist_um:  10.5 – 11.5
gap_close_dist_um: 14 – 16
div_sister_dist_um: 7.0 – 8.0
prune_soft_neighbors: True / False
```

---

## Expected impact (v1.5)

| Component | Estimate |
|-----------|----------|
| Adaptive threshold fix | +0.005 – 0.015 |
| Gap closing | +0.01 – 0.03 (edge recall) |
| Soft prune | +0.005 – 0.02 (node recall) |
| Division symmetry | +0.002 – 0.01 |
| **Combined (optimistic)** | **+0.02 – 0.05** → ~0.68 – 0.71 |

*Estimates are heuristic; validate with Kaggle submission.*

---

## Runtime (v1.5 vs v1.4)

- Gap closing: one extra linking pass over unmatched nodes — ~5–10% wall time on full test set.
- Adaptive retry: at most one extra detection pass per frame when over cap — rare.
- Hyperparameter search: offline; not in submission hot path.

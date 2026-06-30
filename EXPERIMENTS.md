# Experiments — Sprint 2 Leaderboard Optimization

Evidence-based engineering log for the classical competition pipeline.

## Leaderboard evidence

| Notebook version | Public score | Pipeline basis |
|------------------|-------------|----------------|
| V2 | 0.607 | Early v1.x calibration |
| **V4** | **0.659** | **v1.4 — current best** |
| V5 | 0.648 | v1.5 — **regression** |
| V6 (target) | TBD | v4 baseline + one-knob tuning |

**Rule:** Do not add features without A/B evidence. V6 is built on V4, not V5.

---

## Phase 2 — V4 vs V5 code comparison

V5 used repository commit `6682370` (pipeline v1.5). V4 aligned with v1.4 (`8c19f55`) plus notebook-specific `thresh_rel` from density calibration.

### Changes in v1.5 (V5) not present in v1.4 (V4)

| Change | File | Expected effect | Likely LB impact |
|--------|------|-----------------|------------------|
| **Gap closing** (`t-2 → t`, 15 µm gate) | `tracking.py`, `submission.py` | Recover missed links | **Negative** — long-range false edges, wrong topology, extra division candidates via `link_frames` |
| **Soft orphan pruning** | `tracking.py` | Keep nodes near neighbors without edges | **Negative** — extra unmatched nodes hurt node precision / graph consistency |
| **Division symmetry penalty** (`weight=0.35`) | `tracking.py` | Penalize asymmetric daughters | **Mixed/negative** — may skip true mitosis or reorder daughter assignment |
| **Adaptive threshold retry** (bug fix) | `detection.py` | Tighten threshold when over count cap | **Mixed** — can reduce FPs but also drop true cells vs V4 (where retry never ran) |
| Hyperparameter grid expansion | `tuning.py` | Offline only if disabled | Neutral if `run_hyperparameter_search=False` |

### Regression hypothesis (ranked)

1. **Gap closing** — highest risk: adds edges outside the v4 Hungarian window, pollutes edge Jaccard and division graph.
2. **Soft pruning** — retains detections that v4 would drop; increases false nodes.
3. **Adaptive retry** — changes per-frame counts vs frozen v4 behavior.
4. **Division symmetry** — smaller effect; may reduce division recall.

**Conclusion:** V6 defaults **disable all four** via `competition_v4_preset()`.

---

## Phase 3 — Error analysis (metric mapping)

| Issue | Affects |
|-------|---------|
| False positive detections | Node precision, spurious edges |
| False negative detections | Node recall, broken tracks |
| False edges (gap close, long gate) | Edge Jaccard |
| Missing edges | Edge recall |
| False divisions | Division metric precision |
| Missed divisions | Division metric recall |
| Isolated nodes after prune | Node recall if true cells unlinked |

---

## Phase 4 — Improvement ranking (post-regression)

| Improvement | Expected LB gain | Difficulty | Runtime | Risk |
|-------------|------------------|------------|---------|------|
| **Revert to v4 preset (V6)** | Recover ~0.659 baseline | Low | Same | Low |
| **Hyperparameter search on train** (thresh, link, div) | +0.01–0.03 | Medium | Offline | Low |
| **Single-knob thresh_rel sweep** after calibration | +0.005–0.015 | Low | Low | Low |
| Re-enable gap close with tighter gate (13 µm) | Unknown | Low | +5% | **High** |
| Re-enable soft prune | Unknown | Low | Same | **High** |
| Learned detector | Large | High | High | Medium |

**Implement now:** v4 preset only. Tune via `run_hyperparameter_search.py`, one knob per submission.

---

## Phase 5–7 — What we did NOT implement

No new detection/tracking/division algorithms in Sprint 2. Feature adds caused V5 regression.

---

## Phase 8 — Hyperparameter search

```bash
python scripts/run_hyperparameter_search.py --train-dir /path/to/train
```

Output: `results/hyperparameter_search.csv`

Apply **one** parameter change per submission attempt. Compare against V4 baseline.

---

## Phase 9 — Local diagnostics

```bash
# V4 preset (default)
python scripts/run_diagnostics.py --synthetic --preset v4

# Compare against V5 settings locally
python scripts/run_diagnostics.py --synthetic --preset v5

# With train data
python scripts/run_diagnostics.py --train-dir /path/to/train --preset v4
```

Plots in `results/diagnostics/`: detections/frame, track lengths, link distances, divisions, node density, scores.

### Synthetic A/B (local)

| Metric | v4 preset | v5 preset | Interpretation |
|--------|-----------|-----------|----------------|
| Nodes | 109 | 163 | Soft prune + gap close retain extra graph nodes |
| Edges | 95 | 149 | Gap closing adds long-range false links (+57%) |
| Divisions | 5 | 5 | Same on synthetic; real data may differ |
| Detections/frame | ~13.6 | ~13.6 | Adaptive retry did not change count on synthetic |

---

## V6 submission workflow

```bash
python scripts/build_notebook.py
```

Notebook applies `CFG.competition_v4_preset()` automatically.

`build_submission()` applies the same preset when `use_competition_preset=True` (default).

### Opt-in v1.5 experiments (offline A/B only)

```python
CFG = Config(use_competition_preset=False).copy_with(
    gap_close_enabled=True,  # test one flag at a time
)
```

---

## Track A vs Track B

| Track | Focus |
|-------|--------|
| **A — Competition** | `submission.py`, notebook, `EXPERIMENTS.md`, preset tuning |
| **B — Research** | Streamlit app, paper, `main` docs — no experimental flags in defaults |

---

## Runtime comparison

| Setting | Relative runtime |
|---------|------------------|
| V4 preset | 1.0× (baseline) |
| V5 (+ gap close) | ~1.05–1.10× |

---

## Risk assessment (V6)

| Risk | Mitigation |
|------|------------|
| V6 matches V4 but not beat it | Run hyperparameter search; single-knob commits |
| Overfitting train proxy | Validate with public LB one change at a time |
| Re-enabling v1.5 flags | Only via explicit opt-in, never default |

---

## Expected leaderboard impact

| Action | Estimate |
|--------|----------|
| V6 = V4 preset | **~0.659** (recover V5 regression) |
| + tuned thresh_rel / link gate | +0.005–0.02 |

Validate with **one submission** (V6). Do not batch multiple changes.

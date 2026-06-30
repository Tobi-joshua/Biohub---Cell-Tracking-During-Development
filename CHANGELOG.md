# Changelog

## v1.5 — Pipeline improvements (target: >0.659 leaderboard)

### Detection
- **Fixed adaptive threshold bug:** previously passed `n_detected=0`, so overcount penalty never applied. Now retries with a tighter threshold when a frame exceeds the adaptive cap.
- Refactored detection into `_extract_from_sm` for a clean single-pass + optional retry.

### Tracking
- **Gap closing:** `close_frame_gaps` links unmatched nodes across one skipped frame (`t-2 → t`) within `gap_close_dist_um` (default 15 µm).
- **Soft isolated-node pruning:** keeps detections without edges if a neighbor exists in `t±1` within `prune_neighbor_dist_um` (default 9 µm).
- **Division symmetry cost:** penalizes asymmetric parent–daughter distances when scoring mitosis candidates.

### Tuning & validation
- Expanded hyperparameter grid (`thresh_rel`, linking, division, `nms_radius_um`).
- Search results include `runtime_s` and `n_samples`; saved to `results/hyperparameter_search.csv`.
- New `biohub.validation` module and `scripts/run_validation.py` for local proxy metrics.

### Configuration (new defaults)
| Parameter | Default | Purpose |
|-----------|---------|---------|
| `gap_close_enabled` | `True` | Enable 1-frame gap closing |
| `gap_close_dist_um` | `15.0` | Extended link gate for gaps |
| `prune_soft_neighbors` | `True` | Keep near-neighbor orphans |
| `prune_neighbor_dist_um` | `9.0` | Spatial gate for soft prune |
| `div_symmetry_weight` | `0.35` | Division daughter symmetry penalty |

### Unchanged
- Submission CSV schema
- Streamlit app API
- Detector backend interface

### Risks
- Gap closing may add false long-range links in very dense tissue.
- Soft pruning retains more nodes → possible false-positive nodes if linking fails.
- Hyperparameter grid is larger → longer offline tuning runs.

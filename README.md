# Biohub - Cell Tracking During Development

Kaggle competition workspace for building a submission notebook for **Biohub - Cell Tracking During Development**.

## Goal

Detect cells in 3D time-lapse microscopy volumes, track them across frames, and reconstruct cell lineage graphs with correct division events.

## Repository layout

| Path | Purpose |
|------|---------|
| `notebooks/biohub-cell-tracking-submission.ipynb` | **Final Kaggle submission notebook** |
| `src/biohub/` | Reusable pipeline modules (data, detection, tracking, submission) |
| `scripts/build_notebook.py` | Regenerate notebook from `src/biohub/` |
| `starter_notebooks/` | Competition starter notebooks (reference only) |
| `COMPETITION_RULES.md` | Rules summary |
| `DATA_NOTES.md` | Data format notes |

## Pipeline summary

1. **Detection** — full-Z + XY block-mean (÷4), Gaussian smooth, Otsu/relative threshold, local maxima, intensity-weighted centroid refinement, physical NMS
2. **Linking** — Hungarian assignment on physical distances (≤11 µm gate)
3. **Divisions** — second daughter for parents with one child, sister-distance and continuation checks
4. **Pruning** — remove isolated single-frame detections
5. **Calibration** — sweep `thresh_rel` on train `estimated_number_of_nodes`

## Notebook requirements

- Must run on Kaggle (no internet)
- Output: `submission.csv`
- Runtime target: under 12 hours (typically ~1 min on CPU for public test split)

## Regenerate notebook

```bash
python scripts/build_notebook.py
```

## References

- van der Walt et al., scikit-image, PeerJ 2014
- Kuhn, The Hungarian Method, Naval Research Logistics 1955
- Competition starter notebooks in `starter_notebooks/`
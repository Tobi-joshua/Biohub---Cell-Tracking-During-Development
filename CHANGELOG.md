# Changelog

All notable changes to **Biohub Cell Lineage Tracker** are documented here.

## [1.7.0] — 2026-07-03 (V10 DoG detection experiment)

### Added
- **DoG band-pass preprocessing** in `detection.py` (`dog_bandpass`, `preprocess_detection_volume`)
- `Config.competition_v10_dog_preset()` — v4 tracking + DoG detection front-end
- `peaks_dog` detector backend and `DogPeakDetector`
- Notebook `USE_V10_DOG` toggle and optional `V10_DOG_OVERRIDES`

### Unchanged
- V7 baseline (`competition_v4_preset`, `USE_V10_DOG=False`) — still the default at 0.659

---

## [1.6.0] — 2026-06-30 (Sprint 2 — competition)

### Changed
- **Default submission preset reverts to v4 baseline** (leaderboard 0.659)
- v1.5 features (`gap_close`, `soft prune`, `div symmetry`, adaptive retry) **default OFF**
- `Config.competition_v4_preset()` and `use_competition_preset=True` in `build_submission()`
- Notebook v6/v7 uses v4 preset; see `EXPERIMENTS.md` for V4 vs V5 analysis
- **V7 Kaggle submission confirmed 0.659** — regression recovery validated

### Added
- `scripts/run_diagnostics.py` — local diagnostic plots (v4 vs v5 preset compare)
- `EXPERIMENTS.md` — evidence-based engineering log
- `docs/SPRINT2_ENGINEERING_REPORT.md` — full Sprint 2 phases 1–11 report
- `scripts/run_single_knob_sweep.py` and notebook sweep cells for safer V8+ tuning

### Not changed
- Streamlit app (Track B) — experimental flags available via `Config.copy_with()`
- Core algorithms remain; only defaults and submission path preset

---

## [1.0.0] — 2026-06-30

Publication release.

### Added
- Interactive Streamlit application with local dataset browser
- Core pipeline: detection, Hungarian linking, division inference, export
- IEEE manuscript (`paper/`) and figure generation scripts
- Public live demo (Streamlit Community Cloud)
- Batch submission notebook builder
- Hyperparameter search and validation utilities
- Overleaf bundle script (`scripts/prepare_overleaf.py`)
- `CONTRIBUTING.md`, `CITATION.cff`, documentation

### Pipeline highlights (v1.5 implementation)
- Gap closing across one missed frame
- Soft neighbor-aware orphan pruning
- Adaptive detection threshold retry
- Division symmetry scoring
- Expanded offline tuning grid

---

## [0.5.0] — 2026-06 (development)

- Pipeline v1.4: rich linking, division detection, train calibration
- Local Zarr/GEFF dataset catalog
- Visualization and export modules

## [0.1.0] — 2026-06 (development)

- Initial modular Python package
- Batch lineage CSV export
- Anisotropy-aware peak detection

[1.0.0]: https://github.com/Tobi-joshua/Biohub---Cell-Tracking-During-Development/releases/tag/v1.0.0

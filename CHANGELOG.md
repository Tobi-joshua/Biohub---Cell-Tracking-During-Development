# Changelog

All notable changes to **Biohub Cell Lineage Tracker** are documented here.

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

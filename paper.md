---
title: 'Biohub Cell Lineage Tracker: Interactive 3D cell tracking and lineage reconstruction for fluorescence microscopy'
tags:
  - Python
  - cell tracking
  - lineage reconstruction
  - light-sheet microscopy
  - image analysis
  - Streamlit
authors:
  - name: Tobi-Joshua Samuel
    affiliation: 1
    corresponding: true
affiliations:
  - index: 1
    name: Independent Researcher, Nigeria
date: 24 October 2026
bibliography: paper.bib
---

# Summary

Three-dimensional time-lapse fluorescence microscopy records how cells move, divide, and organize during development.
Turning raw image stacks into reproducible lineage graphs still requires specialized detection, data association, and quality review.
Biohub Cell Lineage Tracker is an open-source Python package and Streamlit application that detects cell centroids in anisotropic 3D frames, links them across time with a multi-cue assignment solver, and infers mitosis events when a parent links to two nearby daughters.
Users can browse local Zarr or GEFF-formatted volumes, inspect overlays and timelines in a browser, export CSV and JSON lineage tables, and run the same pipeline headlessly for batch processing.
The design targets developmental biologists and computational imaging researchers who need an inspectable classical baseline rather than a closed black-box tracker.

# Statement of need

Live-imaging experiments in model organisms such as zebrafish produce four-dimensional datasets with tens of thousands of voxels per frame and hundreds of time points.
Manual lineage tracing is accurate but slow and difficult to audit at scale.
Existing tools span GUI-centric particle trackers, deep learning segmenters, and competition-oriented batch pipelines, yet researchers often still need a transparent workflow that connects **volume inspection**, **parameter tuning**, and **graph export** in one place.

Biohub Cell Lineage Tracker addresses this gap for the Biohub Cell Tracking During Development setting: anisotropic light-sheet volumes stored as Zarr, optional sparse GEFF graph labels for calibration, and competition-style CSV submissions.
The software solves three recurring tasks: (1) centroid detection that respects physical Z–XY spacing, (2) robust frame-to-frame linking with optional division inference, and (3) interactive validation before exporting lineage graphs for downstream analysis or publication figures.

The primary audience is researchers working with similar fluorescence time-lapse volumes who want a documented, modifiable pipeline and a no-install demo for teaching or outreach.
The package does not replace full manual curation or learned segmenters when those are required; it provides a reproducible classical core with clear extension points for learned detectors.

# State of the field

Particle tracking in bioimaging is mature.
TrackMate integrates detection and linking inside Fiji/ImageJ and remains a standard reference for interactive single-particle tracking [@tinevez2017trackmate].
Lineage-focused systems such as the lineaging approach of Amat *et al.* emphasize linking at scale on large movies [@amat2014lineage].
Deep learning tools—including Cellpose and 3D U-Net—improve segmentation when training data exist [@stringer2021cellpose; @cicek20163dunet].
Scikit-image furnishes the peak-finding and filtering primitives used in many classical pipelines [@van2014scikit].

Biohub Cell Lineage Tracker deliberately **builds** rather than **contributes** to those codebases: it is not a TrackMate plugin or Cellpose fork.
Its scholarly niche is an integrated **Python 3** stack—batch pipeline, tuning scripts, Streamlit UI, and export utilities—aligned with Biohub Zarr/GEFF conventions and documented competition presets in this repository.
Alternatives such as TrackMate excel at manual refinement inside Fiji but do not ship with this project's Zarr catalog browser, Streamlit deployment, or competition submission notebook builder.
Conversely, Cellpose offers stronger detection when retrained, but adds model weight management and GPU dependencies this package treats as optional (`LearnedDetector` scaffold only).
The Hungarian assignment formulation follows the classical linear assignment literature [@kuhn1955hungarian].

# Software design

The architecture separates **configuration**, **detection**, **tracking**, and **presentation**.

`Config` centralizes physical voxel spacing, detection thresholds, linking costs, and division gates, including a `competition_v4_preset()` that reproduces the repository's documented public leaderboard baseline (score 0.659 in `EXPERIMENTS.md`).
Detection downsamples XY via block averaging to approximate isotropic sampling, then finds local maxima with Otsu-style thresholds, optional dense-cluster recovery, intensity-weighted centroid refinement, and physical non-maximum suppression in micrometers.
Tracking builds a cost matrix combining Euclidean distance in physical space with optional motion, intensity, and neighborhood-signature terms, solves assignment with the Hungarian algorithm, and runs a second pass to attach unmatched daughters when sister-distance and midpoint gates indicate mitosis.
Post-processing can prune isolated nodes; gap closing and soft pruning remain opt-in because they regressed competition scores in internal A/B logs.

The Streamlit app (`app.py`, `app/ui.py`) loads local dataset catalogs or synthetic volumes, runs the same `run_tracking_pipeline` entry point as batch scripts, and renders matplotlib-based viewers.
Exports flatten nodes and edges into one CSV table and a JSON graph suitable for NetworkX or external visualization tools.

Design trade-offs favor **interpretability and modularity** over end-to-end learning: every stage exposes plain NumPy/Pandas structures, enabling unit tests on synthetic Gaussian blobs with known centroids (see `tests/` and `docs/REPRODUCIBLE_EXAMPLE.md`).

![Pipeline overview: detection, linking, and lineage export.](figures/pipeline_overview.png)

# Research impact statement

Documented use of this software to date is anchored in the repository itself rather than external publications citing a release:

- **Competition engineering:** The maintainer used the pipeline in the public Biohub Cell Tracking During Development challenge; `EXPERIMENTS.md` records versioned notebook submissions and a best public leaderboard score of **0.659** with the v4/v7 classical preset (verified only to the extent those logs and scores remain visible on the competition platform—authors should attach permalinks before JOSS submission).
- **Interactive dissemination:** A Streamlit Community Cloud deployment linked from `README.md` provides a no-install synthetic demo and upload path for custom NumPy volumes.
- **Reproducible materials:** Automated pytest coverage on synthetic ground truth, a reproducible example document, and GitHub Actions workflows to compile this paper and run tests on the `joss-preparation` branch.

The IEEE-style manuscript in `paper/main.tex` describes methods and UI behavior but is **not** itself peer-reviewed evidence of impact.
No independent laboratory adoption is claimed here; prospective JOSS reviewers should treat competition participation and the live demo as near-term significance signals pending third-party citations.

# AI usage disclosure

See `docs/JOSS_AI_DISCLOSURE.md` for a session-specific disclosure of generative-AI assistance preparing this JOSS branch, plus items requiring author confirmation about earlier development.

Human authors remain responsible for scientific claims, parameter choices, and verification of all commands and test results.

# Acknowledgements

The author thanks the Biohub Cell Tracking During Development organizers and community participants for dataset specifications and leaderboard feedback that shaped the competition presets documented in this repository.

No grant funding is declared in repository metadata; update this section if financial support applies.

# References

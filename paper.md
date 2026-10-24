---
title: 'Biohub Cell Lineage Tracker: An open pipeline and interactive system for 3D cell tracking during development'
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

Three-dimensional time-lapse fluorescence microscopy is widely used to study embryonic development, but reconstructing cell positions and lineage relationships from volumetric data remains difficult because of anisotropic sampling, crowding, motion, and division.
Biohub Cell Lineage Tracker is an open-source Python package and Streamlit application that detects cell centroids in each 3D frame, links them across time with a multi-cue linear assignment solver, and infers mitosis when one parent associates with two nearby daughters.
The same analysis core serves batch scripts and a browser UI for inspecting volumes, overlays, montages, lineage graphs, and CSV/JSON exports.
The implementation prioritizes interpretable classical image processing while exposing a detector interface for future learned segmenters.

# Statement of need

Live imaging produces sequences $I_t(z,y,x)$ whose manual lineage tracing is accurate but slow at scale.
Automated workflows must detect centroids in anisotropic volumes, associate them across time, and emit a directed graph $G=(V,E)$ with nodes $(t,z,y,x)$ and edges for continuations or divisions.

Biohub Cell Tracking During Development uses Zarr volumes and sparse GEFF labels; researchers need tunable parameters, slice-level review, and exports suitable for publications—not only a batch CSV writer.
TrackMate excels in Fiji/ImageJ but does not bundle this Zarr catalog workflow; Cellpose can improve detection when retraining is feasible, yet sparse-label benchmarks still rely on classical baselines.
Biohub Cell Lineage Tracker connects inspection, execution, and export in one documented Python stack.

# State of the field

TrackMate [@tinevez2017trackmate], lineaging pipelines [@amat2014lineage], and deep segmenters [@stringer2021cellpose; @cicek20163dunet] address parts of the problem; scikit-image peaks and Hungarian assignment underpin many classical trackers [@van2014scikit; @kuhn1955hungarian].
Streamlit enables rapid review UIs [@streamlit2019].
This repository **builds** an integrated Python 3 stack—`src/biohub/` modules, Streamlit front end, tuning scripts, and notebook builder—around one `Config` and `run_tracking_pipeline` entry point for Biohub Zarr/GEFF data.

# Software design

## Problem formulation and configuration

Volumes are stored as uint16 Zarr arrays with shape $(T,Z,Y,X)$ and anisotropic voxel spacing $s_z=1.625\,\mu\mathrm{m}$, $s_y=s_x=0.40625\,\mu\mathrm{m}$ (`SCALE` in `biohub.config`).
Optional training annotations live in GEFF graph directories with sparse centroid labels; a missing label does not imply absence of a cell.
All hyperparameters—detection thresholds, physical non-maximum suppression radii, linking weights, and division gates—live in a dataclass `Config`, which supports immutable overrides via `copy_with()` and documents a `competition_v4_preset()` aligned with the maintainer’s logged public leaderboard score of 0.659 on the Biohub challenge (`EXPERIMENTS.md`).
## Detection pipeline

Detection operates per frame in `detect_cells()` (`biohub.detection`).
Block mean pooling with `xy_ds=4` preserves $Z$ while downsampling $Y$ and $X$ to an approximately isotropic working grid.
The downsampled volume is preprocessed either with a Gaussian smoother (`smooth_sigma=1.0`) or, when opt-in flags select the `peaks_dog` backend, with a difference-of-Gaussians band-pass (`dog_bandpass`) whose sigmas are converted from micrometers to voxels on the downsampled grid.
The default Streamlit path and `competition_v4_preset()` use Gaussian smoothing; the DoG front-end is an experimental alternative (`competition_v10_dog_preset()`) kept separate because it changed only the detection stage in internal experiments.

Candidate peaks are obtained with scikit-image `peak_local_max` (or a maximum-filter fallback) on a thresholded map.
The absolute threshold is the maximum of Otsu’s method and a relative-rise rule $ \tau = b + \alpha (h-b) $, where $b$ is the median intensity, $h$ is a high percentile (`thresh_hi_percentile=99.8`), and $\alpha$ is `thresh_rel` (default 0.30, tunable on the competition path).
A secondary **dense-cluster pass** (`use_dense_cluster_pass=True`) repeats peak finding with a lower relative threshold and smaller minimum peak distance to recover nearby cells in crowded regions.
Peaks are mapped back to full resolution, refined by intensity-weighted centroids in local $(Z,YX)$ neighborhoods (`refine_centroid`), and filtered by relative contrast, optional axial floor rules, and border guards that retain only high-scoring border detections.
Physical non-maximum suppression (`physical_nms`) merges duplicates within `nms_radius_um` (default 2.65 µm), with an optional second pass at tighter radius after dense recovery.
Per-frame caps discard excess candidates when counts exceed adaptive or hard limits (`max_nodes_per_frame`).
Adaptive threshold retries (disabled in `competition_v4_preset()`) tighten $\alpha$ when frames exceed density caps.
Block pooling and physical NMS express distances in micrometers; dual-threshold peaks improve cluster recall without learned segmentation.

## Temporal linking

Consecutive frames are associated in `link_frames()` (`biohub.tracking`) by building a cost matrix on detections expressed in physical coordinates $\mathbf{p} = (z\,s_z, y\,s_y, x\,s_x)$.

When `use_rich_linking=True` (default), the assignment cost is
$$C_{ij} = d_{ij} + \lambda_m \rho^m_{ij} + \lambda_I f_{ij} + \lambda_N g_{ij},$$
where $d_{ij}$ is Euclidean distance, $\rho^m_{ij}$ is motion residual relative to the previous displacement of parent $i$, $f_{ij}$ is normalized intensity difference, and $g_{ij}$ compares $k$-nearest-neighbor offset signatures within `neighborhood_radius_um` (default 15 µm, $k=4$).
Default weights are $\lambda_m=0.20$, $\lambda_I=0.15$, $\lambda_N=0.10$.
Pairs with $d_{ij} > \texttt{max\_link\_dist\_um}$ (default 11 µm) receive a prohibitive cost before `scipy.optimize.linear_sum_assignment` selects one-to-one matches.

Velocities update along accepted edges; the pipeline streams one time point at a time for low memory use.
Optional gap closing ($t{-}2\!\to\!t$) and soft orphan pruning exist but are off in `competition_v4_preset()` after internal A/B logs linked them to leaderboard regression.

## Division inference

After primary assignment, unmatched detections in the current frame may become second daughters of a parent that already has exactly one matched child.
A candidate division must satisfy distance gates (`div_parent_dist_um`, `div_sister_dist_um`), and, when `div_use_midpoint_gate=True`, the parent at $t{-}1$ must lie near the midpoint between sisters in micrometers (`div_midpoint_dist_um`).
The implementation scores candidates by parent–daughter distance plus a weighted sister separation term; optional symmetry weighting (`div_symmetry_weight`) is zero in the competition preset.
Divisions appear in exports as nodes with two or more outgoing edges; `division_events()` summarizes parents with multiple daughters.

The rule set limits fan-out and favors symmetric mitoses; atypical geometries remain a limitation.

`run_tracking_pipeline()` (`biohub.analysis`) reads Zarr via Blosc2 or in-memory frame lists, builds Pandas node/edge tables, optionally prunes isolated nodes, and returns an `AnalysisResult` with division statistics.
Tuning scripts score sparse GEFF proxies when local train data exist.

## Architecture and interactive application

Libraries under `src/biohub/` cover I/O, detection, tracking, export, and Matplotlib visualization; `app.py`/`app/ui.py` implement Streamlit.
Seven pages (Home, Dataset, Volume, Pipeline, Detection, Lineage, Exports) load local `train/`/`test` Zarr/GEFF catalogs, synthetic demo data, or uploaded $(T,Z,Y,X)$ NumPy volumes.
Pipeline runs preview or full sequences; Detection shows overlays, link blends, montages, and GIF export via `build_overlay_gif()`; Lineage renders topology and track timelines with scale bars (`biohub.visualization`).
`scripts/generate_figures.py` and `paper/main.tex` mirror manuscript figures.

![Processing pipeline from 3D time-lapse volume to exported lineage graph.](figures/pipeline_overview.png)

## Exports and visualization outputs

`biohub.export` flattens lineage results into a single CSV in which each row is tagged `row_type=node` or `row_type=edge`, carrying node coordinates or `(source_id,target_id)` pairs.
JSON export encodes parallel `nodes` and `edges` arrays plus a `stats` object (volume shape serialized as a list for JSON compatibility).
Pytest suites on Gaussian-blob phantoms verify detection, linking, divisions, and export round-trips.

## Limitations and manuscript–code alignment

Classical peak detection can under-segment dense clusters and over-detect bright structures near tissue boundaries.
Frame-to-frame Hungarian linking recovers short motion but not long occlusions unless optional gap closing is enabled.
Division inference may miss oblique or overlapping mitoses.
`LearnedDetector` defines a hook for pretrained weights but falls back to classical peaks when no checkpoint is supplied; no bundled Cellpose or StarDist models ship with the repository.

The companion IEEE manuscript (`paper/main.tex`; author PDF) describes the default Gaussian peak path; code additionally exposes DoG detection, adaptive thresholds, gap closing, soft pruning, and division symmetry weighting (mostly off in `competition_v4_preset()`).
IEEE “Future work” items such as watershed splitting are not implemented.
Zebrafish-style qualitative figures require user-downloaded volumes; train/test Zarr are not redistributed here.
The logged leaderboard score **0.659** appears only in `EXPERIMENTS.md`—not verified by tests or embedded permalinks.

# Research impact statement

Use documented in-repo includes Biohub challenge participation (`EXPERIMENTS.md`, logged public score **0.659** with the v4/v7 preset), a public Streamlit demo (`README.md`), companion IEEE-format methods text (`paper/main.tex`), figure scripts, pytest on synthetic data, and CI that compiles this paper.
No third-party publications or independent lab adoptions are listed in repository metadata.

# AI usage disclosure

Generative AI assisted preparation of the JOSS materials on the `joss-preparation` branch.
A Cursor Cloud Agent (Composer) read JOSS requirements, inspected source modules, added pytest suites on synthetic ground truth, drafted and revised `paper.md`, configured CI to compile the PDF, and corrected JSON export of volume shapes after test failures.
The submitting author is responsible for verifying algorithmic descriptions against `src/biohub/` and the IEEE manuscript PDF used for this revision.
`docs/CLEANUP_REPORT.md` records agent-related branch cleanup and a 2026-07-07 history rewrite on `main`; whether other AI tools contributed to earlier commits, `paper/main.tex`, or UI text is not recorded in repository metadata.

# Acknowledgements

The author thanks the Biohub Cell Tracking During Development organizers and community participants for dataset specifications and leaderboard feedback that informed competition presets in this repository.
No grant funding is listed in repository metadata.

# References

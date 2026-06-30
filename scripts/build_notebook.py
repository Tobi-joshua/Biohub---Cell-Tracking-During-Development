#!/usr/bin/env python3
"""Generate the Kaggle submission notebook from src/biohub modules."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "biohub"
OUT = ROOT / "notebooks" / "biohub-cell-tracking-submission.ipynb"


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")],
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [line + "\n" for line in text.strip().split("\n")],
    }


def read_module(name: str) -> str:
    lines = (SRC / name).read_text().splitlines()
    cleaned: list[str] = []
    skip = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("from biohub.") or stripped.startswith("import biohub"):
            skip = stripped.endswith("(")
            continue
        if skip:
            if ")" in stripped:
                skip = False
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


cells: list[dict] = []

cells.append(
    md(
        """
# Biohub Cell Tracking — Classical 3D+Time Lineage Baseline

Detect cell centroids in 3D fluorescence volumes, link them across time, and reconstruct lineage graphs with division events. Output: `submission.csv`.

**Approach:** full-Z resolution, XY block-mean to an isotropic working grid, local-max detection with centroid refinement, Hungarian assignment in physical microns, conservative mitosis pass, isolated-node pruning.

**Dependencies:** numpy, scipy, pandas, scikit-image, blosc2, matplotlib (all available on Kaggle).
"""
    )
)

cells.append(
    md(
        """
## Competition Overview

| | |
|---|---|
| Input | `.zarr` image volumes `(T,Z,Y,X)`, chunked one frame at a time |
| Train labels | `.geff` sparse graphs: node centroids + directed edges |
| Voxel spacing | Z=1.625 µm, Y=X=0.40625 µm |
| Node match gate | 7 µm physical distance |
| Metric | Edge Jaccard + Division Jaccard (node over-prediction penalized) |
| Division | Parent node with ≥2 outgoing edges to daughters |

Sparse annotations: unlabeled cells still exist in the image. `estimated_number_of_nodes` in GEFF metadata helps calibrate detection density on the training split.
"""
    )
)

cells.append(
    code(
        """
from __future__ import annotations

import gc
import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import blosc2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter, maximum_filter
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
from skimage.feature import peak_local_max
from skimage.filters import threshold_otsu

plt.rcParams.update({'figure.dpi': 110, 'font.size': 9})
np.random.seed(42)
"""
    )
)

cells.append(md("## Configuration"))

cells.append(code(read_module("config.py")))

cells.append(md("## Data Loading"))

cells.append(code(read_module("data.py")))

cells.append(md("## Detection"))

cells.append(code(read_module("detection.py")))

cells.append(md("## Tracking and Division Handling"))

cells.append(code(read_module("tracking.py")))

cells.append(md("## Visualization"))

cells.append(code(read_module("visualization.py")))

cells.append(md("## Submission Pipeline"))

cells.append(code(read_module("submission.py")))

cells.append(md("## Path Resolution"))

cells.append(
    code(
        """
CFG = Config()
CFG.resolve_paths()
print('train:', CFG.train_dir)
print('test:', CFG.test_dir)
print('output:', CFG.output_path)
print('thresh_rel:', CFG.thresh_rel, '| max_link:', CFG.max_link_dist_um, 'µm')
"""
    )
)

cells.append(md("## EDA"))

cells.append(
    code(
        """
RUN_EDA = CFG.train_dir is not None and not CFG.submit_mode

if RUN_EDA:
    train_names = list_datasets(CFG.train_dir)
    print(f'{len(train_names)} training datasets')
    rows = []
    for name in train_names[:CFG.eda_sample_limit]:
        zpath = CFG.train_dir / f'{name}.zarr'
        shape, dtype = read_zarr_meta(zpath)
        est = read_estimated_nodes(CFG.train_dir / f'{name}.geff')
        rows.append({'name': name, 'T': shape[0], 'shape': shape, 'est_nodes': est})
    display(pd.DataFrame(rows))
else:
    print('EDA skipped (submit mode or no train data)')
"""
    )
)

cells.append(md("## Ground Truth Inspection"))

cells.append(
    code(
        """
if RUN_EDA and train_names:
    sample = train_names[0]
    gt_nodes, gt_edges = load_geff_graph(CFG.train_dir / f'{sample}.geff')
    zpath = CFG.train_dir / f'{sample}.zarr'
    shape, dtype = read_zarr_meta(zpath)
    vol = load_volume(zpath, 0, shape, dtype)
    pred, _ = detect_cells(vol, CFG)
    gt0 = gt_nodes[gt_nodes['t'] == 0][['z', 'y', 'x']].to_numpy() if gt_nodes is not None else np.empty((0, 3))
    fig = plot_gt_overlay(vol, gt0, pred, t=0, title=sample)
    plt.show()
    if gt_nodes is not None:
        out_deg = gt_edges.groupby('source_id').size()
        n_div = int((out_deg >= 2).sum())
        print(f'GT nodes={len(gt_nodes)}, edges={len(gt_edges)}, divisions={n_div}')
        print(f'Frame-0 recall proxy: {local_recall_proxy(gt_nodes, pred, 0):.3f}')
"""
    )
)

cells.append(md("## Detection Calibration (train)"))

cells.append(
    code(
        """
if RUN_EDA:
    best = calibrate_detection(CFG.train_dir, CFG, CFG.eda_sample_limit, CFG.calibration_frames)
    print(f'Calibrated THRESH_REL -> {best:.2f}')
else:
    print('Using default detection thresholds')
"""
    )
)

cells.append(md("## Visualization — sample frame"))

cells.append(
    code(
        """
viz_dir = CFG.test_dir or CFG.train_dir
if viz_dir is not None:
    names = list_datasets(viz_dir)
    if names:
        name = names[0]
        zpath = viz_dir / f'{name}.zarr'
        shape, dtype = read_zarr_meta(zpath)
        vol = load_volume(zpath, 0, shape, dtype)
        coords, _ = detect_cells(vol, CFG)
        fig = plot_volume_slices(vol, coords, title=f'{name} t=0')
        plt.show()
        counts = []
        for t in range(min(20, shape[0])):
            v = load_volume(zpath, t, shape, dtype)
            c, _ = detect_cells(v, CFG)
            counts.append(len(c))
        fig2 = plot_frame_counts(counts, title=f'{name} — first 20 frames')
        plt.show()
"""
    )
)

cells.append(md("## Inference"))

cells.append(
    code(
        """
# Calibrate on train when available, even in submit mode (fast, few frames).
if CFG.train_dir is not None:
    calibrate_detection(CFG.train_dir, CFG, sample_limit=3, frames_per_sample=3)
    print(f'Calibrated THRESH_REL = {CFG.thresh_rel:.2f}')

t0 = time.time()
submission, stats_df = build_submission(CFG)
display(stats_df)
print(f'Pipeline wall time: {(time.time()-t0)/60:.1f} min')
"""
    )
)

cells.append(md("## Submission Generation"))

cells.append(
    code(
        """
print(submission['row_type'].value_counts())
display(submission.head(8))
submission.to_csv(CFG.output_path)
print('Saved', CFG.output_path)
"""
    )
)

cells.append(md("## Validation"))

cells.append(
    code(
        """
validate_submission(submission, CFG.test_dir)
"""
    )
)

cells.append(
    md(
        """
## Runtime Notes

- Streams one timepoint at a time via blosc2 chunk decompression (~50 s for 4 test datasets on CPU).
- Full Z preserved; only XY averaged (÷4) for detection — keeps centroids inside the 7 µm match gate.
- `PRUNE_ISOLATED_NODES` removes single-frame detections with no edges (reduces node-count penalty).
- Division pass requires both daughters to have a plausible successor in `t+2` when `div_require_continued=True`.

## Limitations

- Classical peak picking under-segments dense clusters and over-segments bright noise.
- Frame-pair Hungarian linking cannot recover from long occlusions without gap closing.
- Sparse train labels make offline proxy scores optimistic.

## Future Work

- Pretrained 3D segmenters (Cellpose, StarDist) attached as Kaggle datasets.
- Marker-controlled watershed on distance transforms with anisotropic sampling.
- Global multi-frame assignment or lightweight motion priors.
- Gap closing across `t→t+2` for missed detections.

## Citations

- van der Walt et al. scikit-image, PeerJ 2014.
- Kuhn, The Hungarian Method, Naval Research Logistics 1955.
- Competition starter notebooks: nearest-neighbour baseline, strong-start guide, lineage tracker V2.
"""
    )
)

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"},
    },
    "cells": cells,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(nb, indent=1))
print(f"Wrote {OUT} ({len(cells)} cells)")

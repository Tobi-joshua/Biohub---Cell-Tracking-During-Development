#!/usr/bin/env python3
"""Generate the Kaggle submission notebook from src/biohub modules."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from biohub.config import PIPELINE_VERSION

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
        f"""
# Biohub Cell Tracking — Pipeline v{PIPELINE_VERSION}

3D+time cell detection, tracking, and lineage submission for the Biohub competition.

| Version | Focus |
|---------|-------|
| v1.1 | Dense-cluster peak pass, adaptive thresholds, intensity sampling |
| v1.2 | Rich linking: distance + motion + intensity + neighborhood |
| v1.3 | Improved division detection (midpoint gate, relaxed count gate) |
| v1.4 | Train hyperparameter search (`CFG.run_hyperparameter_search=True`) |
| v2.0 | Learned detector scaffold (`CFG.detector_backend='learned'`) |

Public baseline: **0.607**. This revision targets detection quality, link precision, and division recall.
"""
    )
)

cells.append(
    md(
        """
## Competition Overview

| | |
|---|---|
| Input | `.zarr` volumes `(T,Z,Y,X)`, one timepoint per chunk |
| Output | `submission.csv` with `node` + `edge` rows |
| Voxel spacing | Z=1.625 µm, Y=X=0.40625 µm |
| Match gate | 7 µm physical distance |
| Metric | Edge Jaccard + Division Jaccard |
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
from dataclasses import dataclass, field, replace
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

for title, module in [
    ("Configuration", "config.py"),
    ("Data Loading", "data.py"),
    ("Detection (v1.1)", "detection.py"),
    ("Tracking (v1.2 / v1.3)", "tracking.py"),
    ("Hyperparameter Search (v1.4)", "tuning.py"),
    ("Detector Backends (v2.0)", "detector.py"),
    ("Visualization", "visualization.py"),
    ("Submission Pipeline", "submission.py"),
]:
    cells.append(md(f"## {title}"))
    cells.append(code(read_module(module)))

cells.append(md("## Path Resolution"))

cells.append(
    code(
        """
CFG = Config()
CFG.resolve_paths()
# Fast submit: leave run_hyperparameter_search=False (~2 min)
# Offline tuning: CFG.run_hyperparameter_search = True  # adds ~5-10 min on train
print('pipeline:', PIPELINE_VERSION)
print('train:', CFG.train_dir)
print('test:', CFG.test_dir)
print('output:', CFG.output_path)
"""
    )
)

cells.append(md("## EDA"))

cells.append(
    code(
        """
RUN_EDA = CFG.train_dir is not None
train_names = list_datasets(CFG.train_dir) if RUN_EDA else []

if RUN_EDA:
    print(f'{len(train_names)} training datasets')
    rows = []
    for name in train_names[:CFG.eda_sample_limit]:
        zpath = CFG.train_dir / f'{name}.zarr'
        shape, dtype = read_zarr_meta(zpath)
        est = read_estimated_nodes(CFG.train_dir / f'{name}.geff')
        rows.append({'name': name, 'T': shape[0], 'shape': shape, 'est_nodes': est})
    display(pd.DataFrame(rows))
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
    pred, _, _ = detect_cells(vol, CFG)
    gt0 = gt_nodes[gt_nodes['t'] == 0][['z', 'y', 'x']].to_numpy() if gt_nodes is not None else np.empty((0, 3))
    fig = plot_gt_overlay(vol, gt0, pred, t=0, title=sample)
    plt.show()
    if gt_nodes is not None:
        n_div = int((gt_edges.groupby('source_id').size() >= 2).sum())
        print(f'GT nodes={len(gt_nodes)}, edges={len(gt_edges)}, divisions={n_div}')
        print(f'Frame-0 recall proxy: {local_recall_proxy(gt_nodes, pred, 0):.3f}')
"""
    )
)

cells.append(md("## Inference"))

cells.append(
    code(
        """
t0 = time.time()
submission, stats_df = build_submission(CFG)
display(stats_df)
print(f'Pipeline wall time: {(time.time()-t0)/60:.1f} min')
"""
    )
)

cells.append(md("## Submission + Validation"))

cells.append(
    code(
        """
print(submission['row_type'].value_counts())
display(submission.head(8))
submission.to_csv(CFG.output_path)
validate_submission(submission, CFG.test_dir)
print('Saved', CFG.output_path)
"""
    )
)

cells.append(
    md(
        """
## Runtime Notes

- Default submit: ~2 min CPU on the public 4-dataset test split.
- `run_hyperparameter_search=True` sweeps `thresh_rel`, `max_link_dist_um`, division gates on 3 train samples.
- Set `detector_backend='learned'` when Cellpose/StarDist weights are attached as a Kaggle dataset (v2.0).

## Citations

- van der Walt et al., scikit-image, PeerJ 2014
- Kuhn, The Hungarian Method, Naval Research Logistics 1955
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

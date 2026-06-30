#!/usr/bin/env python3
"""Generate a self-contained batch submission notebook from src/biohub modules."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "biohub"
OUT = ROOT / "notebooks" / "biohub-cell-tracking-submission.ipynb"

sys.path.insert(0, str(ROOT / "src"))
from biohub.config import PIPELINE_VERSION  # noqa: E402

MODULES = [
    ("Configuration", "config.py"),
    ("Data I/O", "data.py"),
    ("Detection", "detection.py"),
    ("Tracking", "tracking.py"),
    ("Detector", "detector.py"),
    ("Tuning", "tuning.py"),
    ("Batch export", "submission.py"),
]


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


def build_cells() -> list[dict]:
    cells: list[dict] = []

    cells.append(
        md(
            f"""
# Biohub Cell Tracking — Batch Submission (Pipeline v{PIPELINE_VERSION})

Self-contained notebook generated from `src/biohub/`.  
Regenerate locally: `python scripts/build_notebook.py`

**Steps**
1. Add the Biohub dataset to this notebook.
2. Run all cells.
3. Submit `submission.csv` from the output panel.

| Setting | Default |
|---------|---------|
| Output | `submission.csv` |
| Tuning | density calibration on train; optional grid search |
| Pipeline | v{PIPELINE_VERSION} gap closing + soft prune |
"""
        )
    )

    cells.append(
        code(
            """
import gc
import json
import time
import warnings
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter, maximum_filter
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

try:
    from skimage.feature import peak_local_max
    from skimage.filters import threshold_otsu
except ImportError:
    peak_local_max = None
    threshold_otsu = None

try:
    import blosc2
except ImportError:
    blosc2 = None

try:
    import zarr
except ImportError:
    zarr = None

warnings.filterwarnings("ignore")
print("Imports OK")
"""
        )
    )

    for title, fname in MODULES:
        cells.append(md(f"## {title}"))
        cells.append(code(read_module(fname)))

    cells.append(
        md(
            """
## Run pipeline

Set `run_hyperparameter_search=True` only if you have spare runtime (train grid search).
"""
        )
    )

    cells.append(
        code(
            f"""
CFG = Config()
CFG.resolve_paths()

# --- Tweak submission settings here ---
CFG = CFG.copy_with(
    thresh_rel=0.30,
    max_link_dist_um=11.0,
    div_parent_dist_um=12.0,
    div_sister_dist_um=7.5,
    gap_close_enabled=True,
    gap_close_dist_um=15.0,
    prune_soft_neighbors=True,
    run_hyperparameter_search=False,
    hyperparam_sample_limit=3,
    hyperparam_frames=4,
)

print(f"Pipeline v{{PIPELINE_VERSION}}")
print(f"train: {{CFG.train_dir}}")
print(f"test:  {{CFG.test_dir}}")
print(f"out:   {{CFG.output_path}}")
"""
        )
    )

    cells.append(
        code(
            """
submission, stats_df = build_submission(CFG)
print(submission["row_type"].value_counts())
display(submission.head(8))
display(stats_df)
submission.to_csv(CFG.output_path)
if CFG.test_dir is not None:
    validate_submission(submission, CFG.test_dir)
print(f"Wrote {CFG.output_path} ({len(submission):,} rows)")
"""
        )
    )

    return cells


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "cells": build_cells(),
    }
    OUT.write_text(json.dumps(notebook, indent=1))
    print(f"Wrote {OUT} ({len(notebook['cells'])} cells)")


if __name__ == "__main__":
    main()

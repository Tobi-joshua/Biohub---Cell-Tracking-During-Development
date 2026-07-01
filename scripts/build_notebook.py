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

**Version 7** validated **0.659** (v4 competition baseline).  
**Version 8+** — run optional train hyperparameter search, then change **one** knob.

v1.5 experiments stay disabled — see `EXPERIMENTS.md`.

**Steps**
1. Add the Biohub dataset to this notebook.
2. Run all cells (search → optional V8 override → submit).
3. Submit `submission.csv` from the output panel.

| Setting | Default |
|---------|---------|
| Output | `submission.csv` |
| Preset | v4 competition baseline (v1.5 features off) |
| Tuning | Optional train grid search + density calibration |
| V8 rule | Change **one** parameter per submission |
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
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

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
## 1. Configuration (v4 preset)

Baseline validated at **0.659** (V7). Starts from `competition_v4_preset()`.
"""
        )
    )

    cells.append(
        code(
            f"""
CFG = Config()
CFG.resolve_paths()

# v4 competition baseline (0.659) — v1.5 features OFF
CFG = CFG.competition_v4_preset()

print(f"Pipeline v{{PIPELINE_VERSION}}")
print(f"train: {{CFG.train_dir}}")
print(f"test:  {{CFG.test_dir}}")
print(f"out:   {{CFG.output_path}}")
"""
        )
    )

    cells.append(
        md(
            """
## 2. Candidate sweep (recommended for V8+)

Ranks safe one-knob candidates on train labels and writes `single_knob_sweep.csv`.  
This is faster and safer than manual trial-and-error or changing multiple knobs at once.
"""
        )
    )

    cells.append(
        code(
            """
RUN_SINGLE_KNOB_SWEEP = True
AUTO_APPLY_SWEEP_WINNER = True

if RUN_SINGLE_KNOB_SWEEP and CFG.train_dir is not None:
    CFG, sweep_table = single_knob_sweep(
        CFG.train_dir,
        CFG,
        sample_limit=5,
        frames=6,
    )
    sweep_path = Path("/kaggle/working/single_knob_sweep.csv") if Path("/kaggle/working").is_dir() else Path("single_knob_sweep.csv")
    sweep_table.to_csv(sweep_path, index=False)
    display(sweep_table.head(12))
    print(
        "Best proxy candidate:",
        f"thresh_rel={CFG.thresh_rel:.3f}",
        f"max_link_dist_um={CFG.max_link_dist_um:.1f}",
        f"nms={CFG.nms_radius_um:.2f}",
        f"div_parent={CFG.div_parent_dist_um:.1f}",
        f"div_sister={CFG.div_sister_dist_um:.1f}",
        f"density_calibration={CFG.run_density_calibration}",
    )
    print(f"Wrote {sweep_path}")
    if not AUTO_APPLY_SWEEP_WINNER:
        CFG = Config().competition_v4_preset()
        CFG.resolve_paths()
        print("AUTO_APPLY_SWEEP_WINNER=False — reset to V7 baseline")
elif CFG.train_dir is None:
    print("No train directory — skipping candidate sweep")
else:
    print("Skipping candidate sweep (RUN_SINGLE_KNOB_SWEEP=False)")
"""
        )
    )

    cells.append(
        md(
            """
## 3. Manual V8 override (optional)

Use this only if you want to override the sweep winner.  
**Rule:** keep at most **one** key in `V8_OVERRIDES`. Threshold overrides automatically disable density calibration so they are not overwritten.

| Knob | Typical effect |
|------|----------------|
| `max_link_dist_um` | Edge recall vs false links |
| `thresh_rel` | Node count / precision |
| `nms_radius_um` | Duplicate peak suppression |
| `div_parent_dist_um` / `div_sister_dist_um` | Division metric |
"""
        )
    )

    cells.append(
        code(
            """
# === Optional manual V8 override: keep at most ONE key ===
V8_OVERRIDES = {
    # "max_link_dist_um": 10.0,
    # "max_link_dist_um": 10.5,
    # "thresh_rel": 0.28,
    # "thresh_rel": 0.32,
    # "nms_radius_um": 2.5,
    # "div_parent_dist_um": 11.0,
    # "div_sister_dist_um": 7.0,
    # "div_sister_dist_um": 8.0,
}

if V8_OVERRIDES:
    if len(V8_OVERRIDES) != 1:
        raise ValueError(f"Use exactly one V8 override, got {len(V8_OVERRIDES)}: {V8_OVERRIDES}")
    CFG = CFG.copy_with(**V8_OVERRIDES)
    if "thresh_rel" in V8_OVERRIDES:
        CFG = CFG.copy_with(run_density_calibration=False)
        print("Disabled density calibration so explicit thresh_rel is preserved")
    print("V8 overrides applied:", V8_OVERRIDES)
else:
    print("No manual overrides — using sweep winner if enabled, otherwise V7 baseline")
"""
        )
    )

    cells.append(
        md(
            """
## 4. Build submission

Runs density calibration when enabled, then processes all test volumes.
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

"""Competition configuration and physical scale constants."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

import numpy as np


# Physical voxel spacing (Z, Y, X) in micrometers.
SCALE: Tuple[float, float, float] = (1.625, 0.40625, 0.40625)
MATCH_GATE_UM: float = 7.0


@dataclass
class Config:
    """Pipeline hyperparameters. Tuned for metric geometry and CPU runtime."""

    # Paths (resolved at runtime on Kaggle or locally).
    data_root: Path | None = None
    train_dir: Path | None = None
    test_dir: Path | None = None
    output_path: Path = field(default_factory=lambda: Path("submission.csv"))

    # Detection on an approximately isotropic working grid (full Z, XY block-mean).
    xy_ds: int = 4
    smooth_sigma: float = 1.0
    min_peak_dist: int = 3
    thresh_rel: float = 0.30
    thresh_hi_percentile: float = 99.8
    min_rel_contrast: float = 0.08

    # Centroid refinement and duplicate suppression.
    refine_radius_z: int = 2
    refine_radius_yx: int = 5
    nms_radius_um: float = 2.65
    border_z: int = 3
    border_yx: int = 2
    border_keep_quantile: float = 0.80

    # Frame-level count stabilizer (guards against threshold glitches).
    max_frame_count_mult: float = 1.70
    max_frame_count_add: int = 45
    max_nodes_per_frame: int = 20_000

    # Linking (physical distance, microns).
    max_link_dist_um: float = 11.0

    # Division detection.
    detect_divisions: bool = True
    div_parent_dist_um: float = 12.0
    div_sister_dist_um: float = 7.0
    div_min_count_gain: int = 1
    div_require_continued: bool = False

    # Post-processing.
    prune_isolated_nodes: bool = True

    # Runtime / EDA switches.
    submit_mode: bool = True
    eda_sample_limit: int = 4
    calibration_frames: int = 5
    random_state: int = 42

    @property
    def scale_array(self) -> np.ndarray:
        return np.array(SCALE, dtype=np.float64)

    def resolve_paths(self) -> None:
        """Locate competition data directories."""
        candidates = [
            Path("/kaggle/input/competitions/biohub-cell-tracking-during-development"),
            Path("/kaggle/input/biohub-cell-tracking-during-development"),
        ]
        if self.data_root is None:
            self.data_root = next((p for p in candidates if p.is_dir()), None)
        if self.data_root is not None:
            if self.train_dir is None:
                train = self.data_root / "train"
                self.train_dir = train if train.is_dir() else None
            if self.test_dir is None:
                test = self.data_root / "test"
                self.test_dir = test if test.is_dir() else None

        if Path("/kaggle/working").exists():
            self.output_path = Path("/kaggle/working/submission.csv")

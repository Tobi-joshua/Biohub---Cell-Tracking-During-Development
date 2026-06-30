"""Pipeline configuration and physical scale constants."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Tuple

import numpy as np

# Physical voxel spacing (Z, Y, X) in micrometers.
SCALE: Tuple[float, float, float] = (1.625, 0.40625, 0.40625)
MATCH_GATE_UM: float = 7.0
PIPELINE_VERSION: str = "1.5"


@dataclass
class Config:
    """Pipeline hyperparameters for detection, tracking, and lineage reconstruction."""

    data_root: Path | None = None
    train_dir: Path | None = None
    test_dir: Path | None = None
    output_dir: Path = field(default_factory=lambda: Path("outputs"))
    output_path: Path = field(default_factory=lambda: Path("outputs/lineage_graph.csv"))

    detector_backend: str = "peaks"

    # Detection
    xy_ds: int = 4
    smooth_sigma: float = 1.0
    min_peak_dist: int = 3
    thresh_rel: float = 0.30
    thresh_hi_percentile: float = 99.8
    min_rel_contrast: float = 0.08
    use_dense_cluster_pass: bool = True
    dense_min_peak_dist: int = 2
    dense_thresh_rel_delta: float = -0.04
    use_adaptive_frame_threshold: bool = True
    adaptive_overcount_penalty: float = 0.04
    min_z_hard: int = 4

    refine_radius_z: int = 2
    refine_radius_yx: int = 5
    nms_radius_um: float = 2.65
    nms_dense_radius_um: float = 2.0
    border_z: int = 3
    border_yx: int = 2
    border_keep_quantile: float = 0.80

    max_frame_count_mult: float = 1.70
    max_frame_count_add: int = 45
    max_nodes_per_frame: int = 20_000

    # Linking
    max_link_dist_um: float = 11.0
    use_rich_linking: bool = True
    motion_lambda: float = 0.20
    intensity_lambda: float = 0.15
    neighborhood_lambda: float = 0.10
    neighborhood_k: int = 4
    neighborhood_radius_um: float = 15.0

    # Divisions
    detect_divisions: bool = True
    div_parent_dist_um: float = 12.0
    div_sister_dist_um: float = 7.5
    div_min_count_gain: int = 0
    div_require_continued: bool = False
    div_use_midpoint_gate: bool = True
    div_midpoint_dist_um: float = 9.0

    prune_isolated_nodes: bool = True
    prune_soft_neighbors: bool = True
    prune_neighbor_dist_um: float = 9.0

    # Gap closing (link across one missed frame)
    gap_close_enabled: bool = True
    gap_close_dist_um: float = 15.0

    # Division scoring
    div_symmetry_weight: float = 0.35

    # Tuning
    run_hyperparameter_search: bool = False
    hyperparam_sample_limit: int = 3
    hyperparam_frames: int = 4
    hyperparam_results_path: Path = field(default_factory=lambda: Path("results/hyperparameter_search.csv"))

    preview_max_frames: int = 20
    eda_sample_limit: int = 4
    calibration_frames: int = 5
    random_state: int = 42

    @property
    def scale_array(self) -> np.ndarray:
        return np.array(SCALE, dtype=np.float64)

    def resolve_paths(self, project_root: Path | None = None) -> None:
        """Resolve default data directories relative to the project root."""
        root = project_root or Path.cwd()

        # Hosted notebook runtime (e.g. Kaggle): discover competition input paths.
        kaggle_candidates = [
            Path("/kaggle/input/competitions/biohub-cell-tracking-during-development"),
            Path("/kaggle/input/biohub-cell-tracking-during-development"),
        ]
        for comp_root in kaggle_candidates:
            if (comp_root / "test").is_dir():
                self.data_root = comp_root
                self.test_dir = comp_root / "test"
                self.train_dir = comp_root / "train" if (comp_root / "train").is_dir() else None
                if Path("/kaggle/working").is_dir():
                    self.output_path = Path("/kaggle/working/submission.csv")
                self.output_dir.mkdir(parents=True, exist_ok=True)
                return

        candidates = [
            root / "data",
            root / "data" / "train",
            root.parent / "data",
        ]
        if self.data_root is None:
            self.data_root = next((p for p in candidates if p.is_dir()), None)
        if self.data_root is not None:
            if self.train_dir is None:
                train = self.data_root / "train" if (self.data_root / "train").is_dir() else self.data_root
                self.train_dir = train if train.is_dir() else None
            if self.test_dir is None:
                test = self.data_root / "test"
                self.test_dir = test if test.is_dir() else None
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.output_path.parent == Path("."):
            self.output_path = self.output_dir / self.output_path.name

    def copy_with(self, **kwargs) -> "Config":
        return replace(self, **kwargs)

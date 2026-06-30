"""Detector backends (v2.0 scaffold)."""

from __future__ import annotations

from typing import Optional, Protocol, Tuple

import numpy as np

from biohub.config import Config


class CellDetector(Protocol):
    """Interface for swappable detection backends."""

    def detect(
        self,
        vol: np.ndarray,
        cfg: Config,
        prev_count: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return coords (N,3), scores (N,), intensities (N,)."""
        ...


class PeakDetector:
    """Classical anisotropy-aware peak detector (default, v1.x)."""

    def detect(
        self,
        vol: np.ndarray,
        cfg: Config,
        prev_count: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return detect_cells(vol, cfg, prev_count=prev_count)


class LearnedDetector:
    """
    Placeholder for v2.0 learned backends (Cellpose, StarDist, 3D U-Net).

    Attach pretrained weights as a Kaggle dataset and implement `predict`
    to return centroid coordinates in (z, y, x) voxel space.
    """

    def __init__(self, weights_path: str | None = None) -> None:
        self.weights_path = weights_path

    def detect(
        self,
        vol: np.ndarray,
        cfg: Config,
        prev_count: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.weights_path is None:
            return detect_cells(vol, cfg, prev_count=prev_count)
        raise NotImplementedError(
            "LearnedDetector is a scaffold. Subclass and load Cellpose/StarDist weights "
            "from a Kaggle dataset, then map instance centroids to (z,y,x)."
        )


def get_detector(cfg: Config) -> CellDetector:
    if cfg.detector_backend == "learned":
        return LearnedDetector()
    return PeakDetector()

"""Detector backends."""

from __future__ import annotations

from typing import Optional, Protocol, Tuple

import numpy as np

from biohub.config import Config
from biohub.detection import detect_cells


class CellDetector(Protocol):
    def detect(
        self,
        vol: np.ndarray,
        cfg: Config,
        prev_count: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        ...


class PeakDetector:
    """Classical anisotropy-aware peak detector (Gaussian or DoG band-pass)."""

    def detect(
        self,
        vol: np.ndarray,
        cfg: Config,
        prev_count: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return detect_cells(vol, cfg, prev_count=prev_count)


class DogPeakDetector(PeakDetector):
    """Peak detector with DoG band-pass preprocessing enabled."""

    def detect(
        self,
        vol: np.ndarray,
        cfg: Config,
        prev_count: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        cfg = cfg.copy_with(use_dog_bandpass=True, detector_backend="peaks_dog")
        return detect_cells(vol, cfg, prev_count=prev_count)


class LearnedDetector:
    """
    Scaffold for learned backends (Cellpose, StarDist, 3D U-Net).

    Provide a `weights_path` to a local checkpoint and override `predict`.
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
            "Load pretrained weights and map instance centroids to (z, y, x)."
        )


def get_detector(cfg: Config) -> CellDetector:
    if cfg.detector_backend == "learned":
        return LearnedDetector()
    if cfg.detector_backend == "peaks_dog" or cfg.use_dog_bandpass:
        return DogPeakDetector()
    return PeakDetector()

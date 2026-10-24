"""Deterministic synthetic volumes with known cell centroids (voxel coordinates)."""

from __future__ import annotations

from typing import Iterable, Sequence, Tuple

import numpy as np

from biohub.config import Config

CentroidZYX = Tuple[int, int, int]


def gaussian_blob_frame(
    shape_zyx: Tuple[int, int, int],
    centers_zyx: Sequence[CentroidZYX],
    amplitude: float = 2500.0,
    sigma_zyx: Tuple[float, float, float] = (2.0, 1.5, 1.5),
) -> np.ndarray:
    """Build one uint16 frame with bright Gaussian blobs at ``centers_zyx``."""
    z, y, x = shape_zyx
    vol = np.zeros((z, y, x), dtype=np.uint16)
    zz, yy, xx = np.ogrid[:z, :y, :x]
    for cz, cy, cx in centers_zyx:
        blob = np.exp(
            -(
                (zz - cz) ** 2 / sigma_zyx[0] ** 2
                + (yy - cy) ** 2 / sigma_zyx[1] ** 2
                + (xx - cx) ** 2 / sigma_zyx[2] ** 2
            )
        )
        vol += np.clip(amplitude * blob, 0, np.iinfo(np.uint16).max).astype(np.uint16)
    return vol


def drifting_centers(
    base: Sequence[CentroidZYX],
    frame: int,
    delta_y: int = 2,
    delta_x: int = 1,
) -> list[CentroidZYX]:
    """Translate each centroid linearly across time (ground-truth motion model)."""
    return [(z, y + frame * delta_y, x + frame * delta_x) for z, y, x in base]


def synthetic_test_config() -> Config:
    """
    Stable detection settings for unit tests (no adaptive/dense passes).

    Uses the competition v4 linking/division preset with test-friendly detection thresholds.
    """
    return Config().competition_v4_preset().copy_with(
        use_adaptive_frame_threshold=False,
        use_dense_cluster_pass=False,
        thresh_rel=0.15,
        use_competition_preset=False,
    )


def match_centroids(
    detected: np.ndarray,
    ground_truth: Sequence[CentroidZYX],
    max_distance_vox: float = 2.5,
) -> dict[CentroidZYX, np.ndarray]:
    """
    Greedy one-to-one matching from ground truth to detections within a voxel radius.

    Raises ``AssertionError`` when a ground-truth cell has no matching detection.
    """
    if detected.size == 0:
        raise AssertionError("No detections to match against ground truth.")
    gt_arr = np.asarray(ground_truth, dtype=np.float64)
    used = set()
    mapping: dict[CentroidZYX, np.ndarray] = {}
    for i, gt in enumerate(gt_arr):
        dists = np.linalg.norm(detected.astype(np.float64) - gt, axis=1)
        order = np.argsort(dists)
        matched = False
        for j in order:
            if j in used:
                continue
            if dists[j] <= max_distance_vox:
                used.add(int(j))
                key = tuple(int(v) for v in ground_truth[i])
                mapping[key] = detected[j]
                matched = True
                break
        if not matched:
            raise AssertionError(f"Ground-truth cell {ground_truth[i]} has no detection within {max_distance_vox} vox.")
    return mapping


def division_scenario_frames(
    shape_zyx: Tuple[int, int, int] = (24, 64, 64),
    parent_center: CentroidZYX = (10, 30, 32),
    daughter_separation_vox: int = 16,
) -> tuple[list[np.ndarray], CentroidZYX, tuple[CentroidZYX, CentroidZYX]]:
    """
    Three-frame mitosis-like sequence: one cell, one cell, two separated daughters.

    ``daughter_separation_vox`` must be large enough for peak NMS to keep two detections.
    """
    z, y, cx = parent_center
    f0 = gaussian_blob_frame(shape_zyx, [parent_center])
    f1 = gaussian_blob_frame(shape_zyx, [(z, y + 2, cx)])
    half = daughter_separation_vox // 2
    d0: CentroidZYX = (z, y + 4, cx - half)
    d1: CentroidZYX = (z, y + 4, cx + half)
    f2 = gaussian_blob_frame(shape_zyx, [d0, d1])
    return [f0, f1, f2], parent_center, (d0, d1)

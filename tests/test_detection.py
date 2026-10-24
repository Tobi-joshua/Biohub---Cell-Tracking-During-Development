"""Tests for anisotropy-aware peak detection on synthetic ground truth."""

from __future__ import annotations

import numpy as np

from biohub.detection import detect_cells
from tests.fixtures.synthetic_ground_truth import (
    gaussian_blob_frame,
    match_centroids,
    synthetic_test_config,
)


def test_detect_cells_recovers_known_centroids():
    cfg = synthetic_test_config()
    ground_truth = [(8, 24, 24), (8, 24, 40), (12, 40, 24)]
    vol = gaussian_blob_frame((24, 64, 64), ground_truth)

    coords, scores, intensities = detect_cells(vol, cfg)

    assert len(coords) == len(ground_truth)
    match_centroids(coords, ground_truth, max_distance_vox=1.0)
    assert scores.shape == (len(ground_truth),)
    assert intensities.shape == (len(ground_truth),)
    assert np.all(intensities > 0)


def test_detect_cells_empty_volume_returns_no_nodes():
    cfg = synthetic_test_config()
    vol = np.zeros((16, 32, 32), dtype=np.uint16)
    coords, scores, intensities = detect_cells(vol, cfg)
    assert len(coords) == 0
    assert len(scores) == 0
    assert len(intensities) == 0

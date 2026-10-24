"""Tests for multi-frame linking on synthetic trajectories."""

from __future__ import annotations

import numpy as np

from biohub.analysis import run_tracking_pipeline
from tests.fixtures.synthetic_ground_truth import (
    drifting_centers,
    gaussian_blob_frame,
    synthetic_test_config,
)


def test_pipeline_links_drifting_cells_across_frames():
    cfg = synthetic_test_config()
    base = [(8, 24, 24), (8, 24, 40), (12, 40, 24)]
    frames = [
        gaussian_blob_frame((24, 64, 64), drifting_centers(base, t))
        for t in range(3)
    ]

    result = run_tracking_pipeline(frames, cfg, dataset_name="tracking-test", max_frames=3)

    assert result.n_nodes == 9
    assert result.n_edges == 6
    assert result.n_divisions == 0
    per_frame = result.nodes.groupby("t").size().tolist()
    assert per_frame == [3, 3, 3]

    # Each detection after t=0 has exactly one parent edge (simple motion, no divisions).
    for t in (1, 2):
        ids_t = set(result.nodes.loc[result.nodes["t"] == t, "node_id"])
        incoming = result.edges[result.edges["target_id"].isin(ids_t)]
        assert len(incoming) == len(ids_t)
        assert incoming["source_id"].nunique() == len(ids_t)

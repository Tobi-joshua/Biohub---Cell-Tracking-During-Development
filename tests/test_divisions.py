"""Tests for mitosis inference (Hungarian linking + division pass)."""

from __future__ import annotations

import numpy as np

from biohub.analysis import run_tracking_pipeline
from biohub.export import division_events
from biohub.tracking import link_frames
from tests.fixtures.synthetic_ground_truth import division_scenario_frames, synthetic_test_config


def test_link_frames_infers_one_to_two_division_on_synthetic_coords():
    cfg = synthetic_test_config()
    prev_ids = [1]
    prev_xyz = np.array([[10.0, 30.0, 32.0]])
    curr_ids = [2, 3]
    curr_xyz = np.array([[10.0, 34.0, 24.0], [10.0, 34.0, 40.0]])

    edges = link_frames(prev_ids, prev_xyz, curr_ids, curr_xyz, cfg)

    assert sorted(edges) == [(1, 2), (1, 3)]


def test_pipeline_detects_division_in_three_frame_synthetic_mitosis():
    cfg = synthetic_test_config()
    frames, _parent, _daughters = division_scenario_frames(daughter_separation_vox=16)

    result = run_tracking_pipeline(frames, cfg, dataset_name="division-test", max_frames=3)

    assert result.nodes.groupby("t").size().tolist() == [1, 1, 2]
    assert result.n_divisions == 1
    divs = division_events(result)
    assert len(divs) == 1
    assert int(divs.iloc[0]["n_daughters"]) == 2

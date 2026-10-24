"""Tests for CSV and JSON lineage export."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from biohub.analysis import run_tracking_pipeline
from biohub.export import save_graph_json, save_lineage_csv, to_graph_json, to_lineage_csv
from tests.fixtures.synthetic_ground_truth import (
    drifting_centers,
    gaussian_blob_frame,
    synthetic_test_config,
)


def _small_result():
    cfg = synthetic_test_config()
    base = [(8, 24, 24), (8, 24, 40)]
    frames = [gaussian_blob_frame((24, 64, 64), drifting_centers(base, t)) for t in range(2)]
    return run_tracking_pipeline(frames, cfg, dataset_name="export-test", max_frames=2)


def test_lineage_csv_contains_nodes_and_edges(tmp_path: Path):
    result = _small_result()
    df = to_lineage_csv(result)

    assert set(df["row_type"].unique()) == {"node", "edge"}
    assert len(df[df["row_type"] == "node"]) == result.n_nodes
    assert len(df[df["row_type"] == "edge"]) == result.n_edges

    out = tmp_path / "lineage.csv"
    save_lineage_csv(result, out)
    loaded = pd.read_csv(out, index_col=0)
    pd.testing.assert_frame_equal(df, loaded)


def test_graph_json_roundtrip_structure(tmp_path: Path):
    result = _small_result()
    payload = to_graph_json(result)

    assert payload["dataset"] == "export-test"
    assert len(payload["nodes"]) == result.n_nodes
    assert len(payload["edges"]) == result.n_edges
    assert payload["stats"]["nodes"] == result.n_nodes

    for node in payload["nodes"]:
        assert set(node.keys()) == {"id", "t", "z", "y", "x"}
    for edge in payload["edges"]:
        assert set(edge.keys()) == {"source", "target"}

    out = tmp_path / "graph.json"
    save_graph_json(result, out)
    reloaded = json.loads(out.read_text())
    assert reloaded == payload

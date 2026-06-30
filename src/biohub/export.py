"""Export lineage graphs to CSV and network formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd

from biohub.analysis import AnalysisResult


def to_lineage_csv(result: AnalysisResult) -> pd.DataFrame:
    """Merge node and edge rows into a single export table."""
    node_cols = ["dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
    if result.nodes.empty and result.edges.empty:
        return pd.DataFrame(columns=node_cols)
    parts = []
    if not result.nodes.empty:
        n = result.nodes.copy()
        n["row_type"] = "node"
        parts.append(n[node_cols])
    if not result.edges.empty:
        e = result.edges.copy()
        e["row_type"] = "edge"
        parts.append(e[node_cols])
    out = pd.concat(parts, ignore_index=True)
    out.index.name = "id"
    return out


def save_lineage_csv(result: AnalysisResult, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    to_lineage_csv(result).to_csv(path)
    return path


def to_graph_json(result: AnalysisResult) -> dict:
    """Export nodes and edges for graph visualization libraries."""
    nodes = []
    if not result.nodes.empty:
        for row in result.nodes.itertuples(index=False):
            nodes.append(
                {
                    "id": int(row.node_id),
                    "t": int(row.t),
                    "z": int(row.z),
                    "y": int(row.y),
                    "x": int(row.x),
                }
            )
    edges = []
    if not result.edges.empty:
        for row in result.edges.itertuples(index=False):
            edges.append({"source": int(row.source_id), "target": int(row.target_id)})
    return {
        "dataset": result.dataset_name,
        "nodes": nodes,
        "edges": edges,
        "stats": result.stats,
    }


def save_graph_json(result: AnalysisResult, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_graph_json(result), indent=2))
    return path


def division_events(result: AnalysisResult) -> pd.DataFrame:
    """List parent nodes with two or more outgoing edges."""
    if result.edges.empty:
        return pd.DataFrame(columns=["source_id", "n_daughters", "target_ids"])
    counts = result.edges.groupby("source_id")["target_id"].apply(list).reset_index()
    counts.columns = ["source_id", "target_ids"]
    counts["n_daughters"] = counts["target_ids"].apply(len)
    return counts[counts["n_daughters"] >= 2].reset_index(drop=True)

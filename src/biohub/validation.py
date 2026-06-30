"""Local validation utilities and diagnostic metrics (v1.5)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from biohub.analysis import AnalysisResult, run_tracking_pipeline
from biohub.config import MATCH_GATE_UM, Config
from biohub.data import list_datasets, load_geff_graph, read_zarr_meta
from biohub.export import division_events
from biohub.tuning import score_config_on_sample


def link_distance_stats(edges: pd.DataFrame, nodes: pd.DataFrame, scale: np.ndarray) -> Dict[str, float]:
    """Physical link lengths for edges with resolvable node coordinates."""
    if edges.empty or nodes.empty:
        return {"mean_um": np.nan, "median_um": np.nan, "p95_um": np.nan}
    pos = nodes.set_index("node_id")[["z", "y", "x"]].astype(float)
    dists = []
    for row in edges.itertuples(index=False):
        s, t = int(row.source_id), int(row.target_id)
        if s not in pos.index or t not in pos.index:
            continue
        a = pos.loc[s].to_numpy() * scale
        b = pos.loc[t].to_numpy() * scale
        dists.append(float(np.linalg.norm(a - b)))
    if not dists:
        return {"mean_um": np.nan, "median_um": np.nan, "p95_um": np.nan}
    arr = np.array(dists)
    return {
        "mean_um": float(arr.mean()),
        "median_um": float(np.median(arr)),
        "p95_um": float(np.percentile(arr, 95)),
    }


def track_length_distribution(edges: pd.DataFrame) -> pd.Series:
    """Outgoing edge count per source node (proxy for tracklet length)."""
    if edges.empty:
        return pd.Series(dtype=int)
    return edges.groupby("source_id").size()


def summarize_result(result: AnalysisResult, cfg: Config) -> Dict[str, object]:
    """Aggregate diagnostics for one pipeline run."""
    counts = [len(f.coords) for f in result.frames]
    link_stats = link_distance_stats(result.edges, result.nodes, cfg.scale_array)
    lengths = track_length_distribution(result.edges)
    divs = division_events(result)
    return {
        "dataset": result.dataset_name,
        "nodes": result.n_nodes,
        "edges": result.n_edges,
        "divisions": result.n_divisions,
        "removed_isolated": result.stats.get("removed_isolated", 0),
        "detections_min": int(min(counts)) if counts else 0,
        "detections_max": int(max(counts)) if counts else 0,
        "detections_mean": float(np.mean(counts)) if counts else 0.0,
        "link_mean_um": link_stats["mean_um"],
        "link_median_um": link_stats["median_um"],
        "link_p95_um": link_stats["p95_um"],
        "track_len_mean": float(lengths.mean()) if len(lengths) else 0.0,
        "track_len_max": int(lengths.max()) if len(lengths) else 0,
        "division_events": len(divs),
    }


def evaluate_train_proxy(
    train_dir: Path,
    cfg: Config,
    sample_limit: int = 3,
    frames: int = 4,
) -> pd.DataFrame:
    """Per-sample proxy scores using sparse GEFF labels."""
    rows = []
    for name in list_datasets(train_dir)[:sample_limit]:
        t0 = time.time()
        scores = score_config_on_sample(train_dir, name, cfg, frames)
        rows.append(
            {
                "sample": name,
                "runtime_s": round(time.time() - t0, 2),
                **scores,
            }
        )
    return pd.DataFrame(rows)


def run_validation_report(
    train_dir: Path,
    cfg: Optional[Config] = None,
    output_dir: Path = Path("results"),
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run proxy evaluation and write CSV summaries to ``output_dir``.

    Returns (per-sample proxy table, aggregate summary as one-row DataFrame).
    """
    cfg = cfg or Config()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    proxy = evaluate_train_proxy(train_dir, cfg, cfg.hyperparam_sample_limit, cfg.hyperparam_frames)
    proxy_path = output_dir / "validation_proxy.csv"
    proxy.to_csv(proxy_path, index=False)

    summaries = []
    for name in list_datasets(train_dir)[: cfg.hyperparam_sample_limit]:
        zarr_path = train_dir / f"{name}.zarr"
        shape, _ = read_zarr_meta(zarr_path)
        max_frames = min(cfg.hyperparam_frames, shape[0])
        t0 = time.time()
        result = run_tracking_pipeline(zarr_path, cfg, dataset_name=name, max_frames=max_frames)
        row = summarize_result(result, cfg)
        row["runtime_s"] = round(time.time() - t0, 2)
        summaries.append(row)

    summary = pd.DataFrame(summaries)
    summary_path = output_dir / "validation_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"Wrote {proxy_path} and {summary_path}")
    return proxy, summary

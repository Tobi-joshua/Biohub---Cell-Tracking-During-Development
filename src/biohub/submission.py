"""Batch pipeline for exporting lineage CSV across multiple test volumes."""

from __future__ import annotations

import gc
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from biohub.config import Config, MATCH_GATE_UM, PIPELINE_VERSION, SCALE
from biohub.data import (
    list_datasets,
    load_geff_graph,
    load_volume,
    read_estimated_nodes,
    read_zarr_meta,
)
from biohub.detector import get_detector
from biohub.tracking import count_divisions, link_frames, prune_isolated_nodes
from biohub.tuning import hyperparameter_search


def _node_row(dataset: str, node_id: int, t: int, zyx) -> dict:
    z, y, x = [int(v) for v in zyx]
    return {
        "dataset": dataset,
        "row_type": "node",
        "node_id": int(node_id),
        "t": int(t),
        "z": z,
        "y": y,
        "x": x,
        "source_id": -1,
        "target_id": -1,
    }


def _edge_row(dataset: str, source_id: int, target_id: int) -> dict:
    return {
        "dataset": dataset,
        "row_type": "edge",
        "node_id": -1,
        "t": -1,
        "z": -1,
        "y": -1,
        "x": -1,
        "source_id": int(source_id),
        "target_id": int(target_id),
    }


def calibrate_detection(
    train_dir: Path,
    cfg: Config,
    sample_limit: int = 4,
    frames_per_sample: int = 5,
) -> float:
    """Sweep thresh_rel on training samples to match per-frame density."""
    detector = get_detector(cfg)
    names = list_datasets(train_dir)[:sample_limit]
    if not names:
        return cfg.thresh_rel

    grid = [0.26, 0.30, 0.34, 0.38]
    best_thresh, best_err = cfg.thresh_rel, np.inf

    for thresh in grid:
        cfg.thresh_rel = thresh
        ratios = []
        for name in names:
            est = read_estimated_nodes(train_dir / f"{name}.geff")
            if est is None or est <= 0:
                continue
            zarr_path = train_dir / f"{name}.zarr"
            shape, dtype = read_zarr_meta(zarr_path)
            n_frames = min(frames_per_sample, shape[0])
            n_pred = 0
            for t in range(n_frames):
                vol = load_volume(zarr_path, t, shape, dtype)
                coords, _, _ = detector.detect(vol, cfg)
                n_pred += len(coords)
            avg_per_frame = n_pred / max(n_frames, 1)
            target_per_frame = est / max(shape[0], 1)
            ratios.append(avg_per_frame / max(target_per_frame, 1e-6))
        if ratios:
            ratio = float(np.median(ratios))
            err = (ratio - 1.0) ** 2
            if ratio > 1.0:
                err += 0.75 * (ratio - 1.0) ** 2
            if err < best_err:
                best_err, best_thresh = err, thresh

    cfg.thresh_rel = best_thresh
    return best_thresh


def apply_train_tuning(cfg: Config) -> Tuple[Config, Optional[pd.DataFrame]]:
    """Run v1.4 hyperparameter search when enabled and train data exists."""
    if not cfg.run_hyperparameter_search or cfg.train_dir is None:
        return cfg, None
    print(f"Running hyperparameter search (v{PIPELINE_VERSION})...")
    best, table = hyperparameter_search(
        cfg.train_dir,
        cfg,
        sample_limit=cfg.hyperparam_sample_limit,
        frames=cfg.hyperparam_frames,
    )
    if len(table):
        print(table.head(3).to_string(index=False))
    return best, table


def process_dataset(
    split_dir: Path,
    name: str,
    cfg: Config,
) -> Tuple[List[dict], Dict[str, object]]:
    """Run detection + tracking on one dataset."""
    detector = get_detector(cfg)
    zarr_path = split_dir / f"{name}.zarr"
    shape, dtype = read_zarr_meta(zarr_path)
    n_t = shape[0]

    node_rows: List[dict] = []
    edge_rows: List[dict] = []
    frame_ids: List[List[int]] = []
    frame_centroids: List[np.ndarray] = []
    frame_intensities: List[np.ndarray] = []
    node_id = 1
    prev_count: Optional[int] = None
    frame_counts: List[int] = []
    velocity_by_id: Dict[int, np.ndarray] = {}
    position_by_id: Dict[int, np.ndarray] = {}

    for t in range(n_t):
        vol = load_volume(zarr_path, t, shape, dtype)
        coords, scores, intens = detector.detect(vol, cfg, prev_count=prev_count)
        del vol
        gc.collect()

        if len(coords):
            order = np.lexsort((coords[:, 2], coords[:, 1], coords[:, 0]))
            coords = coords[order]
            intens = intens[order]

        curr_ids = list(range(node_id, node_id + len(coords)))
        node_id += len(coords)
        frame_ids.append(curr_ids)
        frame_centroids.append(coords)
        frame_intensities.append(intens)
        frame_counts.append(len(coords))
        prev_count = len(coords)

        for nid, pt in zip(curr_ids, coords):
            node_rows.append(_node_row(name, nid, t, pt))
            position_by_id[int(nid)] = pt.astype(np.float64)

    for t in range(1, n_t):
        prev_ids = frame_ids[t - 1]
        curr_ids = frame_ids[t]
        prev_xyz = frame_centroids[t - 1]
        curr_xyz = frame_centroids[t]
        prev_int = frame_intensities[t - 1]
        curr_int = frame_intensities[t]
        prev_vel = np.asarray(
            [velocity_by_id.get(pid, np.zeros(3, dtype=np.float64)) for pid in prev_ids],
            dtype=np.float64,
        )

        links = link_frames(
            prev_ids,
            prev_xyz,
            curr_ids,
            curr_xyz,
            cfg,
            prev_intensity=prev_int,
            curr_intensity=curr_int,
            prev_velocity=prev_vel if cfg.use_rich_linking else None,
        )
        for s, u in links:
            edge_rows.append(_edge_row(name, s, u))
            if s in position_by_id and u in position_by_id:
                velocity_by_id[u] = (
                    position_by_id[u] - position_by_id[s]
                ) * cfg.scale_array

    nodes_before = len(node_rows)
    edges_before = len(edge_rows)
    div_before = count_divisions(edge_rows)

    if cfg.prune_isolated_nodes:
        node_rows, edge_rows, prune_stats = prune_isolated_nodes(node_rows, edge_rows)
    else:
        prune_stats = {"removed_isolated": 0}

    stats = {
        "dataset": name,
        "shape": shape,
        "nodes_before_prune": nodes_before,
        "edges_before_prune": edges_before,
        "nodes_after_prune": len(node_rows),
        "edges_after_prune": len(edge_rows),
        "divisions": count_divisions(edge_rows),
        "divisions_before_prune": div_before,
        "removed_isolated": prune_stats.get("removed_isolated", 0),
        "count_min": int(min(frame_counts)) if frame_counts else 0,
        "count_max": int(max(frame_counts)) if frame_counts else 0,
        "count_mean": float(np.mean(frame_counts)) if frame_counts else 0.0,
    }
    return node_rows + edge_rows, stats


def build_submission(cfg: Optional[Config] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Process all test datasets and write a combined lineage CSV."""
    cfg = cfg or Config()
    cfg.resolve_paths()
    if cfg.test_dir is None:
        raise FileNotFoundError("Test directory not found")

    if cfg.train_dir is not None:
        cfg, _ = apply_train_tuning(cfg)
        calibrate_detection(cfg.train_dir, cfg, cfg.eda_sample_limit, cfg.calibration_frames)

    datasets = list_datasets(cfg.test_dir)
    all_rows: List[dict] = []
    all_stats = []
    t0 = time.time()

    print(f"Pipeline v{PIPELINE_VERSION} | detector={cfg.detector_backend} | thresh_rel={cfg.thresh_rel:.2f}")

    for i, name in enumerate(datasets, 1):
        rows, stats = process_dataset(cfg.test_dir, name, cfg)
        all_rows.extend(rows)
        all_stats.append(stats)
        elapsed = time.time() - t0
        print(
            f"[{i}/{len(datasets)}] {name}: "
            f"{stats['nodes_after_prune']} nodes, {stats['edges_after_prune']} edges, "
            f"{stats['divisions']} divisions ({elapsed:.0f}s)"
        )

    cols = ["dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
    sub = pd.DataFrame(all_rows)[cols]
    sub.index.name = "id"
    sub.to_csv(cfg.output_path)
    print(f"Wrote {cfg.output_path} ({len(sub):,} rows) in {(time.time()-t0)/60:.1f} min")
    return sub, pd.DataFrame(all_stats)


def validate_submission(sub: pd.DataFrame, test_dir: Path) -> None:
    """Assert submission format and graph consistency."""
    expected = ["dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
    assert list(sub.columns) == expected, f"Wrong columns: {list(sub.columns)}"
    assert len(sub) > 0, "Empty submission"

    datasets = set(list_datasets(test_dir))
    assert datasets.issubset(set(sub["dataset"].unique())), "Missing test datasets"

    nodes = sub[sub.row_type == "node"]
    edges = sub[sub.row_type == "edge"]
    assert (nodes[["node_id", "t", "z", "y", "x"]] >= 0).all().all()
    assert (nodes[["source_id", "target_id"]] == -1).all().all()
    assert (edges[["node_id", "t", "z", "y", "x"]] == -1).all().all()
    assert (edges[["source_id", "target_id"]] >= 0).all().all()

    for ds, grp in sub.groupby("dataset"):
        nset = set(grp.loc[grp.row_type == "node", "node_id"].astype(int))
        e = grp[grp.row_type == "edge"]
        assert e["source_id"].astype(int).isin(nset).all(), f"dangling source in {ds}"
        assert e["target_id"].astype(int).isin(nset).all(), f"dangling target in {ds}"

    print("Validation passed")


def local_recall_proxy(
    gt_nodes: pd.DataFrame,
    pred_xyz: np.ndarray,
    t: int,
    scale: np.ndarray = np.array(SCALE),
    gate_um: float = MATCH_GATE_UM,
) -> float:
    """Fraction of GT nodes at time t matched by a prediction within gate_um."""
    gt_t = gt_nodes[gt_nodes["t"] == t]
    if len(gt_t) == 0 or len(pred_xyz) == 0:
        return np.nan
    gt_phys = gt_t[["z", "y", "x"]].to_numpy(dtype=np.float64) * scale
    pred_phys = pred_xyz.astype(np.float64) * scale
    matched = 0
    for g in gt_phys:
        d = np.sqrt(((pred_phys - g) ** 2).sum(axis=1))
        if np.min(d) <= gate_um:
            matched += 1
    return matched / len(gt_t)

"""Systematic hyperparameter search on training data (v1.4)."""

from __future__ import annotations

import copy
from dataclasses import fields
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from biohub.config import Config, MATCH_GATE_UM, SCALE
from biohub.data import list_datasets, load_geff_graph, load_volume, read_zarr_meta
from biohub.detection import detect_cells
from biohub.tracking import link_frames


def _edge_proxy(
    gt_nodes: pd.DataFrame,
    gt_edges: pd.DataFrame,
    pred_edges: List[Tuple[int, int]],
    pred_id_to_gt: Dict[int, int],
) -> float:
    if not pred_edges or gt_edges is None or len(gt_edges) == 0:
        return 0.0
    gt_set = set(map(tuple, gt_edges[["source_id", "target_id"]].astype(int).to_numpy()))
    tp = 0
    for s, t in pred_edges:
        gs, gt = pred_id_to_gt.get(s), pred_id_to_gt.get(t)
        if gs is not None and gt is not None and (gs, gt) in gt_set:
            tp += 1
    denom = len(pred_edges) + max(len(gt_set) - tp, 0)
    return tp / denom if denom else 0.0


def _match_nodes_to_gt(
    pred_xyz: np.ndarray,
    gt_frame: pd.DataFrame,
    scale: np.ndarray,
    gate_um: float = MATCH_GATE_UM,
) -> Dict[int, int]:
    """Map predicted index -> gt node_id using greedy nearest matching."""
    if len(pred_xyz) == 0 or len(gt_frame) == 0:
        return {}
    gt_xyz = gt_frame[["z", "y", "x"]].to_numpy(dtype=np.float64)
    gt_ids = gt_frame["node_id"].astype(int).to_numpy()
    pred_phys = pred_xyz.astype(np.float64) * scale
    gt_phys = gt_xyz * scale
    mapping: Dict[int, int] = {}
    used_gt = set()
    for i, p in enumerate(pred_phys):
        d = np.sqrt(((gt_phys - p) ** 2).sum(axis=1))
        j = int(np.argmin(d))
        if d[j] <= gate_um and j not in used_gt:
            mapping[i] = int(gt_ids[j])
            used_gt.add(j)
    return mapping


def score_config_on_sample(
    train_dir: Path,
    name: str,
    cfg: Config,
    n_frames: int = 4,
) -> Dict[str, float]:
    """Proxy score on one training sample using sparse GEFF labels."""
    gt_nodes, gt_edges = load_geff_graph(train_dir / f"{name}.geff")
    if gt_nodes is None:
        return {"recall": np.nan, "edge_proxy": np.nan, "divisions": 0.0, "score": np.nan}

    zarr_path = train_dir / f"{name}.zarr"
    shape, dtype = read_zarr_meta(zarr_path)
    scale = cfg.scale_array

    recalls = []
    edge_proxies = []
    divisions = 0
    prev_xyz = np.empty((0, 3))
    prev_int = np.empty((0,))
    prev_vel = None
    prev_ids: List[int] = []
    pred_id = 1
    idx_to_pred_id: Dict[int, int] = {}
    pred_id_to_gt: Dict[int, int] = {}

    for t in range(min(n_frames, shape[0])):
        vol = load_volume(zarr_path, t, shape, dtype)
        coords, _, intens = detect_cells(vol, cfg, prev_count=len(prev_xyz) if t else None)
        gt_t = gt_nodes[gt_nodes["t"] == t]
        if len(gt_t) and len(coords):
            gt_phys = gt_t[["z", "y", "x"]].to_numpy(dtype=np.float64) * scale
            pred_phys = coords.astype(np.float64) * scale
            matched = 0
            for g in gt_phys:
                if np.min(np.sqrt(((pred_phys - g) ** 2).sum(axis=1))) <= MATCH_GATE_UM:
                    matched += 1
            recalls.append(matched / len(gt_t))

        frame_map = _match_nodes_to_gt(coords, gt_t, scale)
        curr_ids = []
        for i in range(len(coords)):
            pid = pred_id
            pred_id += 1
            curr_ids.append(pid)
            idx_to_pred_id[i] = pid
            if i in frame_map:
                pred_id_to_gt[pid] = frame_map[i]

        if t > 0 and len(prev_ids) and len(curr_ids):
            links = link_frames(
                prev_ids,
                prev_xyz,
                curr_ids,
                coords,
                cfg,
                prev_intensity=prev_int,
                curr_intensity=intens,
                prev_velocity=prev_vel,
            )
            edge_proxies.append(_edge_proxy(gt_nodes, gt_edges, links, pred_id_to_gt))
            src_counts: Dict[int, int] = {}
            for s, _ in links:
                src_counts[s] = src_counts.get(s, 0) + 1
            divisions += sum(1 for c in src_counts.values() if c >= 2)

            if len(links):
                vel = {}
                pos = {pid: prev_xyz[i] for i, pid in enumerate(prev_ids)}
                pos.update({pid: coords[i] for i, pid in enumerate(curr_ids)})
                for s, u in links:
                    if s in pos and u in pos:
                        vel[u] = (pos[u] - pos[s]) * scale
                prev_vel = np.asarray(
                    [vel.get(pid, np.zeros(3)) for pid in prev_ids],
                    dtype=np.float64,
                )

        prev_xyz, prev_int, prev_ids = coords, intens, curr_ids

    recall = float(np.mean(recalls)) if recalls else 0.0
    edge_p = float(np.mean(edge_proxies)) if edge_proxies else 0.0
    div_rate = divisions / max(min(n_frames, shape[0]) - 1, 1)
    score = 0.45 * recall + 0.45 * edge_p + 0.10 * min(div_rate, 1.0)
    return {"recall": recall, "edge_proxy": edge_p, "divisions": float(divisions), "score": score}


def hyperparameter_search(
    train_dir: Path,
    cfg: Config,
    sample_limit: int = 3,
    frames: int = 4,
) -> Tuple[Config, pd.DataFrame]:
    """
    Grid search key hyperparameters on training samples.

    Returns best config and a results table.
    """
    names = list_datasets(train_dir)[:sample_limit]
    if not names:
        return cfg, pd.DataFrame()

    grid = {
        "thresh_rel": [0.26, 0.30, 0.34],
        "max_link_dist_um": [10.5, 11.0, 12.0],
        "div_parent_dist_um": [11.0, 12.0],
        "div_sister_dist_um": [7.0, 7.5, 8.0],
    }

    rows: List[dict] = []
    best_cfg = cfg
    best_score = -1.0

    base = {
        "thresh_rel": cfg.thresh_rel,
        "max_link_dist_um": cfg.max_link_dist_um,
        "div_parent_dist_um": cfg.div_parent_dist_um,
        "div_sister_dist_um": cfg.div_sister_dist_um,
    }

    def _iter_grid(d, keys, i=0, cur=None):
        cur = cur or {}
        if i == len(keys):
            yield cur
            return
        k = keys[i]
        for v in d[k]:
            cur[k] = v
            yield from _iter_grid(d, keys, i + 1, cur)

    for params in _iter_grid(grid, list(grid.keys())):
        trial = cfg.copy_with(**params)
        scores = [score_config_on_sample(train_dir, n, trial, frames) for n in names]
        mean_score = float(np.nanmean([s["score"] for s in scores]))
        row = {**params, "mean_score": mean_score}
        row.update({f"{k}_{i}": s[k] for i, s in enumerate(scores) for k in ("recall", "edge_proxy")})
        rows.append(row)
        if mean_score > best_score:
            best_score = mean_score
            best_cfg = trial.copy_with(**params)

    results = pd.DataFrame(rows).sort_values("mean_score", ascending=False)
    return best_cfg, results

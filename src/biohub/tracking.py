"""Frame-to-frame linking and division detection (v1.2 / v1.3)."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

from biohub.config import Config


def neighbor_signature(xyz_phys: np.ndarray, cfg: Config) -> np.ndarray:
    """K-nearest-neighbor offset vectors as a local context descriptor."""
    n = len(xyz_phys)
    if n == 0:
        return np.empty((0, cfg.neighborhood_k * 3), dtype=np.float64)
    k = min(cfg.neighborhood_k, max(n - 1, 0))
    if k == 0:
        return np.zeros((n, cfg.neighborhood_k * 3), dtype=np.float64)
    tree = cKDTree(xyz_phys)
    dists, idx = tree.query(xyz_phys, k=k + 1)
    sig = np.zeros((n, cfg.neighborhood_k * 3), dtype=np.float64)
    for i in range(n):
        nbrs = idx[i, 1:] if np.ndim(idx) > 1 else []
        for j, nb in enumerate(nbrs[: cfg.neighborhood_k]):
            if dists[i, j + 1] <= cfg.neighborhood_radius_um:
                sig[i, j * 3 : (j + 1) * 3] = xyz_phys[nb] - xyz_phys[i]
    return sig


def _intensity_cost(prev_i: np.ndarray, curr_j: np.ndarray) -> np.ndarray:
    if prev_i.size == 0 or curr_j.size == 0:
        return np.zeros((len(prev_i), len(curr_j)), dtype=np.float64)
    p = prev_i[:, None].astype(np.float64)
    c = curr_j[None, :].astype(np.float64)
    denom = np.maximum(np.maximum(p, c), 1.0)
    return np.abs(p - c) / denom


def _signature_cost(prev_sig: np.ndarray, curr_sig: np.ndarray) -> np.ndarray:
    if len(prev_sig) == 0 or len(curr_sig) == 0:
        return np.zeros((len(prev_sig), len(curr_sig)), dtype=np.float64)
    diff = prev_sig[:, None, :] - curr_sig[None, :, :]
    return np.sqrt((diff ** 2).sum(axis=2))


def build_link_cost(
    prev_phys: np.ndarray,
    curr_phys: np.ndarray,
    cfg: Config,
    prev_intensity: Optional[np.ndarray] = None,
    curr_intensity: Optional[np.ndarray] = None,
    prev_velocity: Optional[np.ndarray] = None,
    prev_sig: Optional[np.ndarray] = None,
    curr_sig: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Physical distance matrix plus optional rich-linking terms."""
    dist = np.sqrt(((prev_phys[:, None, :] - curr_phys[None, :, :]) ** 2).sum(axis=2))
    cost = dist.copy()

    if cfg.use_rich_linking:
        if prev_velocity is not None and len(prev_velocity) == len(prev_phys):
            predicted = prev_phys[:, None, :] + prev_velocity[:, None, :]
            motion_resid = np.sqrt(((curr_phys[None, :, :] - predicted) ** 2).sum(axis=2))
            cost = cost + cfg.motion_lambda * motion_resid
        if prev_intensity is not None and curr_intensity is not None:
            cost = cost + cfg.intensity_lambda * _intensity_cost(prev_intensity, curr_intensity)
        if prev_sig is not None and curr_sig is not None:
            sig_cost = _signature_cost(prev_sig, curr_sig)
            med = float(np.median(sig_cost[sig_cost > 0])) if np.any(sig_cost > 0) else 1.0
            cost = cost + cfg.neighborhood_lambda * (sig_cost / max(med, 1e-6))

    big = 1e6
    cost = np.where(dist <= cfg.max_link_dist_um, cost, big)
    return cost, dist


def link_frames(
    prev_ids: Sequence[int],
    prev_xyz: np.ndarray,
    curr_ids: Sequence[int],
    curr_xyz: np.ndarray,
    cfg: Config,
    prev_intensity: Optional[np.ndarray] = None,
    curr_intensity: Optional[np.ndarray] = None,
    prev_velocity: Optional[np.ndarray] = None,
    next_xyz: Optional[np.ndarray] = None,
) -> List[Tuple[int, int]]:
    """Hungarian assignment with rich costs plus division pass."""
    if len(prev_ids) == 0 or len(curr_ids) == 0:
        return []

    scale = cfg.scale_array
    prev_phys = prev_xyz.astype(np.float64) * scale[None, :]
    curr_phys = curr_xyz.astype(np.float64) * scale[None, :]

    prev_sig = neighbor_signature(prev_phys, cfg) if cfg.use_rich_linking else None
    curr_sig = neighbor_signature(curr_phys, cfg) if cfg.use_rich_linking else None

    cost, dist = build_link_cost(
        prev_phys,
        curr_phys,
        cfg,
        prev_intensity=prev_intensity,
        curr_intensity=curr_intensity,
        prev_velocity=prev_velocity,
        prev_sig=prev_sig,
        curr_sig=curr_sig,
    )

    ri, ci = linear_sum_assignment(cost)
    big = 1e6

    edges: List[Tuple[int, int]] = []
    parent_children: Dict[int, List[int]] = defaultdict(list)
    matched_curr = set()

    for r, c in zip(ri, ci):
        if cost[r, c] < big:
            edges.append((int(prev_ids[r]), int(curr_ids[c])))
            parent_children[int(r)].append(int(c))
            matched_curr.add(int(c))

    allow_div = cfg.detect_divisions
    if allow_div and cfg.div_min_count_gain > 0 and len(curr_ids) - len(prev_ids) < cfg.div_min_count_gain:
        allow_div = False

    if allow_div:
        for c in range(len(curr_ids)):
            if c in matched_curr:
                continue
            best_p, best_score = None, np.inf
            for p in range(len(prev_ids)):
                if dist[p, c] > cfg.div_parent_dist_um or len(parent_children.get(p, [])) != 1:
                    continue
                sister = parent_children[p][0]
                sister_dist = float(np.linalg.norm(curr_phys[c] - curr_phys[sister]))
                if sister_dist > cfg.div_sister_dist_um:
                    continue
                if cfg.div_use_midpoint_gate:
                    midpoint = 0.5 * (curr_phys[c] + curr_phys[sister])
                    mid_dist = float(np.linalg.norm(prev_phys[p] - midpoint))
                    if mid_dist > cfg.div_midpoint_dist_um:
                        continue
                score = float(dist[p, c] + 0.25 * sister_dist)
                if score < best_score:
                    best_p, best_score = p, score
            if best_p is not None:
                edges.append((int(prev_ids[best_p]), int(curr_ids[c])))
                parent_children[best_p].append(c)
                matched_curr.add(c)

    return edges


def prune_isolated_nodes(
    node_rows: List[dict],
    edge_rows: List[dict],
) -> Tuple[List[dict], List[dict], Dict[str, int]]:
    """Remove detections that never participate in an edge."""
    incident = set()
    for e in edge_rows:
        incident.add(int(e["source_id"]))
        incident.add(int(e["target_id"]))
    kept_nodes = [r for r in node_rows if int(r["node_id"]) in incident]
    kept_ids = {int(r["node_id"]) for r in kept_nodes}
    kept_edges = [
        e
        for e in edge_rows
        if int(e["source_id"]) in kept_ids and int(e["target_id"]) in kept_ids
    ]
    return kept_nodes, kept_edges, {
        "removed_isolated": len(node_rows) - len(kept_nodes),
        "kept_nodes": len(kept_nodes),
        "kept_edges": len(kept_edges),
    }


def count_divisions(edge_rows: List[dict]) -> int:
    src_counts = Counter(int(e["source_id"]) for e in edge_rows)
    return sum(1 for c in src_counts.values() if c >= 2)

"""Frame-to-frame linking and division detection."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment

from biohub.config import Config


def _has_next_detection(point_phys: np.ndarray, next_xyz: np.ndarray, cfg: Config) -> bool:
    if next_xyz is None or len(next_xyz) == 0:
        return False
    next_phys = next_xyz.astype(np.float64) * cfg.scale_array
    dist = np.sqrt(((next_phys - point_phys[None, :]) ** 2).sum(axis=1))
    return bool(np.any(dist <= cfg.max_link_dist_um))


def link_frames(
    prev_ids: Sequence[int],
    prev_xyz: np.ndarray,
    curr_ids: Sequence[int],
    curr_xyz: np.ndarray,
    cfg: Config,
    next_xyz: Optional[np.ndarray] = None,
) -> List[Tuple[int, int]]:
    """
    Hungarian assignment in physical space, plus optional division pass.

    A division is a parent with two outgoing edges to daughters in the next frame.
    """
    if len(prev_ids) == 0 or len(curr_ids) == 0:
        return []

    scale = cfg.scale_array
    prev_phys = prev_xyz.astype(np.float64) * scale[None, :]
    curr_phys = curr_xyz.astype(np.float64) * scale[None, :]
    dist = np.sqrt(((prev_phys[:, None, :] - curr_phys[None, :, :]) ** 2).sum(axis=2))

    big = 1e6
    cost = np.where(dist <= cfg.max_link_dist_um, dist, big)
    ri, ci = linear_sum_assignment(cost)

    edges: List[Tuple[int, int]] = []
    parent_children: Dict[int, List[int]] = defaultdict(list)
    matched_curr = set()

    for r, c in zip(ri, ci):
        if cost[r, c] < big:
            edges.append((int(prev_ids[r]), int(curr_ids[c])))
            parent_children[int(r)].append(int(c))
            matched_curr.add(int(c))

    allow_div = cfg.detect_divisions
    if allow_div and len(curr_ids) - len(prev_ids) < cfg.div_min_count_gain:
        allow_div = False

    if allow_div:
        for c in range(len(curr_ids)):
            if c in matched_curr:
                continue
            best_p, best_d = None, np.inf
            for p in range(len(prev_ids)):
                if dist[p, c] > cfg.div_parent_dist_um or len(parent_children.get(p, [])) != 1:
                    continue
                sister = parent_children[p][0]
                sister_dist = float(np.linalg.norm(curr_phys[c] - curr_phys[sister]))
                if sister_dist > cfg.div_sister_dist_um:
                    continue
                if cfg.div_require_continued:
                    if next_xyz is None:
                        continue
                    if not (
                        _has_next_detection(curr_phys[c], next_xyz, cfg)
                        and _has_next_detection(curr_phys[sister], next_xyz, cfg)
                    ):
                        continue
                if dist[p, c] < best_d:
                    best_p, best_d = p, dist[p, c]
            if best_p is not None:
                edges.append((int(prev_ids[best_p]), int(curr_ids[c])))
                parent_children[best_p].append(c)
                matched_curr.add(c)

    return edges


def prune_isolated_nodes(
    node_rows: List[dict],
    edge_rows: List[dict],
) -> Tuple[List[dict], List[dict], Dict[str, int]]:
    """Remove detections that never participate in an edge (reduces node-count penalty)."""
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

"""Visualization helpers for analysis and publication figures."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np

from biohub.analysis import AnalysisResult

PLOT_STYLE = {
    "figure.dpi": 120,
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
}


def apply_style() -> None:
    plt.rcParams.update(PLOT_STYLE)


def mip(vol: np.ndarray, axis: int = 0) -> np.ndarray:
    return vol.max(axis=axis)


def plot_intensity_histogram(vol: np.ndarray, title: str = "Intensity distribution") -> plt.Figure:
    apply_style()
    fig, ax = plt.subplots(figsize=(5, 3))
    sample = vol.ravel()
    if sample.size > 500_000:
        rng = np.random.default_rng(0)
        sample = rng.choice(sample, size=500_000, replace=False)
    ax.hist(sample, bins=80, color="#3366AA", alpha=0.85, edgecolor="white", linewidth=0.3)
    ax.set_xlabel("intensity")
    ax.set_ylabel("count")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def plot_slice_overlay(
    vol: np.ndarray,
    z_idx: int,
    centroids: Optional[np.ndarray] = None,
    title: str = "",
    highlight_divisions: Optional[np.ndarray] = None,
) -> plt.Figure:
    apply_style()
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.imshow(vol[z_idx], cmap="gray", aspect="equal")
    if centroids is not None and len(centroids):
        zc, yc, xc = centroids[:, 0], centroids[:, 1], centroids[:, 2]
        on = np.abs(zc - z_idx) <= 1
        ax.scatter(xc[on], yc[on], s=18, c="#2E8B57", linewidths=0.4, edgecolors="white", label="detections")
        if highlight_divisions is not None and len(highlight_divisions):
            hd = highlight_divisions
            ond = np.abs(hd[:, 0] - z_idx) <= 1
            ax.scatter(hd[ond, 2], hd[ond, 1], s=40, facecolors="none", edgecolors="#C77C2E", linewidths=1.2, label="divisions")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(title or f"XY slice, z = {z_idx}")
    if centroids is not None and len(centroids):
        ax.legend(loc="upper right", fontsize=8, frameon=False)
    fig.tight_layout()
    return fig


def plot_volume_slices(
    vol: np.ndarray,
    centroids: Optional[np.ndarray] = None,
    title: str = "",
    z_idx: Optional[int] = None,
) -> plt.Figure:
    apply_style()
    if z_idx is None:
        z_idx = vol.shape[0] // 2
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.5))
    axes[0].imshow(vol[z_idx], cmap="gray", aspect="equal")
    axes[0].set_title(f"XY @ z={z_idx}")
    axes[1].imshow(mip(vol, axis=2), cmap="gray", aspect="auto")
    axes[1].set_title("ZY projection")
    axes[2].imshow(mip(vol, axis=1), cmap="gray", aspect="auto")
    axes[2].set_title("ZX projection")
    if centroids is not None and len(centroids):
        zc, yc, xc = centroids[:, 0], centroids[:, 1], centroids[:, 2]
        on_slice = np.abs(zc - z_idx) <= 1
        axes[0].scatter(xc[on_slice], yc[on_slice], s=12, c="#2E8B57", linewidths=0.5, edgecolors="white")
    if title:
        fig.suptitle(title, y=1.02)
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    return fig


def plot_frame_counts(counts: Sequence[int], title: str = "Detections per frame") -> plt.Figure:
    apply_style()
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(counts, color="#3366AA", linewidth=1.2)
    ax.set_xlabel("frame")
    ax.set_ylabel("detections")
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


def plot_gt_overlay(
    vol: np.ndarray,
    gt_xyz: np.ndarray,
    pred_xyz: Optional[np.ndarray] = None,
    t: int = 0,
    title: str = "",
) -> plt.Figure:
    """Overlay ground-truth and optional predictions on a mid-Z slice."""
    apply_style()
    z_mid = int(np.median(gt_xyz[:, 0])) if len(gt_xyz) else vol.shape[0] // 2
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(vol[z_mid], cmap="gray")
    if len(gt_xyz):
        on = np.abs(gt_xyz[:, 0] - z_mid) <= 1
        ax.scatter(gt_xyz[on, 2], gt_xyz[on, 1], s=20, c="cyan", label="GT", alpha=0.8)
    if pred_xyz is not None and len(pred_xyz):
        on = np.abs(pred_xyz[:, 0] - z_mid) <= 1
        ax.scatter(pred_xyz[on, 2], pred_xyz[on, 1], s=14, c="lime", label="pred", alpha=0.7)
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    ax.set_title(title or f"t={t}, z={z_mid}")
    ax.axis("off")
    fig.tight_layout()
    return fig


def plot_track_overlay(
    vol: np.ndarray,
    frame_a: np.ndarray,
    frame_b: np.ndarray,
    links: Sequence[tuple],
    z_idx: int,
    title: str = "Track overlay",
) -> plt.Figure:
    apply_style()
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    base = 0.5 * vol[z_idx].astype(np.float32) + 0.5 * vol[z_idx].astype(np.float32)
    ax.imshow(base, cmap="gray")
    if len(frame_a) and len(frame_b):
        za, ya, xa = frame_a[:, 0], frame_a[:, 1], frame_a[:, 2]
        zb, yb, xb = frame_b[:, 0], frame_b[:, 1], frame_b[:, 2]
        on_a = np.abs(za - z_idx) <= 1
        on_b = np.abs(zb - z_idx) <= 1
        ax.scatter(xa[on_a], ya[on_a], s=16, c="#3366AA", label="t")
        ax.scatter(xb[on_b], yb[on_b], s=16, c="#2E8B57", label="t+1")
        id_to_xy_a = {i + 1: (xa[i], ya[i]) for i in range(len(frame_a)) if on_a[i]}
        id_to_xy_b = {i + 1: (xb[i], yb[i]) for i in range(len(frame_b)) if on_b[i]}
        for s, t in links:
            if s in id_to_xy_a and t in id_to_xy_b:
                x1, y1 = id_to_xy_a[s]
                x2, y2 = id_to_xy_b[t]
                ax.plot([x1, x2], [y1, y2], color="#C77C2E", linewidth=0.8, alpha=0.8)
    ax.set_title(title)
    ax.axis("off")
    fig.tight_layout()
    return fig


def plot_lineage_graph(result: AnalysisResult, max_nodes: int = 120) -> plt.Figure:
    apply_style()
    import networkx as nx

    g = nx.DiGraph()
    if not result.nodes.empty:
        sub = result.nodes.head(max_nodes)
        for row in sub.itertuples(index=False):
            g.add_node(int(row.node_id), t=int(row.t))
    if not result.edges.empty:
        for row in result.edges.itertuples(index=False):
            g.add_edge(int(row.source_id), int(row.target_id))

    fig, ax = plt.subplots(figsize=(7, 5))
    if g.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "No graph to display", ha="center", va="center")
        ax.axis("off")
        return fig

    pos = nx.spring_layout(g, seed=42, k=0.45)
    nx.draw_networkx_nodes(g, pos, node_size=40, node_color="#3366AA", alpha=0.85, ax=ax)
    nx.draw_networkx_edges(g, pos, edge_color="#6B7280", arrows=True, arrowsize=8, width=0.7, ax=ax)
    ax.set_title("Lineage graph")
    ax.axis("off")
    fig.tight_layout()
    return fig


def save_figure(fig: plt.Figure, path: Path, dpi: int = 200) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path

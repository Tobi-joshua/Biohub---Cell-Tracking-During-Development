"""Visualization helpers for analysis and publication figures."""

from __future__ import annotations

import io
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np

from biohub.analysis import AnalysisResult
from biohub.config import SCALE

PLOT_STYLE = {
    "figure.dpi": 150,
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "lines.linewidth": 1.2,
}

COLORS = {
    "detection": "#1B9E77",
    "division": "#D95F02",
    "link": "#7570B3",
    "gt": "#66C2A5",
    "pred": "#FC8D62",
    "accent": "#3366AA",
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


def _add_scale_bar(ax: plt.Axes, pixel_size_um: float, length_um: float = 20.0) -> None:
    """Draw a horizontal scale bar in the lower-left corner."""
    length_px = length_um / pixel_size_um
    y0, x0 = ax.get_ylim()[0] + 4, ax.get_xlim()[0] + 4
    ax.plot([x0, x0 + length_px], [y0, y0], color="white", linewidth=2.5, solid_capstyle="butt")
    ax.plot([x0, x0 + length_px], [y0, y0], color="black", linewidth=1.2, solid_capstyle="butt")
    ax.text(
        x0 + length_px / 2,
        y0 + 6,
        f"{length_um:.0f} µm",
        ha="center",
        va="bottom",
        fontsize=8,
        color="white",
        bbox=dict(boxstyle="round,pad=0.15", facecolor="black", alpha=0.55, edgecolor="none"),
    )


def plot_slice_overlay(
    vol: np.ndarray,
    z_idx: int,
    centroids: Optional[np.ndarray] = None,
    title: str = "",
    highlight_divisions: Optional[np.ndarray] = None,
    show_scale_bar: bool = True,
) -> plt.Figure:
    apply_style()
    fig, ax = plt.subplots(figsize=(6, 6))
    vmin, vmax = np.percentile(vol[z_idx], (1, 99.5))
    ax.imshow(vol[z_idx], cmap="gray", aspect="equal", vmin=vmin, vmax=vmax)
    if centroids is not None and len(centroids):
        zc, yc, xc = centroids[:, 0], centroids[:, 1], centroids[:, 2]
        on = np.abs(zc - z_idx) <= 1
        ax.scatter(
            xc[on],
            yc[on],
            s=28,
            c=COLORS["detection"],
            linewidths=0.5,
            edgecolors="white",
            alpha=0.92,
            label="detections",
        )
        if highlight_divisions is not None and len(highlight_divisions):
            hd = highlight_divisions
            ond = np.abs(hd[:, 0] - z_idx) <= 1
            ax.scatter(
                hd[ond, 2],
                hd[ond, 1],
                s=70,
                facecolors="none",
                edgecolors=COLORS["division"],
                linewidths=1.6,
                label="divisions",
            )
    ax.set_xlabel("x (pixels)")
    ax.set_ylabel("y (pixels)")
    ax.set_title(title or f"XY slice, z = {z_idx}")
    if centroids is not None and len(centroids):
        ax.legend(loc="upper right", frameon=True, fancybox=False, edgecolor="#cccccc")
    if show_scale_bar:
        _add_scale_bar(ax, SCALE[2])
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
    vol_a: np.ndarray,
    frame_a: np.ndarray,
    frame_b: np.ndarray,
    links: Sequence[tuple],
    z_idx: int,
    vol_b: Optional[np.ndarray] = None,
    title: str = "Track overlay",
) -> plt.Figure:
    apply_style()
    fig, ax = plt.subplots(figsize=(6, 6))
    slice_a = vol_a[z_idx].astype(np.float32)
    slice_b = vol_b[z_idx].astype(np.float32) if vol_b is not None else slice_a
    base = 0.5 * slice_a + 0.5 * slice_b
    vmin, vmax = np.percentile(base, (1, 99.5))
    ax.imshow(base, cmap="gray", vmin=vmin, vmax=vmax)
    if len(frame_a) and len(frame_b):
        za, ya, xa = frame_a[:, 0], frame_a[:, 1], frame_a[:, 2]
        zb, yb, xb = frame_b[:, 0], frame_b[:, 1], frame_b[:, 2]
        on_a = np.abs(za - z_idx) <= 1
        on_b = np.abs(zb - z_idx) <= 1
        ax.scatter(xa[on_a], ya[on_a], s=22, c=COLORS["accent"], label="t", edgecolors="white", linewidths=0.4)
        ax.scatter(xb[on_b], yb[on_b], s=22, c=COLORS["detection"], label="t+1", edgecolors="white", linewidths=0.4)
        id_to_xy_a = {i + 1: (xa[i], ya[i]) for i in range(len(frame_a)) if on_a[i]}
        id_to_xy_b = {i + 1: (xb[i], yb[i]) for i in range(len(frame_b)) if on_b[i]}
        for s, t in links:
            if s in id_to_xy_a and t in id_to_xy_b:
                x1, y1 = id_to_xy_a[s]
                x2, y2 = id_to_xy_b[t]
                ax.plot([x1, x2], [y1, y2], color=COLORS["link"], linewidth=1.0, alpha=0.85)
    ax.set_title(title)
    ax.legend(loc="upper right", frameon=True, fancybox=False, edgecolor="#cccccc")
    _add_scale_bar(ax, SCALE[2])
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

    fig, ax = plt.subplots(figsize=(8, 5.5))
    if g.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "No graph to display", ha="center", va="center")
        ax.axis("off")
        return fig

    pos = nx.spring_layout(g, seed=42, k=0.45)
    nx.draw_networkx_nodes(g, pos, node_size=45, node_color=COLORS["accent"], alpha=0.9, ax=ax)
    nx.draw_networkx_edges(g, pos, edge_color="#6B7280", arrows=True, arrowsize=10, width=0.8, ax=ax)
    ax.set_title("Lineage graph (topology)")
    ax.axis("off")
    fig.tight_layout()
    return fig


def plot_lineage_timeline(result: AnalysisResult, max_tracks: int = 80) -> plt.Figure:
    """Spaghetti plot of track centroids over time (common in tracking papers)."""
    apply_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    if result.nodes.empty:
        ax.text(0.5, 0.5, "No tracks to display", ha="center", va="center")
        ax.axis("off")
        return fig

    nodes = result.nodes.sort_values(["node_id", "t"])
    track_ids = nodes["node_id"].unique()[:max_tracks]
    cmap = plt.cm.tab20(np.linspace(0, 1, min(len(track_ids), 20)))

    for i, tid in enumerate(track_ids):
        sub = nodes[nodes["node_id"] == tid]
        color = cmap[i % len(cmap)]
        ax.plot(sub["t"], sub["y"], color=color, alpha=0.75, linewidth=1.0)
        ax.scatter(sub["t"], sub["y"], s=10, color=color, alpha=0.85, edgecolors="none")

    ax.set_xlabel("time frame")
    ax.set_ylabel("y position (pixels)")
    ax.set_title("Track trajectories over time")
    ax.grid(True, alpha=0.2, linestyle="--")
    fig.tight_layout()
    return fig


def plot_temporal_montage(
    vol4d: np.ndarray,
    frames: Sequence,
    z_idx: int,
    frame_indices: Optional[Sequence[int]] = None,
    title: str = "Temporal montage",
) -> plt.Figure:
    """Multi-panel strip of detection overlays across selected frames."""
    apply_style()
    n_t = vol4d.shape[0]
    if frame_indices is None:
        frame_indices = np.linspace(0, n_t - 1, min(6, n_t), dtype=int)
    frame_indices = list(frame_indices)
    ncols = len(frame_indices)
    fig, axes = plt.subplots(1, ncols, figsize=(2.8 * ncols, 3.2))
    if ncols == 1:
        axes = [axes]

    for ax, t_idx in zip(axes, frame_indices):
        vol = vol4d[t_idx]
        vmin, vmax = np.percentile(vol[z_idx], (1, 99.5))
        ax.imshow(vol[z_idx], cmap="gray", vmin=vmin, vmax=vmax)
        coords = frames[t_idx].coords if t_idx < len(frames) else None
        if coords is not None and len(coords):
            zc, yc, xc = coords[:, 0], coords[:, 1], coords[:, 2]
            on = np.abs(zc - z_idx) <= 1
            ax.scatter(xc[on], yc[on], s=12, c=COLORS["detection"], edgecolors="white", linewidths=0.3)
        ax.set_title(f"t = {t_idx}", fontsize=9)
        ax.axis("off")

    fig.suptitle(title, y=1.02, fontsize=11)
    fig.tight_layout()
    return fig


def build_overlay_gif(
    vol4d: np.ndarray,
    frames: Sequence,
    z_idx: int,
    fps: int = 4,
    highlight_divisions: Optional[np.ndarray] = None,
) -> bytes:
    """Render a time-lapse GIF of detection overlays for Streamlit display or export."""
    import imageio.v3 as imageio

    images: List[np.ndarray] = []
    for t_idx in range(vol4d.shape[0]):
        fig = plot_slice_overlay(
            vol4d[t_idx],
            z_idx,
            frames[t_idx].coords if t_idx < len(frames) else None,
            title=f"t = {t_idx}",
            highlight_divisions=highlight_divisions,
            show_scale_bar=False,
        )
        fig.canvas.draw()
        rgba = np.asarray(fig.canvas.buffer_rgba())
        images.append(rgba[:, :, :3].copy())
        plt.close(fig)

    buf = io.BytesIO()
    imageio.imwrite(buf, images, extension=".gif", fps=fps, loop=0)
    return buf.getvalue()


def save_figure(fig: plt.Figure, path: Path, dpi: int = 200) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path

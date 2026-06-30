"""Visualization helpers for EDA and sanity checks."""

from __future__ import annotations

from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np


def mip(vol: np.ndarray, axis: int = 0) -> np.ndarray:
    """Maximum intensity projection along axis (0=Z, 1=Y, 2=X)."""
    return vol.max(axis=axis)


def plot_volume_slices(
    vol: np.ndarray,
    centroids: Optional[np.ndarray] = None,
    title: str = "",
    z_idx: Optional[int] = None,
) -> plt.Figure:
    """Show XY slice at mid-Z plus ZY and ZX projections."""
    if z_idx is None:
        z_idx = vol.shape[0] // 2
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.5))

    axes[0].imshow(vol[z_idx], cmap="gray", aspect="equal")
    axes[0].set_title(f"XY @ z={z_idx}")
    axes[1].imshow(mip(vol, axis=2), cmap="gray", aspect="auto")
    axes[1].set_title("ZY (max proj)")
    axes[2].imshow(mip(vol, axis=1), cmap="gray", aspect="auto")
    axes[2].set_title("ZX (max proj)")

    if centroids is not None and len(centroids):
        zc, yc, xc = centroids[:, 0], centroids[:, 1], centroids[:, 2]
        on_slice = np.abs(zc - z_idx) <= 1
        axes[0].scatter(xc[on_slice], yc[on_slice], s=12, c="lime", linewidths=0.5, edgecolors="k")

    if title:
        fig.suptitle(title, y=1.02)
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    return fig


def plot_frame_counts(counts: Sequence[int], title: str = "Nodes per frame") -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 3))
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
    z_mid = int(np.median(gt_xyz[:, 0])) if len(gt_xyz) else vol.shape[0] // 2
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(vol[z_mid], cmap="gray")
    if len(gt_xyz):
        on = np.abs(gt_xyz[:, 0] - z_mid) <= 1
        ax.scatter(gt_xyz[on, 2], gt_xyz[on, 1], s=20, c="cyan", label="GT", alpha=0.8)
    if pred_xyz is not None and len(pred_xyz):
        on = np.abs(pred_xyz[:, 0] - z_mid) <= 1
        ax.scatter(pred_xyz[on, 2], pred_xyz[on, 1], s=14, c="lime", label="pred", alpha=0.7)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(title or f"t={t}, z={z_mid}")
    ax.axis("off")
    fig.tight_layout()
    return fig

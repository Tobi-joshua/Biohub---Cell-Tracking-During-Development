#!/usr/bin/env python3
"""Generate publication figures for the paper and figures/ directory."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
FIGURES = ROOT / "figures"

from biohub.analysis import run_tracking_pipeline
from biohub.config import Config
from biohub.sample_data import synthetic_volume
from biohub.visualization import (
    plot_frame_counts,
    plot_lineage_graph,
    plot_lineage_timeline,
    plot_slice_overlay,
    plot_temporal_montage,
    plot_volume_slices,
    save_figure,
)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    cfg = Config()
    vol4d = synthetic_volume(t=16, z=32, y=96, x=96, n_cells=20)
    result = run_tracking_pipeline(list(vol4d), cfg, dataset_name="figure_sample")

    save_figure(
        plot_volume_slices(vol4d[0], result.frames[0].coords, title="Sample volume and detections"),
        FIGURES / "sample_volume.png",
    )
    save_figure(
        plot_slice_overlay(vol4d[5], 16, result.frames[5].coords, title="Detection overlay"),
        FIGURES / "detection_overlay.png",
    )
    save_figure(
        plot_frame_counts([len(f.coords) for f in result.frames], title="Detections per frame"),
        FIGURES / "frame_counts.png",
    )
    save_figure(plot_lineage_graph(result), FIGURES / "lineage_graph.png")
    save_figure(plot_lineage_timeline(result), FIGURES / "lineage_timeline.png")
    save_figure(
        plot_temporal_montage(vol4d, result.frames, z_idx=16, title="Temporal detection montage"),
        FIGURES / "temporal_montage.png",
    )

    # Pipeline schematic (simple matplotlib diagram)
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 2.2))
    steps = ["Volume", "Detection", "Linking", "Lineage", "Export"]
    xs = range(len(steps))
    ax.scatter(xs, [0] * len(steps), s=400, c="#3366AA", zorder=2)
    for i, label in enumerate(steps):
        ax.annotate(label, (i, 0), ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        if i < len(steps) - 1:
            ax.annotate("", xy=(i + 0.72, 0), xytext=(i + 0.28, 0), arrowprops=dict(arrowstyle="->", color="#6B7280"))
    ax.set_xlim(-0.5, len(steps) - 0.5)
    ax.axis("off")
    ax.set_title("Processing pipeline")
    save_figure(fig, FIGURES / "pipeline_overview.png")

    print(f"Wrote figures to {FIGURES}")
    print("Place a Streamlit UI screenshot at figures/ui_screenshot.png after running the app.")


if __name__ == "__main__":
    main()

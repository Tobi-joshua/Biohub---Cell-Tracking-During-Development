#!/usr/bin/env python3
"""Generate diagnostic plots for local pipeline analysis (Sprint 2)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from biohub.analysis import run_tracking_pipeline
from biohub.config import Config
from biohub.data import list_datasets, read_zarr_meta
from biohub.export import division_events
from biohub.validation import link_distance_stats, summarize_result, track_length_distribution


def plot_diagnostics(result, cfg: Config, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / name

    counts = [len(f.coords) for f in result.frames]
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(counts, marker="o", markersize=3)
    ax.set_xlabel("frame")
    ax.set_ylabel("detections")
    ax.set_title(f"{name}: detections per frame")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(f"{prefix}_detections_per_frame.png", dpi=150)
    plt.close(fig)

    lengths = track_length_distribution(result.edges)
    fig, ax = plt.subplots(figsize=(6, 3))
    if len(lengths):
        ax.hist(lengths.values, bins=min(30, max(5, len(lengths))), color="#3366AA", alpha=0.85)
    ax.set_xlabel("outgoing edges per source node")
    ax.set_ylabel("count")
    ax.set_title(f"{name}: track length proxy")
    fig.tight_layout()
    fig.savefig(f"{prefix}_track_lengths.png", dpi=150)
    plt.close(fig)

    stats = link_distance_stats(result.edges, result.nodes, cfg.scale_array)
    if not result.edges.empty:
        pos = result.nodes.set_index("node_id")[["z", "y", "x"]].astype(float)
        dists = []
        scale = cfg.scale_array
        for row in result.edges.itertuples(index=False):
            s, t = int(row.source_id), int(row.target_id)
            if s in pos.index and t in pos.index:
                a = pos.loc[s].to_numpy() * scale
                b = pos.loc[t].to_numpy() * scale
                dists.append(float(np.linalg.norm(a - b)))
        if dists:
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.hist(dists, bins=40, color="#2E8B57", alpha=0.85)
            ax.axvline(cfg.max_link_dist_um, color="red", linestyle="--", label=f"gate={cfg.max_link_dist_um}µm")
            ax.set_xlabel("link distance (µm)")
            ax.set_ylabel("count")
            ax.set_title(f"{name}: link distance histogram")
            ax.legend()
            fig.tight_layout()
            fig.savefig(f"{prefix}_link_distances.png", dpi=150)
            plt.close(fig)

    divs = division_events(result)
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.bar(["divisions"], [len(divs)], color="#D95F02")
    ax.set_ylabel("count")
    ax.set_title(f"{name}: division events ({len(divs)})")
    fig.tight_layout()
    fig.savefig(f"{prefix}_divisions.png", dpi=150)
    plt.close(fig)

    if result.frames and any(len(f.scores) for f in result.frames):
        scores = np.concatenate([f.scores for f in result.frames if len(f.scores)])
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.hist(scores, bins=50, color="#7570B3", alpha=0.85)
        ax.set_xlabel("detection score")
        ax.set_ylabel("count")
        ax.set_title(f"{name}: detection confidence")
        fig.tight_layout()
        fig.savefig(f"{prefix}_detection_scores.png", dpi=150)
        plt.close(fig)

    if not result.nodes.empty and "t" in result.nodes.columns:
        density = result.nodes.groupby("t").size()
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(density.index, density.values, marker="o", markersize=3, color="#E7298A")
        ax.set_xlabel("frame")
        ax.set_ylabel("nodes in graph")
        ax.set_title(f"{name}: node density per frame")
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        fig.savefig(f"{prefix}_node_density.png", dpi=150)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Biohub diagnostic plots")
    parser.add_argument("--train-dir", type=Path, help="Train split for labeled proxy run")
    parser.add_argument("--synthetic", action="store_true", help="Run on synthetic demo volume")
    parser.add_argument("--output-dir", type=Path, default=Path("results/diagnostics"))
    parser.add_argument("--frames", type=int, default=12)
    parser.add_argument("--preset", choices=["v4", "v5", "current"], default="v4")
    args = parser.parse_args()

    cfg = Config()
    if args.preset == "v4":
        cfg = cfg.competition_v4_preset()
    elif args.preset == "v5":
        cfg = cfg.copy_with(
            gap_close_enabled=True,
            prune_soft_neighbors=True,
            div_symmetry_weight=0.35,
            use_adaptive_frame_threshold=True,
        )

    summaries = []
    if args.synthetic:
        from biohub.sample_data import synthetic_volume

        vol = synthetic_volume(t=args.frames, z=32, y=96, x=96, n_cells=18)
        result = run_tracking_pipeline(list(vol), cfg, dataset_name="synthetic")
        plot_diagnostics(result, cfg, args.output_dir, "synthetic")
        summaries.append(summarize_result(result, cfg))
    elif args.train_dir:
        for name in list_datasets(args.train_dir)[:2]:
            zarr_path = args.train_dir / f"{name}.zarr"
            shape, _ = read_zarr_meta(zarr_path)
            max_f = min(args.frames, shape[0])
            result = run_tracking_pipeline(zarr_path, cfg, dataset_name=name, max_frames=max_f)
            plot_diagnostics(result, cfg, args.output_dir, name)
            summaries.append(summarize_result(result, cfg))
    else:
        parser.error("Provide --train-dir or --synthetic")

    summary = pd.DataFrame(summaries)
    summary["preset"] = args.preset
    out_csv = args.output_dir / f"diagnostics_summary_{args.preset}.csv"
    summary.to_csv(out_csv, index=False)
    print(f"Wrote plots and {out_csv}")


if __name__ == "__main__":
    main()

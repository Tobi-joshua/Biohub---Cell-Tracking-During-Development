#!/usr/bin/env python3
"""Rank low-risk one-knob candidates on local train labels."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from biohub.config import Config
from biohub.tuning import single_knob_sweep


def main() -> None:
    parser = argparse.ArgumentParser(description="Biohub single-knob candidate sweep")
    parser.add_argument("--train-dir", type=Path, required=True, help="Path to train/ split")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--frames", type=int, default=6)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/single_knob_sweep.csv"),
    )
    args = parser.parse_args()

    cfg = Config(train_dir=args.train_dir).competition_v4_preset()
    best, table = single_knob_sweep(args.train_dir, cfg, args.samples, args.frames)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output, index=False)

    print("\nTop candidates:")
    print(table.head(10).to_string(index=False))
    print(
        "\nBest candidate:",
        f"thresh_rel={best.thresh_rel:.3f}",
        f"max_link_dist_um={best.max_link_dist_um:.1f}",
        f"nms_radius_um={best.nms_radius_um:.2f}",
        f"div_parent={best.div_parent_dist_um:.1f}",
        f"div_sister={best.div_sister_dist_um:.1f}",
        f"density_calibration={best.run_density_calibration}",
    )
    print(f"\nWrote {len(table)} rows to {args.output}")


if __name__ == "__main__":
    main()

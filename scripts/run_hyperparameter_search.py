#!/usr/bin/env python3
"""Run hyperparameter search on local train data and write results CSV."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from biohub.config import Config
from biohub.tuning import hyperparameter_search


def main() -> None:
    parser = argparse.ArgumentParser(description="Biohub hyperparameter search")
    parser.add_argument("--train-dir", type=Path, required=True, help="Path to train/ split")
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--frames", type=int, default=4)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/hyperparameter_search.csv"),
    )
    args = parser.parse_args()

    cfg = Config(
        train_dir=args.train_dir,
        run_hyperparameter_search=True,
        hyperparam_sample_limit=args.samples,
        hyperparam_frames=args.frames,
        hyperparam_results_path=args.output,
    )
    best, table = hyperparameter_search(args.train_dir, cfg, args.samples, args.frames)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output, index=False)

    print("\nBest configuration:")
    print(
        f"  thresh_rel={best.thresh_rel:.3f}  max_link_dist_um={best.max_link_dist_um:.1f}  "
        f"div_parent={best.div_parent_dist_um:.1f}  div_sister={best.div_sister_dist_um:.1f}  "
        f"nms_radius_um={best.nms_radius_um:.2f}"
    )
    print(f"\nWrote {len(table)} rows to {args.output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run local validation proxy metrics and write diagnostic CSVs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from biohub.config import Config
from biohub.validation import run_validation_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Biohub local validation report")
    parser.add_argument("--train-dir", type=Path, required=True, help="Path to train/ split")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--frames", type=int, default=4)
    args = parser.parse_args()

    cfg = Config(
        train_dir=args.train_dir,
        hyperparam_sample_limit=args.samples,
        hyperparam_frames=args.frames,
    )
    run_validation_report(args.train_dir, cfg, args.output_dir)


if __name__ == "__main__":
    main()

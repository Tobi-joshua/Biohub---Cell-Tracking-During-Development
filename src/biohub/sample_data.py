"""Synthetic and bundled sample volumes for offline development."""

from __future__ import annotations

from pathlib import Path

import numpy as np


def synthetic_volume(
    t: int = 12,
    z: int = 32,
    y: int = 96,
    x: int = 96,
    n_cells: int = 18,
    seed: int = 42,
) -> np.ndarray:
    """
    Generate a fluorescent-cell-like 4D array `(T, Z, Y, X)`.

    Bright Gaussian blobs drift slowly and occasionally divide.
    """
    rng = np.random.default_rng(seed)
    vol = np.zeros((t, z, y, x), dtype=np.uint16)
    cells = []
    for _ in range(n_cells):
        cells.append(
            {
                "pos": np.array(
                    [rng.integers(4, z - 4), rng.integers(8, y - 8), rng.integers(8, x - 8)],
                    dtype=np.float64,
                ),
                "amp": rng.uniform(800, 2200),
            }
        )

    for frame in range(t):
        new_cells = []
        for cell in cells:
            cell["pos"] += rng.normal(0, 0.35, size=3)
            cell["pos"] = np.clip(cell["pos"], [2, 4, 4], [z - 3, y - 4, x - 4])
            cz, cy, cx = cell["pos"].astype(int)
            zz, yy, xx = np.ogrid[:z, :y, :x]
            blob = np.exp(
                -((zz - cz) ** 2 / 4.0 + (yy - cy) ** 2 / 1.5 + (xx - cx) ** 2 / 1.5)
            )
            vol[frame] += (cell["amp"] * blob).astype(np.uint16)
            if frame > 0 and frame % 5 == 0 and rng.random() < 0.08 and len(cells) + len(new_cells) < n_cells + 8:
                daughter = {"pos": cell["pos"] + rng.normal(0.8, 0.2, size=3), "amp": cell["amp"] * 0.9}
                new_cells.append(daughter)
        cells.extend(new_cells)
        vol[frame] += rng.integers(0, 30, size=(z, y, x), dtype=np.uint16)
    return vol


def load_sample_volume(path: Path | None = None) -> np.ndarray:
    path = path or Path("data/sample/synthetic_volume.npy")
    if path.exists():
        return np.load(path)
    return synthetic_volume()


def ensure_sample_data(path: Path | None = None) -> Path:
    path = path or Path("data/sample/synthetic_volume.npy")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        np.save(path, synthetic_volume())
    return path

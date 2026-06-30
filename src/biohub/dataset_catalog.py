"""Discover and index Biohub Cell Tracking dataset layouts on local disk."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

import numpy as np

from biohub.data import (
    list_datasets,
    load_geff_graph,
    load_volume,
    read_estimated_nodes,
    read_zarr_meta,
)


@dataclass(frozen=True)
class DatasetEntry:
    """One sample in the Biohub dataset (paired image volume + optional graph)."""

    name: str
    split: str
    zarr_path: Path
    geff_path: Optional[Path]
    shape: Tuple[int, ...]
    dtype: np.dtype
    estimated_nodes: Optional[float] = None
    n_geff_nodes: Optional[int] = None
    n_geff_edges: Optional[int] = None

    @property
    def has_geff(self) -> bool:
        return self.geff_path is not None and self.geff_path.exists()

    @property
    def label(self) -> str:
        tag = "train+labels" if self.has_geff else "image only"
        return f"{self.split}/{self.name} ({tag})"


@dataclass
class DatasetCatalog:
    """Indexed view of a downloaded Biohub dataset directory."""

    root: Path
    train_dir: Optional[Path] = None
    test_dir: Optional[Path] = None
    entries: List[DatasetEntry] = field(default_factory=list)

    @property
    def n_train(self) -> int:
        return sum(1 for e in self.entries if e.split == "train")

    @property
    def n_test(self) -> int:
        return sum(1 for e in self.entries if e.split == "test")

    def entries_for_split(self, split: str) -> List[DatasetEntry]:
        return [e for e in self.entries if e.split == split]

    def get(self, name: str, split: str) -> Optional[DatasetEntry]:
        for entry in self.entries:
            if entry.name == name and entry.split == split:
                return entry
        return None

    def labels(self) -> List[str]:
        return [e.label for e in self.entries]

    def by_label(self, label: str) -> Optional[DatasetEntry]:
        for entry in self.entries:
            if entry.label == label:
                return entry
        return None


def _is_zarr_dataset(path: Path) -> bool:
    return path.is_dir() and path.name.endswith(".zarr") and (path / "0" / "zarr.json").exists()


def _scan_split_dir(split_dir: Path, split_name: str) -> List[DatasetEntry]:
    if not split_dir.is_dir():
        return []
    entries: List[DatasetEntry] = []
    for name in list_datasets(split_dir):
        zarr_path = split_dir / f"{name}.zarr"
        geff_path = split_dir / f"{name}.geff"
        try:
            shape, dtype = read_zarr_meta(zarr_path)
        except (FileNotFoundError, OSError, ValueError, KeyError):
            continue
        geff = geff_path if geff_path.exists() else None
        est = read_estimated_nodes(geff) if geff else None
        n_nodes, n_edges = None, None
        if geff:
            nodes, edges = load_geff_graph(geff)
            if nodes is not None:
                n_nodes = len(nodes)
            if edges is not None:
                n_edges = len(edges)
        entries.append(
            DatasetEntry(
                name=name,
                split=split_name,
                zarr_path=zarr_path,
                geff_path=geff,
                shape=shape,
                dtype=dtype,
                estimated_nodes=est,
                n_geff_nodes=n_nodes,
                n_geff_edges=n_edges,
            )
        )
    return entries


def resolve_dataset_root(user_path: Path) -> Tuple[Path, Optional[Path], Optional[Path]]:
    """
    Normalize a user-selected path to (root, train_dir, test_dir).

    Accepts:
    - package root containing ``train/`` and/or ``test/``
    - a split directory itself (``.../train`` or ``.../test``)
    - a directory that directly contains ``*.zarr`` files
    """
    path = Path(user_path).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Directory not found: {path}")

    train_dir = path / "train"
    test_dir = path / "test"
    if train_dir.is_dir() or test_dir.is_dir():
        return (
            path,
            train_dir if train_dir.is_dir() else None,
            test_dir if test_dir.is_dir() else None,
        )

    if path.name in {"train", "test"} and any(path.glob("*.zarr")):
        root = path.parent
        if path.name == "train":
            return root, path, root / "test" if (root / "test").is_dir() else None
        return root, root / "train" if (root / "train").is_dir() else None, path

    if any(path.glob("*.zarr")):
        # Flat directory of zarr volumes — treat as a single unlabeled split.
        return path, path, None

    raise ValueError(
        "Could not find Biohub dataset layout. Expected train/ and/or test/ "
        "subdirectories, or a folder containing .zarr volumes."
    )


def discover_catalog(user_path: Path) -> DatasetCatalog:
    """Scan a local dataset root and return an indexed catalog."""
    root, train_dir, test_dir = resolve_dataset_root(user_path)
    entries: List[DatasetEntry] = []
    if train_dir is not None:
        entries.extend(_scan_split_dir(train_dir, "train"))
    if test_dir is not None:
        entries.extend(_scan_split_dir(test_dir, "test"))
    if not entries:
        raise ValueError(f"No .zarr datasets found under {user_path}")
    entries.sort(key=lambda e: (e.split, e.name))
    return DatasetCatalog(root=root, train_dir=train_dir, test_dir=test_dir, entries=entries)


def load_zarr_preview(
    entry: DatasetEntry,
    max_frames: Optional[int] = None,
    progress_callback=None,
) -> np.ndarray:
    """Load the first ``max_frames`` timepoints into a (T,Z,Y,X) array."""
    n_t = entry.shape[0]
    if max_frames is not None:
        n_t = min(n_t, int(max_frames))
    frames = []
    for t in range(n_t):
        frames.append(load_volume(entry.zarr_path, t, entry.shape, entry.dtype))
        if progress_callback is not None:
            progress_callback((t + 1) / n_t)
    return np.stack(frames, axis=0)


def iter_zarr_timepoints(entry: DatasetEntry) -> Iterator[np.ndarray]:
    """Yield (Z,Y,X) frames without building a full 4D array."""
    for t in range(entry.shape[0]):
        yield load_volume(entry.zarr_path, t, entry.shape, entry.dtype)

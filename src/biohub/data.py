"""Zarr volume and GEFF graph loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

try:
    import blosc2
except ImportError:
    blosc2 = None  # type: ignore

try:
    import zarr
except ImportError:
    zarr = None  # type: ignore


def list_datasets(split_dir: Path) -> List[str]:
    """Return sorted dataset names (without .zarr suffix)."""
    if not split_dir or not split_dir.is_dir():
        return []
    return sorted(p.name[:-5] for p in split_dir.iterdir() if p.name.endswith(".zarr"))


def read_zarr_meta(zarr_path: Path) -> Tuple[Tuple[int, ...], np.dtype]:
    """Read shape and dtype from zarr metadata."""
    meta_path = zarr_path / "0" / "zarr.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing metadata: {meta_path}")
    meta = json.loads(meta_path.read_text())
    return tuple(meta["shape"]), np.dtype(meta["data_type"])


def load_volume(
    zarr_path: Path,
    t: int,
    shape: Tuple[int, ...],
    dtype: np.dtype,
) -> np.ndarray:
    """Load one timepoint as (Z, Y, X)."""
    chunk = zarr_path / "0" / "c" / str(t) / "0" / "0" / "0"
    if blosc2 is not None and chunk.exists():
        raw = blosc2.decompress(chunk.read_bytes())
        return np.frombuffer(raw, dtype=dtype).reshape(shape[1:])
    if zarr is not None:
        arr = zarr.open_array(str(zarr_path / "0"), mode="r")
        return np.asarray(arr[t], dtype=dtype)
    raise ImportError("blosc2 or zarr required to read volumes")


def read_estimated_nodes(geff_path: Path) -> float | None:
    """Read estimated_number_of_nodes from GEFF metadata if present."""
    meta_path = geff_path / "zarr.json"
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text())
    except json.JSONDecodeError:
        return None

    def _find(obj):
        if isinstance(obj, dict):
            if "estimated_number_of_nodes" in obj:
                return obj["estimated_number_of_nodes"]
            for v in obj.values():
                found = _find(v)
                if found is not None:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = _find(item)
                if found is not None:
                    return found
        return None

    val = _find(meta)
    return float(val) if val is not None else None


def find_geff_path(split_dir: Path, name: str) -> Optional[Path]:
    """Locate a GEFF graph for ``name`` across common competition layouts."""
    candidates = [
        split_dir / f"{name}.geff",
        split_dir / "geff" / f"{name}.geff",
        split_dir / "graphs" / f"{name}.geff",
        split_dir / "labels" / f"{name}.geff",
        split_dir.parent / "geff" / f"{name}.geff",
        split_dir.parent / "graphs" / f"{name}.geff",
        split_dir.parent / "labels" / f"{name}.geff",
    ]
    return next((p for p in candidates if p.exists()), None)


def load_geff_graph(geff_path: Path):
    """Load node and edge tables from a GEFF directory."""
    if zarr is None or not geff_path.exists():
        return None, None
    try:
        import pandas as pd

        root = zarr.open_group(str(geff_path), mode="r")
        nodes_grp = root["nodes"]
        edges_grp = root["edges"]
        node_ids = np.asarray(nodes_grp["ids"])
        props = nodes_grp["props"]
        nodes = pd.DataFrame(
            {
                "node_id": node_ids,
                "t": np.asarray(props["t"]["values"]),
                "z": np.asarray(props["z"]["values"]),
                "y": np.asarray(props["y"]["values"]),
                "x": np.asarray(props["x"]["values"]),
            }
        )
        edge_ids = np.asarray(edges_grp["ids"])
        edges = pd.DataFrame({"source_id": edge_ids[:, 0], "target_id": edge_ids[:, 1]})
        return nodes, edges
    except Exception:
        return None, None

"""Streamlit UI helpers."""

from __future__ import annotations

import io
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import streamlit as st

from biohub.analysis import AnalysisResult, run_tracking_pipeline
from biohub.config import Config, PIPELINE_VERSION, SCALE
from biohub.data import list_datasets, load_volume, read_zarr_meta
from biohub.export import division_events, to_graph_json, to_lineage_csv
from biohub.sample_data import ensure_sample_data, load_sample_volume, synthetic_volume


def init_session() -> None:
    defaults = {
        "cfg": Config(),
        "volume_4d": None,
        "volume_source": "sample",
        "dataset_name": "synthetic",
        "result": None,
        "zarr_path": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def load_volumes_from_source(
    source: str,
    uploaded_bytes: Optional[bytes],
    zarr_path: str,
    preview_frames: int,
) -> Tuple[np.ndarray, str]:
    if source == "sample":
        path = ensure_sample_data()
        vol4d = load_sample_volume(path)
        name = "synthetic_sample"
    elif source == "upload_npy":
        if uploaded_bytes is None:
            raise ValueError("Upload a `.npy` file with shape (T, Z, Y, X).")
        vol4d = np.load(io.BytesIO(uploaded_bytes), allow_pickle=False)
        if vol4d.ndim != 4:
            raise ValueError(f"Expected 4D array (T,Z,Y,X); got shape {vol4d.shape}.")
        name = "uploaded_volume"
    elif source == "zarr":
        path = Path(zarr_path)
        if not path.is_dir():
            raise ValueError("Provide a valid `.zarr` dataset directory.")
        shape, dtype = read_zarr_meta(path)
        n_t = min(shape[0], preview_frames) if preview_frames else shape[0]
        frames = [load_volume(path, t, shape, dtype) for t in range(n_t)]
        vol4d = np.stack(frames, axis=0)
        name = path.name.replace(".zarr", "")
    else:
        vol4d = synthetic_volume(t=min(preview_frames, 12))
        name = "synthetic_preview"
    return vol4d, name


def run_pipeline(vol4d: np.ndarray, cfg: Config, name: str, preview_frames: int) -> AnalysisResult:
    frames = vol4d[:preview_frames] if preview_frames and preview_frames < vol4d.shape[0] else vol4d
    return run_tracking_pipeline(list(frames), cfg, dataset_name=name)


def sidebar_settings(cfg: Config) -> tuple[Config, str]:
    st.sidebar.header("Settings")
    mode = st.sidebar.radio("Processing mode", ["Preview", "Full sequence"], index=0)
    if mode == "Preview":
        preview_frames = st.sidebar.number_input("Preview frames", 3, 100, int(cfg.preview_max_frames))
    else:
        preview_frames = 10_000
    cfg = cfg.copy_with(
        thresh_rel=st.sidebar.slider("Detection threshold (rel.)", 0.18, 0.42, float(cfg.thresh_rel), 0.02),
        max_link_dist_um=st.sidebar.slider("Max link distance (µm)", 8.0, 14.0, float(cfg.max_link_dist_um), 0.5),
        div_parent_dist_um=st.sidebar.slider("Division parent gate (µm)", 8.0, 14.0, float(cfg.div_parent_dist_um), 0.5),
        div_sister_dist_um=st.sidebar.slider("Division sister gate (µm)", 5.0, 10.0, float(cfg.div_sister_dist_um), 0.5),
        detect_divisions=st.sidebar.checkbox("Detect divisions", value=cfg.detect_divisions),
        prune_isolated_nodes=st.sidebar.checkbox("Prune isolated nodes", value=cfg.prune_isolated_nodes),
        use_rich_linking=st.sidebar.checkbox("Rich linking cost", value=cfg.use_rich_linking),
        preview_max_frames=int(preview_frames),
    )
    st.sidebar.caption(f"Pipeline v{PIPELINE_VERSION}")
    st.sidebar.caption(f"Voxel scale (Z,Y,X): {SCALE[0]}, {SCALE[1]}, {SCALE[2]} µm")
    return cfg, mode, int(preview_frames)

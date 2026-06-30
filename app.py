"""
Biohub Cell Lineage Tracker — interactive analysis application.

Run: streamlit run app.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from app.ui import init_session, load_volumes_from_source, run_pipeline, sidebar_settings  # noqa: E402
from biohub.config import PIPELINE_VERSION, SCALE  # noqa: E402
from biohub.export import division_events, to_graph_json, to_lineage_csv  # noqa: E402
from biohub.visualization import (  # noqa: E402
    plot_frame_counts,
    plot_intensity_histogram,
    plot_lineage_graph,
    plot_slice_overlay,
    plot_volume_slices,
)

st.set_page_config(
    page_title="Biohub Cell Lineage Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; max-width: 1200px;}
    h1 {font-weight: 600; letter-spacing: -0.02em;}
  .caption {color: #4b5563;}
    </style>
    """,
    unsafe_allow_html=True,
)

init_session()


def home_tab() -> None:
    st.title("Biohub Cell Lineage Tracker")
    st.markdown(
        """
        Interactive analysis for **3D time-lapse fluorescence microscopy**.

        Load a volume, run centroid detection and temporal linking, inspect lineage structure,
        and export results for downstream study.
        """
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Pipeline", f"v{PIPELINE_VERSION}")
    col2.metric("Voxel scale Z", f"{SCALE[0]} µm")
    col3.metric("Link gate", "7 µm match / configurable track")
    st.markdown(
        """
        **Workflow**
        1. Choose a data source in the sidebar.
        2. Open **Volume** to inspect raw data.
        3. Run analysis from **Pipeline**.
        4. Review tracks and divisions in **Lineage** and **Exports**.
        """
    )


def data_tab(uploaded) -> None:
    st.subheader("Dataset summary")
    source = st.session_state.get("volume_source", "sample")
    try:
        vol4d, name = load_volumes_from_source(
            source,
            uploaded,
            st.session_state.get("zarr_path", ""),
            int(st.session_state.get("preview_frames", cfg.preview_max_frames)),
        )
        st.session_state.volume_4d = vol4d
        st.session_state.dataset_name = name
        t, z, y, x = vol4d.shape
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Frames (T)", t)
        c2.metric("Z slices", z)
        c3.metric("Y size", y)
        c4.metric("X size", x)
        st.caption(f"dtype: {vol4d.dtype} | min={vol4d.min()} max={vol4d.max()} mean={vol4d.mean():.1f}")
        st.dataframe(
            pd.DataFrame(
                {
                    "axis": ["T", "Z", "Y", "X"],
                    "size": [t, z, y, x],
                    "spacing_um": [None, SCALE[0], SCALE[1], SCALE[2]],
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    except Exception as exc:
        st.error(f"Could not load data: {exc}")


def volume_tab() -> None:
    st.subheader("Volume viewer")
    vol4d = st.session_state.volume_4d
    if vol4d is None:
        st.info("Load a dataset from the sidebar.")
        return
    t_max, z_max = vol4d.shape[0] - 1, vol4d.shape[1] - 1
    c1, c2 = st.columns(2)
    t_idx = c1.slider("Time index", 0, t_max, 0)
    z_idx = c2.slider("Z slice", 0, z_max, z_max // 2)
    vol = vol4d[t_idx]
    fig_hist = plot_intensity_histogram(vol, title=f"Intensity histogram, t={t_idx}")
    st.pyplot(fig_hist, clear_figure=True)
    fig = plot_volume_slices(vol, title=f"{st.session_state.dataset_name} | t={t_idx}", z_idx=z_idx)
    st.pyplot(fig, clear_figure=True)


def pipeline_tab(cfg) -> None:
    st.subheader("Analysis pipeline")
    vol4d = st.session_state.volume_4d
    if vol4d is None:
        st.info("Load a dataset first.")
        return
    if st.button("Run detection and tracking", type="primary"):
        with st.spinner("Processing frames..."):
            try:
                result = run_pipeline(
                    vol4d,
                    cfg,
                    st.session_state.dataset_name,
                    int(st.session_state.get("preview_frames", cfg.preview_max_frames)),
                )
                st.session_state.result = result
                st.success(
                    f"Done: {result.n_nodes} nodes, {result.n_edges} edges, {result.n_divisions} divisions."
                )
            except Exception as exc:
                st.error(f"Pipeline failed: {exc}")
    result = st.session_state.result
    if result is None:
        return
    st.markdown("**Summary**")
    st.json(result.stats)
    counts = [len(f.coords) for f in result.frames]
    fig_counts = plot_frame_counts(counts, title="Detections per frame")
    st.pyplot(fig_counts, clear_figure=True)


def detection_tab() -> None:
    st.subheader("Detection overlay")
    result = st.session_state.result
    vol4d = st.session_state.volume_4d
    if result is None or vol4d is None:
        st.info("Run the pipeline first.")
        return
    t_idx = st.slider("Frame", 0, len(result.frames) - 1, 0, key="det_t")
    z_idx = st.slider("Z slice", 0, vol4d.shape[1] - 1, vol4d.shape[1] // 2, key="det_z")
    frame = result.frames[t_idx]
    div_parents = set(division_events(result)["source_id"].astype(int)) if result.n_divisions else set()
    div_coords = []
    if div_parents and not result.nodes.empty:
        sub = result.nodes[result.nodes["node_id"].isin(div_parents) & (result.nodes["t"] == t_idx)]
        if len(sub):
            div_coords = sub[["z", "y", "x"]].to_numpy()
    highlight = np.array(div_coords) if div_coords else None
    fig = plot_slice_overlay(
        vol4d[t_idx],
        z_idx,
        frame.coords,
        title=f"Detections at t={t_idx}",
        highlight_divisions=highlight,
    )
    st.pyplot(fig, clear_figure=True)
    st.caption(f"{len(frame.coords)} detections in this frame.")


def lineage_tab() -> None:
    st.subheader("Lineage graph")
    result = st.session_state.result
    if result is None:
        st.info("Run the pipeline first.")
        return
    fig = plot_lineage_graph(result)
    st.pyplot(fig, clear_figure=True)
    divs = division_events(result)
    st.markdown("**Division events**")
    if divs.empty:
        st.write("No division events detected.")
    else:
        st.dataframe(divs, use_container_width=True, hide_index=True)


def exports_tab(cfg) -> None:
    st.subheader("Exports")
    result = st.session_state.result
    if result is None:
        st.info("Run the pipeline first.")
        return
    csv_df = to_lineage_csv(result)
    graph = to_graph_json(result)
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{result.dataset_name}_lineage.csv"
    json_path = out_dir / f"{result.dataset_name}_graph.json"
    csv_df.to_csv(csv_path)
    json_path.write_text(json.dumps(graph, indent=2))
    st.download_button(
        "Download lineage CSV",
        data=csv_df.to_csv().encode(),
        file_name=csv_path.name,
        mime="text/csv",
    )
    st.download_button(
        "Download graph JSON",
        data=json.dumps(graph, indent=2).encode(),
        file_name=json_path.name,
        mime="application/json",
    )
    st.caption(f"Saved to `{csv_path}` and `{json_path}`.")


# Sidebar
with st.sidebar:
    st.header("Data source")
    source = st.radio(
        "Input",
        ["sample", "upload_npy", "zarr"],
        format_func=lambda x: {"sample": "Bundled sample", "upload_npy": "Upload .npy", "zarr": "Local .zarr path"}[x],
    )
    st.session_state.volume_source = source
    uploaded = None
    if source == "upload_npy":
        uploaded = st.file_uploader("Volume array (T,Z,Y,X)", type=["npy"])
    if source == "zarr":
        st.session_state.zarr_path = st.text_input("Path to .zarr directory", value="data/sample/example.zarr")

    cfg, _mode, preview_frames = sidebar_settings(st.session_state.cfg)
    st.session_state.cfg = cfg
    st.session_state.preview_frames = preview_frames

tabs = st.tabs(["Home", "Dataset", "Volume", "Pipeline", "Detection", "Lineage", "Exports"])
with tabs[0]:
    home_tab()
with tabs[1]:
    data_tab(uploaded)
with tabs[2]:
    volume_tab()
with tabs[3]:
    pipeline_tab(cfg)
with tabs[4]:
    detection_tab()
with tabs[5]:
    lineage_tab()
with tabs[6]:
    exports_tab(cfg)

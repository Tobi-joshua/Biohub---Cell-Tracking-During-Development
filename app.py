"""
Biohub Cell Lineage Tracker — interactive analysis application.

Run: streamlit run app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from app.ui import (  # noqa: E402
    init_session,
    render_dataset_sidebar,
    run_pipeline_on_session,
    sidebar_settings,
)
from biohub.config import MATCH_GATE_UM, PIPELINE_VERSION, SCALE  # noqa: E402
from biohub.data import load_geff_graph  # noqa: E402
from biohub.dataset_catalog import DatasetCatalog  # noqa: E402
from biohub.export import division_events, to_graph_json, to_lineage_csv  # noqa: E402
from biohub.visualization import (  # noqa: E402
    build_overlay_gif,
    plot_frame_counts,
    plot_gt_overlay,
    plot_intensity_histogram,
    plot_lineage_graph,
    plot_lineage_timeline,
    plot_slice_overlay,
    plot_temporal_montage,
    plot_track_overlay,
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
    /* Main content spacing */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    h1 { font-weight: 600; letter-spacing: -0.02em; }

    /* Keep tab navigation visible while scrolling main content */
    div[data-testid="stTabs"] > div:first-child {
        position: sticky;
        top: 0;
        z-index: 1000;
        background: var(--background-color, #ffffff);
        border-bottom: 1px solid rgba(49, 51, 63, 0.12);
        padding-top: 0.25rem;
        padding-bottom: 0.35rem;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        font-weight: 500;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
        border-bottom: 2px solid #3366AA;
    }

    /* Prevent sidebar from overlapping main tab bar on narrow viewports */
    section[data-testid="stSidebar"] {
        z-index: 999;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

init_session()


def home_tab() -> None:
    st.title("Biohub Cell Lineage Tracker")
    st.markdown(
        """
        Interactive analysis for **3D time-lapse fluorescence microscopy** and
        **Biohub Cell Tracking** volumes stored locally as Zarr/GEFF datasets.

        Point the sidebar at your downloaded dataset root (the folder containing
        `train/` and `test/`), scan, pick a volume, and run the lineage pipeline.
        """
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Pipeline", f"v{PIPELINE_VERSION}")
    col2.metric("Voxel scale Z", f"{SCALE[0]} µm")
    col3.metric("Match gate", f"{MATCH_GATE_UM} µm")
    st.markdown(
        """
        **Workflow**
        1. Set **Dataset root directory** in the sidebar and click **Scan dataset**.
        2. Choose a volume from the dropdown and click **Load volume**.
        3. Inspect raw data under **Volume**, then run **Pipeline**.
        4. Review detections, lineage animations, and exports.

        Use **Synthetic demo** only when no local dataset is available.
        """
    )


def data_tab() -> None:
    st.subheader("Dataset summary")
    catalog: DatasetCatalog | None = st.session_state.get("catalog")
    entry = st.session_state.get("selected_entry")
    vol4d = st.session_state.get("volume_4d")

    if catalog is not None:
        st.markdown(f"**Root:** `{catalog.root}`")
        c1, c2, c3 = st.columns(3)
        c1.metric("Train volumes", catalog.n_train)
        c2.metric("Test volumes", catalog.n_test)
        c3.metric("Total", len(catalog.entries))
        rows = []
        for e in catalog.entries:
            rows.append(
                {
                    "split": e.split,
                    "name": e.name,
                    "shape": str(e.shape),
                    "dtype": str(e.dtype),
                    "geff": "yes" if e.has_geff else "no",
                    "est_nodes": e.estimated_nodes,
                    "gt_nodes": e.n_geff_nodes,
                    "gt_edges": e.n_geff_edges,
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if entry is not None:
        st.markdown("**Selected volume**")
        st.json(
            {
                "name": entry.name,
                "split": entry.split,
                "zarr": str(entry.zarr_path),
                "geff": str(entry.geff_path) if entry.geff_path else None,
                "shape": entry.shape,
                "dtype": str(entry.dtype),
                "estimated_nodes": entry.estimated_nodes,
            }
        )

    if vol4d is None:
        st.info("Scan a local dataset and load a volume from the sidebar.")
        return

    t, z, y, x = vol4d.shape
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Loaded frames (T)", t)
    c2.metric("Z slices", z)
    c3.metric("Y size", y)
    c4.metric("X size", x)
    if entry is not None and t < entry.shape[0]:
        st.caption(f"Preview shows {t} of {entry.shape[0]} timepoints. Use **Full sequence** to process all frames.")
    st.caption(f"dtype: {vol4d.dtype} | min={vol4d.min()} max={vol4d.max()} mean={vol4d.mean():.1f}")
    st.dataframe(
        pd.DataFrame(
            {
                "axis": ["T", "Z", "Y", "X"],
                "loaded_size": [t, z, y, x],
                "full_size": [entry.shape[0] if entry else t, z, y, x],
                "spacing_um": [None, SCALE[0], SCALE[1], SCALE[2]],
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def volume_tab() -> None:
    st.subheader("Volume viewer")
    vol4d = st.session_state.volume_4d
    entry = st.session_state.get("selected_entry")
    if vol4d is None:
        st.info("Load a volume from the sidebar.")
        return

    t_max, z_max = vol4d.shape[0] - 1, vol4d.shape[1] - 1
    c1, c2 = st.columns(2)
    t_idx = c1.slider("Time index", 0, t_max, 0, key="vol_t")
    z_idx = c2.slider("Z slice", 0, z_max, z_max // 2, key="vol_z")
    vol = vol4d[t_idx]

    if entry is not None and entry.has_geff:
        gt_nodes, _ = load_geff_graph(entry.geff_path)
        if gt_nodes is not None:
            gt_t = gt_nodes[gt_nodes["t"] == t_idx][["z", "y", "x"]].to_numpy()
            fig_gt = plot_gt_overlay(
                vol,
                gt_t,
                title=f"Ground-truth labels (sparse) | {entry.name} t={t_idx}",
            )
            st.pyplot(fig_gt, clear_figure=True)

    fig_hist = plot_intensity_histogram(vol, title=f"Intensity histogram, t={t_idx}")
    st.pyplot(fig_hist, clear_figure=True)
    fig = plot_volume_slices(vol, title=f"{st.session_state.dataset_name} | t={t_idx}", z_idx=z_idx)
    st.pyplot(fig, clear_figure=True)


def _division_highlight_coords(result, t_idx: int) -> np.ndarray | None:
    """Return division-parent coordinates for frame t_idx, or None."""
    if not result.n_divisions or result.nodes.empty:
        return None
    div_parents = set(division_events(result)["source_id"].astype(int))
    sub = result.nodes[result.nodes["node_id"].isin(div_parents) & (result.nodes["t"] == t_idx)]
    if sub.empty:
        return None
    return sub[["z", "y", "x"]].to_numpy()


def pipeline_tab(cfg) -> None:
    st.subheader("Analysis pipeline")
    if st.session_state.volume_4d is None and st.session_state.get("selected_entry") is None:
        st.info("Load a volume first.")
        return
    if st.button("Run detection and tracking", type="primary"):
        with st.spinner("Processing frames…"):
            try:
                result = run_pipeline_on_session(
                    cfg,
                    int(st.session_state.get("preview_frames", cfg.preview_max_frames)),
                )
                st.session_state.result = result
                st.success(
                    f"Done: {result.n_nodes} nodes, {result.n_edges} edges, "
                    f"{result.n_divisions} divisions."
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

    t_max = len(result.frames) - 1
    z_max = vol4d.shape[1] - 1
    c1, c2 = st.columns(2)
    t_idx = c1.slider("Frame", 0, t_max, 0, key="det_t")
    z_idx = c2.slider("Z slice", 0, z_max, z_max // 2, key="det_z")
    frame = result.frames[t_idx]
    highlight = _division_highlight_coords(result, t_idx)

    col_a, col_b = st.columns(2)
    with col_a:
        fig = plot_slice_overlay(
            vol4d[t_idx],
            z_idx,
            frame.coords,
            title=f"Detections at t={t_idx}",
            highlight_divisions=highlight,
        )
        st.pyplot(fig, clear_figure=True)
        st.caption(f"{len(frame.coords)} detections in this frame.")

    with col_b:
        if t_idx < t_max:
            next_frame = result.frames[t_idx + 1]
            curr_ids = set(frame.node_ids)
            next_ids = set(next_frame.node_ids)
            links = [
                (int(row.source_id), int(row.target_id))
                for row in result.edges.itertuples(index=False)
                if int(row.source_id) in curr_ids and int(row.target_id) in next_ids
            ]
            fig_links = plot_track_overlay(
                vol4d[t_idx],
                frame.coords,
                next_frame.coords,
                links,
                z_idx,
                vol_b=vol4d[t_idx + 1],
                title=f"Links t={t_idx} → t={t_idx + 1}",
            )
            st.pyplot(fig_links, clear_figure=True)
        else:
            st.info("Select an earlier frame to view inter-frame links.")

    st.markdown("**Temporal montage**")
    fig_montage = plot_temporal_montage(
        vol4d,
        result.frames,
        z_idx,
        title=f"Detection montage (z={z_idx})",
    )
    st.pyplot(fig_montage, clear_figure=True)

    st.markdown("**Time-lapse animation**")
    fps = st.slider("GIF frame rate (fps)", 2, 12, 4, key="gif_fps")
    if st.button("Generate overlay animation", key="gen_gif"):
        with st.spinner("Rendering GIF…"):
            gif_bytes = build_overlay_gif(vol4d, result.frames, z_idx, fps=fps)
            st.session_state.overlay_gif = gif_bytes
    if st.session_state.get("overlay_gif"):
        st.image(st.session_state.overlay_gif, caption=f"Detection overlay, z={z_idx}")
        st.download_button(
            "Download animation (GIF)",
            data=st.session_state.overlay_gif,
            file_name=f"{st.session_state.dataset_name}_overlay_z{z_idx}.gif",
            mime="image/gif",
        )


def lineage_tab() -> None:
    st.subheader("Lineage graph")
    result = st.session_state.result
    if result is None:
        st.info("Run the pipeline first.")
        return

    col_a, col_b = st.columns(2)
    with col_a:
        fig = plot_lineage_graph(result)
        st.pyplot(fig, clear_figure=True)
    with col_b:
        fig_tl = plot_lineage_timeline(result)
        st.pyplot(fig_tl, clear_figure=True)

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


# Main layout: tabs first in the content area, sidebar configured below.
tabs = st.tabs(["Home", "Dataset", "Volume", "Pipeline", "Detection", "Lineage", "Exports"])

with st.sidebar:
    render_dataset_sidebar()
    cfg, _mode, preview_frames = sidebar_settings(st.session_state.cfg)
    st.session_state.cfg = cfg
    st.session_state.preview_frames = preview_frames

with tabs[0]:
    home_tab()
with tabs[1]:
    data_tab()
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

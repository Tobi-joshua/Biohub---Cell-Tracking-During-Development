# Figures for the paper

## Auto-generated (run from repo root)

```bash
python scripts/generate_figures.py
```

| File | Description |
|------|-------------|
| `pipeline_overview.png` | Processing pipeline schematic |
| `sample_volume.png` | XY / ZY / ZX volume views with detections |
| `detection_overlay.png` | Single-slice centroid overlay with scale bar |
| `track_links.png` | Inter-frame assignment links on blended slices |
| `temporal_montage.png` | Multi-frame detection strip |
| `frame_counts.png` | Detections per frame |
| `lineage_graph.png` | Lineage topology graph |
| `lineage_timeline.png` | Track trajectories over time |

## Manual Streamlit screenshots

Capture these after `streamlit run app.py`. Save PNG files into `figures/`.

### 1. `ui_home.png` — Application overview

- Load **Synthetic demo** (or a local volume).
- Stay on **Home**.
- Include the top segmented navigation bar (Home | Dataset | Volume | …).
- Crop to the main content area; hide browser chrome if possible.

### 2. `ui_pipeline.png` — Pipeline execution

- Run **Pipeline** → **Run detection and tracking**.
- Screenshot the success message, summary JSON, and frame-count plot.

### 3. `ui_detection.png` — Detection and montage

- Open **Detection**.
- Show the slice overlay, inter-frame link panel, and temporal montage.
- Scroll to include the **Time-lapse animation** section if a GIF was generated.

### 4. `ui_lineage.png` — Lineage views

- Open **Lineage**.
- Capture both the topology graph and track timeline side by side.

### 5. `ui_dataset.png` (optional) — Local dataset browser

- Point the sidebar at a local Biohub dataset root and scan.
- Open **Dataset** and screenshot the catalog table.

## Compile the paper

```bash
python scripts/generate_figures.py
cd paper
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Missing manual screenshots show a placeholder box in the PDF until you add the files.

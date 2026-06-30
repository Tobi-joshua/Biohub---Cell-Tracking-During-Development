# Biohub Cell Lineage Tracker

Interactive pipeline and Streamlit application for **3D time-lapse cell detection, tracking, and lineage reconstruction** in fluorescence microscopy volumes.

**Author:** Tobi-Joshua Samuel

---

## Features

- Local **Zarr / GEFF** dataset browser (train and test splits)
- Detection, Hungarian linking, and division inference (pipeline v1.4)
- Interactive viewers: volume slices, detection overlays, inter-frame links
- Publication-style plots: montage, lineage timeline, scale bars
- GIF time-lapse export for presentations and papers
- CSV / JSON export of lineage graphs
- IEEE-style LaTeX manuscript in `paper/`

---

## Quick start

```bash
git clone https://github.com/Tobi-joshua/Biohub---Cell-Tracking-During-Development.git
cd Biohub---Cell-Tracking-During-Development

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Using the app

### 1. Load data (sidebar)

| Source | When to use |
|--------|-------------|
| **Local Biohub dataset** | Primary workflow — your downloaded train/test data |
| **Synthetic demo** | Offline testing when no dataset is available |
| **Upload .npy** | Custom NumPy volume, shape `(T, Z, Y, X)` |

**Local dataset steps**

1. Set **Dataset root directory** to the folder containing `train/` and/or `test/`.
2. Click **Scan dataset**.
3. Choose a volume and click **Load volume**.

Expected layout:

```
your-dataset-root/
  train/
    <sample_id>.zarr
    <sample_id>.geff      # optional ground-truth graph
  test/
    <sample_id>.zarr
```

The scanner also accepts a split folder (`.../train`) or a flat directory of `.zarr` volumes.

### 2. Configure analysis (sidebar → Analysis settings)

- **Preview** — process the first *N* frames (fast iteration)
- **Full sequence** — process every timepoint in the volume
- Tune detection threshold, link distance, and division gates

### 3. Navigate pages (top bar)

| Page | Purpose |
|------|---------|
| **Home** | Overview and workflow |
| **Dataset** | Catalog summary and loaded volume metadata |
| **Volume** | Raw slice viewer and intensity histogram |
| **Pipeline** | Run detection + tracking; per-frame counts |
| **Detection** | Overlays, montage, inter-frame links, GIF animation |
| **Lineage** | Topology graph and track timeline |
| **Exports** | Download CSV / JSON lineage files |

---

## VS Code setup

1. Open the cloned repo in VS Code.
2. **Python: Select Interpreter** → `.venv`
3. Install deps: `pip install -r requirements.txt`
4. Start the app:
   - **Terminal:** `streamlit run app.py`
   - **F5:** choose **Streamlit: Biohub App** (`.vscode/launch.json`)

`PYTHONPATH=src` is set in `.vscode/settings.json` so `biohub` imports resolve automatically.

---

## Repository layout

```
app.py                          Streamlit entry point
app/ui.py                       Sidebar and session helpers
src/biohub/                     Core pipeline (detection, tracking, export)
src/biohub/dataset_catalog.py   Local dataset discovery
scripts/generate_figures.py     Batch figure generation for the paper
paper/main.tex                  IEEE-style manuscript
paper/references.bib            Bibliography
figures/                        Generated and manual figures
data/sample/                    Synthetic sample (created on first demo run)
outputs/                        Exported graphs from the app
```

---

## Generate paper figures

```bash
python scripts/generate_figures.py
```

Writes to `figures/`:

- `pipeline_overview.png`
- `sample_volume.png`
- `detection_overlay.png`
- `frame_counts.png`
- `lineage_graph.png`
- `lineage_timeline.png`
- `temporal_montage.png`

For the UI figure, capture a screenshot after running the app and save as `figures/ui_screenshot.png`.

---

## Compile the paper

Requires LaTeX with `IEEEtran`.

```bash
python scripts/generate_figures.py
cd paper
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Output: `paper/main.pdf`

---

## Pipeline summary

| Stage | Method |
|-------|--------|
| Detection | Full-Z + XY block-mean, local maxima, dense-cluster pass, centroid refinement |
| Linking | Hungarian assignment with distance, motion, intensity, and neighborhood costs |
| Divisions | Sister-distance and midpoint-gated mitosis inference |
| Export | CSV lineage table and JSON graph |

**Voxel spacing:** Z = 1.625 µm, Y = X = 0.40625 µm  
**Volume format:** `(T, Z, Y, X)` uint16 Zarr, one frame per chunk

See `DATA_NOTES.md` for format details.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: biohub` | Run from repo root; activate `.venv`; `PYTHONPATH` should include `src` |
| `ImportError: plot_gt_overlay` | `git pull` — ensure you are on the latest `main` |
| `blosc2` / `zarr` errors | `pip install -r requirements.txt` inside `.venv` |
| Scan finds 0 volumes | Path must contain `train/` or `test/` with `*.zarr` folders |
| Navigation hidden under toolbar | Update to latest app — uses top segmented-control navigation |
| Blank page / errors in terminal | Check terminal traceback; try a fresh browser tab |

---

## References

Full bibliography in `paper/references.bib`. Key methods:

- van der Walt et al., scikit-image, PeerJ 2014
- Kuhn, The Hungarian Method, Naval Research Logistics 1955
- Tinevez et al., TrackMate, Methods 2017
- Stringer et al., Cellpose, Nature Methods 2021

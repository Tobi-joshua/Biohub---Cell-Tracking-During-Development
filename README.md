# Biohub Cell Lineage Tracker

Open pipeline and interactive application for **3D time-lapse cell detection, tracking, and lineage reconstruction** in fluorescence microscopy volumes.

Author: **Tobi-Joshua Samuel**

## Repository layout

```
app.py                 Streamlit application entry point
app/ui.py              UI helpers
src/biohub/dataset_catalog.py   Local Biohub dataset discovery (train/test, zarr/geff)
src/data/              Data loader re-exports
src/detection/         Detection re-exports
src/tracking/          Tracking re-exports
src/visualization/     Plotting utilities
src/export/            CSV / JSON export
scripts/generate_figures.py   Publication figure batch script
paper/main.tex         IEEE-style manuscript
paper/references.bib   Bibliography
figures/               Generated and manual figures
data/sample/           Bundled synthetic sample (created on first run)
outputs/               Exported graphs from the app
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the Streamlit app

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Local Biohub dataset (primary workflow)

1. Download the **Biohub Cell Tracking** dataset to your machine.
2. In the sidebar, set **Dataset root directory** to the folder that contains `train/` and/or `test/`.
3. Click **Scan dataset** — the app discovers all `.zarr` volumes and paired `.geff` annotations.
4. Select a volume from the dropdown and click **Load volume**.
5. Run the pipeline and export results.

Expected layout:

```
your-dataset-root/
  train/
    <sample_id>.zarr
    <sample_id>.geff
  test/
    <sample_id>.zarr
```

The app also accepts a split directory (`.../train`) or a flat folder of `.zarr` files.

### Other data sources

- **Synthetic demo** — bundled fallback when no local data is available
- **Upload .npy** — NumPy array with shape `(T, Z, Y, X)`

No remote download or API credentials are required.

## Run in VS Code

### 1. Clone and open

```bash
git clone https://github.com/Tobi-joshua/Biohub---Cell-Tracking-During-Development.git
cd Biohub---Cell-Tracking-During-Development
code .
```

### 2. Create the virtual environment

**Terminal → New Terminal** in VS Code:

```bash
python -m venv .venv
```

Activate it:

| OS | Command |
|----|---------|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (cmd) | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

When prompted, select the `.venv` interpreter:  
`Ctrl+Shift+P` → **Python: Select Interpreter** → `.venv`

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the app

**Option A — integrated terminal (simplest)**

```bash
streamlit run app.py
```

VS Code may show a popup to open `http://localhost:8501` in the browser.

**Option B — Run and Debug**

1. Open **Run and Debug** (`Ctrl+Shift+D`)
2. Choose **Streamlit: Biohub App**
3. Press **F5**

### 5. Load your data in the app

1. Sidebar → **Local Biohub dataset**
2. **Dataset root directory** → absolute path to your downloaded folder, e.g.  
   `C:\data\biohub-cell-tracking-during-development` (Windows) or  
   `/home/you/data/biohub-cell-tracking-during-development` (Linux/macOS)
3. **Scan dataset** → pick a volume → **Load volume**
4. **Pipeline** tab → **Run detection and tracking**

If you do not have the dataset yet, use **Synthetic demo** in the sidebar to try the interface.

### Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: biohub` | Run from repo root; ensure `PYTHONPATH=src` or use the `.vscode` settings included in this repo |
| `blosc2` / `zarr` errors | `pip install -r requirements.txt` inside `.venv` |
| Scan finds 0 volumes | Path must contain `train/` or `test/` with `*.zarr` folders |
| App opens but is blank | Check the terminal for errors; try another browser tab |

## Generate figures for the paper

```bash
python scripts/generate_figures.py
```

This writes to `figures/`:
- `pipeline_overview.png`
- `sample_volume.png`
- `detection_overlay.png`
- `frame_counts.png`
- `lineage_graph.png`

### Manual screenshot for the paper

1. Run `streamlit run app.py`
2. Open the **Pipeline** or **Detection** tab after processing
3. Capture a screenshot
4. Save as `figures/ui_screenshot.png`
5. Uncomment the UI figure block in `paper/main.tex`

## Compile the paper (PDF)

Requires a LaTeX distribution with `IEEEtran`.

```bash
python scripts/generate_figures.py
cd paper
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Output: `paper/main.pdf`

## Pipeline overview

| Stage | Method |
|-------|--------|
| Detection | Full-Z + XY block-mean, local maxima, dense-cluster pass, centroid refinement |
| Linking | Hungarian assignment with distance, motion, intensity, and neighborhood costs |
| Divisions | Sister-distance and midpoint-gated mitosis inference |
| Export | CSV lineage table and JSON graph |

## Data format

Volumes: `(T, Z, Y, X)` uint16, Zarr chunks one frame at a time.  
Voxel spacing: Z = 1.625 µm, Y = X = 0.40625 µm.  
Optional GEFF graph annotations for training / validation.

See `DATA_NOTES.md` for format details.

## References

- van der Walt et al., scikit-image, PeerJ 2014  
- Kuhn, The Hungarian Method, Naval Research Logistics 1955  
- Tinevez et al., TrackMate, Methods 2017  
- Stringer et al., Cellpose, Nature Methods 2021  

Full bibliography in `paper/references.bib`.

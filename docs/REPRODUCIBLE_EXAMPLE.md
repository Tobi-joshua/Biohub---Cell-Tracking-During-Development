# Reproducible example (synthetic ground truth)

This walkthrough runs the **Biohub Cell Lineage Tracker** pipeline on deterministic synthetic data with known cell positions. No proprietary dataset download is required.

## Prerequisites

- Python 3.10 or newer
- Git

## Installation

```bash
git clone https://github.com/Tobi-joshua/Biohub---Cell-Tracking-During-Development.git
cd Biohub---Cell-Tracking-During-Development
git checkout joss-preparation   # JOSS preparation branch (optional)

python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pytest              # only needed to run the automated tests
```

## Run the automated tests (synthetic ground truth)

From the repository root:

```bash
PYTHONPATH=src python3 -m pytest tests/ -v
```

### Expected output (abbreviated)

```
tests/test_detection.py::test_detect_cells_recovers_known_centroids PASSED
tests/test_tracking.py::test_pipeline_links_drifting_cells_across_frames PASSED
tests/test_divisions.py::test_pipeline_detects_division_in_three_frame_synthetic_mitosis PASSED
tests/test_export.py::test_lineage_csv_contains_nodes_and_edges PASSED
...
======================== 7 passed in ... ========================
```

The tests build Gaussian-blob volumes at known `(z, y, x)` centroids, run detection and tracking, and assert:

- centroids are recovered within 1 voxel (detection),
- three drifting cells produce nine nodes and six edges over three frames (tracking),
- a one-to-two division produces one parent with two daughters (division inference),
- CSV and JSON exports contain consistent node and edge records.

## Run the pipeline interactively (Streamlit)

```bash
PYTHONPATH=src streamlit run app.py
```

1. Open `http://localhost:8501`.
2. In the sidebar, choose **Synthetic demo** → **Load synthetic demo**.
3. Open **Pipeline** → run with default analysis settings.
4. Open **Exports** → download CSV / JSON lineage files.

### Expected qualitative behavior

- **Pipeline** reports non-zero detected cells per frame and completes without error.
- **Lineage** shows a graph with edges connecting consecutive time points; occasional branch nodes appear when the random synthetic generator simulates division.
- **Exports** provide a merged CSV (`row_type` = `node` or `edge`) and a JSON graph with `nodes`, `edges`, and `stats`.

Synthetic demo data are **stochastic** (see `src/biohub/sample_data.py`); counts vary between runs. Use the pytest suite above for deterministic checks.

## Run the pipeline from Python (deterministic)

```bash
PYTHONPATH=src python3 << 'PY'
from biohub.config import Config
from biohub.analysis import run_tracking_pipeline
from biohub.export import save_lineage_csv, save_graph_json
from pathlib import Path

# Same construction as tests/fixtures/synthetic_ground_truth.py
from tests.fixtures.synthetic_ground_truth import (
    drifting_centers,
    gaussian_blob_frame,
    synthetic_test_config,
)

base = [(8, 24, 24), (8, 24, 40), (12, 40, 24)]
frames = [gaussian_blob_frame((24, 64, 64), drifting_centers(base, t)) for t in range(3)]
cfg = synthetic_test_config()
result = run_tracking_pipeline(frames, cfg, dataset_name="repro-example", max_frames=3)

out = Path("outputs/repro-example")
save_lineage_csv(result, out / "lineage.csv")
save_graph_json(result, out / "graph.json")
print("nodes", result.n_nodes, "edges", result.n_edges, "divisions", result.n_divisions)
PY
```

### Expected printed values

```
nodes 9 edges 6 divisions 0
```

Files written under `outputs/repro-example/`.

## Limitations

| Topic | Limitation |
|-------|------------|
| **Real microscopy** | This example does not include Biohub Zarr/GEFF train or test volumes. Full-dataset workflows require a local dataset root (see [README.md](../README.md) and [DATA_NOTES.md](../DATA_NOTES.md)). |
| **Accuracy** | Synthetic blobs are idealized; performance on anisotropic zebrafish light-sheet data depends on tuning (`Config`, competition presets) and is documented separately in [EXPERIMENTS.md](../EXPERIMENTS.md) for the public competition leaderboard. |
| **Learned detectors** | `LearnedDetector` is a scaffold only; Cellpose/StarDist weights are not bundled. |
| **Streamlit cloud** | The hosted app supports synthetic demo and `.npy` upload; local Zarr browsing requires running the app on your machine with data on disk. |
| **Hardware** | Large `(T, Z, Y, X)` volumes need sufficient RAM; preview mode limits frames in the UI. |

## Compile the JOSS paper draft (optional)

See [`.github/workflows/joss-preparation.yml`](../.github/workflows/joss-preparation.yml) or, locally with Docker:

```bash
docker run --rm \
  --volume "$PWD:/data" \
  --user "$(id -u):$(id -g)" \
  --env JOURNAL=joss \
  openjournals/inara \
  -o pdf paper.md
```

Output: `paper.pdf` next to `paper.md`.

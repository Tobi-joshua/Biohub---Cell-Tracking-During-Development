# Compile the paper with Overleaf

## Quick path (recommended)

On your machine, from the repo root:

```bash
git pull
pip install -r requirements.txt   # optional, for figure generation
python scripts/prepare_overleaf.py
```

This creates **`overleaf.zip`** in the repo root with:

```
main.tex
references.bib
figures/
  pipeline_overview.png
  sample_volume.png
  detection_overlay.png
  ...
README.txt
```

### Upload to Overleaf

1. Go to [https://www.overleaf.com](https://www.overleaf.com) and sign in.
2. **New Project** → **Upload Project**.
3. Choose **`overleaf.zip`** from your repo folder.
4. Open **Menu** (top left) → **Settings**:
   - **Compiler:** pdfLaTeX
   - **Main document:** `main.tex`
5. Click **Recompile**.

Overleaf runs pdfLaTeX + BibTeX automatically. The PDF appears on the right.

---

## Manual upload (without the script)

1. Generate figures locally:
   ```bash
   python scripts/generate_figures.py
   ```
2. On Overleaf, create a **Blank Project**.
3. Upload these files:
   - `paper/main.tex` → rename paths: change every `../figures/` to `figures/`
   - `paper/references.bib`
   - All `figures/*.png` into a folder named `figures/` in the project
4. Set compiler to **pdfLaTeX**, main file **`main.tex`**, then Recompile.

---

## UI screenshots (optional)

These show **placeholder boxes** until you add the PNGs:

| File | Content |
|------|---------|
| `figures/ui_home.png` | Home page + navigation |
| `figures/ui_pipeline.png` | Pipeline tab after run |
| `figures/ui_detection.png` | Detection overlays |
| `figures/ui_lineage.png` | Lineage graph + timeline |

Capture from the live app, then in Overleaf: **Upload** each file into the `figures/` folder and **Recompile**.

Instructions: `figures/SCREENSHOTS.md` in the repo.

---

## If compilation fails

| Error | Fix |
|-------|-----|
| `IEEEtran.cls not found` | Overleaf includes IEEEtran by default; use a blank project or IEEE template |
| `File not found` for a `.png` | Run `prepare_overleaf.py` again or upload missing files to `figures/` |
| Bibliography empty | Recompile twice, or check **Logs** for BibTeX errors |
| `subfig` errors | Overleaf TeX Live includes `subfig`; recompile with pdfLaTeX |

---

## Local compile (alternative)

If you have LaTeX installed:

```bash
python scripts/generate_figures.py
python scripts/prepare_overleaf.py
cd overleaf
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Output: `overleaf/main.pdf`

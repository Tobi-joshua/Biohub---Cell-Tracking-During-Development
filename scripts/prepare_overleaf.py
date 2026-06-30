#!/usr/bin/env python3
"""Create an Overleaf-ready zip: main.tex, references.bib, and figures/."""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
FIGURES = ROOT / "figures"
OUT_DIR = ROOT / "overleaf"
ZIP_PATH = ROOT / "overleaf.zip"


def main() -> None:
    # Regenerate auto figures when the pipeline is importable.
    gen = ROOT / "scripts" / "generate_figures.py"
    if gen.exists():
        subprocess.run([sys.executable, str(gen)], cwd=ROOT, check=False)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    (OUT_DIR / "figures").mkdir()

    tex = (PAPER / "main.tex").read_text()
    tex = tex.replace("../figures/", "figures/")
    (OUT_DIR / "main.tex").write_text(tex)

    shutil.copy(PAPER / "references.bib", OUT_DIR / "references.bib")

    for png in FIGURES.glob("*.png"):
        shutil.copy(png, OUT_DIR / "figures" / png.name)

    readme = """# Overleaf project contents

Upload this folder to Overleaf (or use overleaf.zip from the repo root).

- Main document: main.tex
- Compiler: pdfLaTeX
- Bibliography: BibTeX

Compile order (Overleaf usually does this automatically):
  pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX

Missing ui_*.png files show placeholder boxes until you add screenshots.
See figures/SCREENSHOTS.md in the GitHub repo for capture instructions.
"""
    (OUT_DIR / "README.txt").write_text(readme)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in OUT_DIR.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(OUT_DIR))

    n_fig = len(list((OUT_DIR / "figures").glob("*.png")))
    print(f"Wrote {OUT_DIR}/")
    print(f"  main.tex, references.bib, figures/ ({n_fig} PNG files)")
    print(f"Wrote {ZIP_PATH}")
    print()
    print("Overleaf: New Project → Upload Project → select overleaf.zip")


if __name__ == "__main__":
    main()

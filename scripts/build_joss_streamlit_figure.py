#!/usr/bin/env python3
"""Extract Detection and Lineage Streamlit panels from the IEEE manuscript PDF.

Source: author-supplied IEEE PDF (Fig. 2 panels c and d). Does not generate
synthetic screenshots. Run from repository root:

    python scripts/build_joss_streamlit_figure.py [--pdf PATH]

Default PDF path: paper/main.pdf if present, else requires --pdf.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "figures" / "joss_streamlit_detection_lineage.png"


def trim_whitespace(im: Image.Image, pad: int = 8) -> Image.Image:
    gray = im.convert("L")
    bbox = gray.point(lambda x: 0 if x > 245 else 255).getbbox()
    if not bbox:
        return im
    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(im.width, right + pad)
    bottom = min(im.height, bottom + pad)
    return im.crop((left, top, right, bottom))


def build(pdf_path: Path, out_path: Path) -> None:
    doc = fitz.open(pdf_path)
    page = doc[2]  # PDF page 3: IEEE composite UI figure
    imgs = page.get_images(full=True)
    if len(imgs) < 4:
        raise RuntimeError(f"Expected 4 UI panels on PDF page 3, found {len(imgs)}")
    panels = []
    for idx in (2, 3):  # Detection, Lineage
        xref = imgs[idx][0]
        pix = fitz.Pixmap(doc, xref)
        if pix.n - pix.alpha > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        panels.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))

    panels = [trim_whitespace(p) for p in panels]
    target_h = 720
    scaled = [
        im.resize((int(im.width * target_h / im.height), target_h), Image.Resampling.LANCZOS)
        for im in panels
    ]
    gap = 24
    label_h = 36
    total_w = scaled[0].width + gap + scaled[1].width
    canvas = Image.new("RGB", (total_w, target_h + label_h), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    x = 0
    for i, im in enumerate(scaled):
        canvas.paste(im, (x, label_h))
        draw.text((x + 8, 4), "(a)" if i == 0 else "(b)", fill="black", font=font)
        x += im.width + gap
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, help="IEEE manuscript PDF with embedded UI figure")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    pdf = args.pdf
    if pdf is None:
        candidate = REPO / "paper" / "main.pdf"
        if candidate.is_file():
            pdf = candidate
        else:
            parser.error("Provide --pdf (IEEE manuscript with Fig. 2 UI composite)")
    build(pdf, args.out)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()

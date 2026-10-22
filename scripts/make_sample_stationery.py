"""Generate placeholder fund stationery and a placeholder partner signature.

The public repository ships only synthetic artwork. This script builds
`data/letterheads/fund_1_source.pdf` (the master the letterhead strips are cropped
from) with the same geometry as the real stationery: a black bar on the left,
a logo block, a right-aligned address and a red bar on the right, plus a footer
rule. Replace it with your own stationery PDF for real use.

Usage: python scripts/make_sample_stationery.py
"""
from __future__ import annotations

from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LETTERHEADS = ROOT / "data" / "letterheads"
SIGNATURES = ROOT / "data" / "signatures"

WIDTH, HEIGHT = 585.12, 842.79
BLACK = (0, 0, 0)
RED = (0.8, 0.13, 0.15)
GREY = (0.35, 0.35, 0.35)


def build_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=WIDTH, height=HEIGHT)
    # Left black bar and right red bar across the header band.
    page.draw_rect(fitz.Rect(0, 0, 15, 80), color=None, fill=BLACK)
    page.draw_rect(fitz.Rect(WIDTH - 15, 0, WIDTH, 80), color=None, fill=RED)
    # Logo block: a red disc with a monogram and a wordmark.
    page.draw_circle(fitz.Point(70, 30), 21, color=None, fill=RED)
    page.insert_text(fitz.Point(58, 37), "SF", fontsize=18, fontname="hebo", color=(1, 1, 1))
    page.insert_text(fitz.Point(30, 66), "SAMPLE FUND", fontsize=13, fontname="tiro", color=BLACK)
    page.insert_text(fitz.Point(36, 76), "PLACEHOLDER STATIONERY", fontsize=6, fontname="helv", color=GREY)
    # Right-aligned address block (sits inside the area the app rewrites per fund).
    lines = ["Sample Angel Fund", "Placeholder address line 1", "Placeholder address line 2", "City - 000000"]
    y = 18
    for i, line in enumerate(lines):
        font = "tibo" if i == 0 else "tiro"
        w = fitz.get_text_length(line, fontname=font, fontsize=10.5)
        page.insert_text(fitz.Point(550 - w, y), line, fontsize=10.5, fontname=font, color=BLACK)
        y += 12.5
    # Footer rule and line.
    page.draw_rect(fitz.Rect(10, HEIGHT - 22, WIDTH - 10, HEIGHT - 20), color=None, fill=RED)
    footer = "Sample corporate office address - placeholder stationery for demonstration only"
    w = fitz.get_text_length(footer, fontname="tiro", fontsize=7)
    page.insert_text(fitz.Point((WIDTH - w) / 2, HEIGHT - 10), footer, fontsize=7, fontname="tiro", color=BLACK)
    doc.save(path, deflate=True, garbage=4)
    doc.close()


def placeholder_signature(path: Path, label: str) -> None:
    image = Image.new("RGBA", (400, 120), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, 399, 119], outline=(26, 115, 232, 255), width=2)
    font = ImageFont.load_default()
    draw.text((20, 40), label, fill=(26, 115, 232, 255), font=font)
    draw.text((20, 75), "(Replace with actual signature PNG)", fill=(120, 120, 120, 255), font=font)
    image.save(path, format="PNG")


def main() -> None:
    LETTERHEADS.mkdir(parents=True, exist_ok=True)
    build_pdf(LETTERHEADS / "fund_1_source.pdf")
    # Derived strips and logo are regenerated from the new master.
    for png in LETTERHEADS.glob("*.png"):
        png.unlink()
    import sys

    sys.path.insert(0, str(ROOT))
    from app.services.letterhead import ensure_letterhead_assets

    ensure_letterhead_assets()
    placeholder_signature(SIGNATURES / "girish_shivani.png", "Girish Shivani")
    print("Placeholder stationery and signature written.")


if __name__ == "__main__":
    main()

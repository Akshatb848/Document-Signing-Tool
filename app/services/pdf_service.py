"""PDF rendering, coordinate mapping, and signature overlay."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image

from app.config import PDF_RENDER_SCALE


@dataclass(frozen=True)
class PageRender:
    page_number: int
    image: Image.Image
    pdf_width: float
    pdf_height: float
    image_width: int
    image_height: int


@dataclass(frozen=True)
class PlacementRect:
    page_number: int
    x0: float
    y0: float
    x1: float
    y1: float

    def as_dict(self) -> dict[str, float | int]:
        return {
            "page_number": self.page_number,
            "x0": round(self.x0, 2),
            "y0": round(self.y0, 2),
            "x1": round(self.x1, 2),
            "y1": round(self.y1, 2),
        }

    def format_position(self) -> str:
        return (
            f"x0={self.x0:.1f}, y0={self.y0:.1f}, "
            f"x1={self.x1:.1f}, y1={self.y1:.1f}"
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def open_pdf(pdf_bytes: bytes) -> fitz.Document:
    return fitz.open(stream=pdf_bytes, filetype="pdf")


def page_count(pdf_bytes: bytes) -> int:
    doc = open_pdf(pdf_bytes)
    try:
        return doc.page_count
    finally:
        doc.close()


def render_page(pdf_bytes: bytes, page_number: int, scale: float = PDF_RENDER_SCALE) -> PageRender:
    doc = open_pdf(pdf_bytes)
    try:
        page = doc[page_number - 1]
        rect = page.rect
        matrix = fitz.Matrix(scale, scale)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        return PageRender(
            page_number=page_number,
            image=image,
            pdf_width=rect.width,
            pdf_height=rect.height,
            image_width=pixmap.width,
            image_height=pixmap.height,
        )
    finally:
        doc.close()


def apply_signature(
    pdf_bytes: bytes,
    signature_path: Path,
    placement: PlacementRect,
) -> bytes:
    doc = open_pdf(pdf_bytes)
    try:
        page = doc[placement.page_number - 1]
        rect = fitz.Rect(placement.x0, placement.y0, placement.x1, placement.y1)
        page.insert_image(rect, filename=str(signature_path))
        return doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()


def build_preview_image(
    pdf_bytes: bytes,
    signature_path: Path,
    placement: PlacementRect,
    scale: float = PDF_RENDER_SCALE,
) -> Image.Image:
    signed_bytes = apply_signature(pdf_bytes, signature_path, placement)
    render = render_page(signed_bytes, placement.page_number, scale=scale)
    return render.image


def save_pdf(pdf_bytes: bytes, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf_bytes)


def signature_aspect_ratio(signature_path: Path) -> float:
    with Image.open(signature_path) as image:
        return image.height / image.width

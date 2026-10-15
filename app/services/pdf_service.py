"""PDF rendering, coordinate mapping, and signature overlay."""

from __future__ import annotations

import base64
import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image

from app.config import DISPLAY_MAX_HEIGHT, DISPLAY_MAX_WIDTH, PDF_RENDER_SCALE


class EncryptedPDFError(ValueError):
    """Raised when the uploaded PDF requires a password."""


@dataclass(frozen=True)
class PageRender:
    page_number: int
    image: Image.Image
    pdf_width: float
    pdf_height: float
    image_width: int
    image_height: int
    rotation: int = 0


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
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if doc.needs_pass:
        doc.close()
        raise EncryptedPDFError(
            "This PDF is password-protected. Export an unlocked copy and upload that."
        )
    return doc


def fit_display_size(
    pdf_width: float,
    pdf_height: float,
    max_width: int = DISPLAY_MAX_WIDTH,
    max_height: int = DISPLAY_MAX_HEIGHT,
) -> tuple[int, int]:
    """Largest integer size that fits the viewport while keeping page aspect."""
    if pdf_width <= 0 or pdf_height <= 0:
        return max_width, max_height
    scale = min(max_width / pdf_width, max_height / pdf_height)
    width = max(1, int(round(pdf_width * scale)))
    height = max(1, int(round(pdf_height * scale)))
    return width, height


def image_to_data_url(image: Image.Image, fmt: str = "JPEG") -> str:
    buffer = io.BytesIO()
    if fmt.upper() == "JPEG" and image.mode != "RGB":
        image = image.convert("RGB")
    save_kwargs = {"quality": 85} if fmt.upper() == "JPEG" else {}
    image.save(buffer, format=fmt, **save_kwargs)
    mime = "image/jpeg" if fmt.upper() == "JPEG" else "image/png"
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def png_file_to_data_url(path: Path) -> str:
    with Image.open(path) as image:
        return image_to_data_url(image.convert("RGBA"), fmt="PNG")


def default_display_box(
    display_width: int,
    display_height: int,
    aspect_ratio: float,
    width_frac: float = 0.18,
    index: int = 0,
) -> dict[str, float]:
    aspect = aspect_ratio if aspect_ratio > 0 else 0.3
    width = max(48.0, display_width * width_frac)
    height = width * aspect
    if height > display_height * 0.22:
        height = display_height * 0.22
        width = height / aspect
    x = display_width * 0.12 + (index % 4) * 28
    y = display_height * 0.72 - height / 2 - (index % 4) * 22
    return clamp_display_box(
        x, y, width, height, display_width, display_height, aspect
    )


def clamp_display_box(
    x: float,
    y: float,
    width: float,
    height: float,
    display_width: int,
    display_height: int,
    aspect_ratio: float | None = None,
    bounds: dict[str, float] | None = None,
    mode: str = "stamp",
) -> dict[str, float]:
    """Keep the stamp on the page (or inside bounds, e.g. the letterhead body)."""
    x0 = float(bounds["x0"]) if bounds else 0.0
    y0 = float(bounds["y0"]) if bounds else 0.0
    x1 = float(bounds["x1"]) if bounds else float(display_width)
    y1 = float(bounds["y1"]) if bounds else float(display_height)
    inner_w = max(48.0, x1 - x0)
    inner_h = max(24.0, y1 - y0)
    if mode == "band":
        width = min(max(inner_w * 0.35, width), inner_w)
        if aspect_ratio and aspect_ratio > 0:
            height = width * aspect_ratio
        height = min(max(18.0, height), inner_h * 0.45)
        if aspect_ratio and aspect_ratio > 0:
            width = min(inner_w, height / aspect_ratio)
        x = min(max(x0, x), max(x0, x1 - width))
        y = min(max(y0, y), max(y0, y1 - height))
        return {"x": x, "y": y, "w": width, "h": height}
    max_w = inner_w * 0.85
    min_w = 48.0
    if aspect_ratio and aspect_ratio > 0:
        max_w = min(max_w, (inner_h * 0.55) / aspect_ratio)
        min_w = max(min_w, 18.0 / aspect_ratio)
        width = min(max(min_w, width), max_w)
        height = width * aspect_ratio
    else:
        width = min(max(48.0, width), max_w)
        height = min(max(18.0, height), inner_h * 0.5)
    x = min(max(x0, x), max(x0, x1 - width))
    y = min(max(y0, y), max(y0, y1 - height))
    return {"x": x, "y": y, "w": width, "h": height}


def page_count(pdf_bytes: bytes) -> int:
    doc = open_pdf(pdf_bytes)
    try:
        return doc.page_count
    finally:
        doc.close()


def document_page_sizes(pdf_bytes: bytes) -> list[str]:
    doc = open_pdf(pdf_bytes)
    try:
        return [
            page_size_label(page.rect.width, page.rect.height, page.rotation)
            for page in doc
        ]
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
            rotation=page.rotation,
        )
    finally:
        doc.close()


def render_page_for_display(
    pdf_bytes: bytes,
    page_number: int,
    scale: float = PDF_RENDER_SCALE,
) -> PageRender:
    """Render a page, then shrink it so the full page fits the operator UI."""
    native = render_page(pdf_bytes, page_number, scale=scale)
    width, height = fit_display_size(native.pdf_width, native.pdf_height)
    display = native.image.resize((width, height), Image.Resampling.LANCZOS)
    return PageRender(
        page_number=page_number,
        image=display,
        pdf_width=native.pdf_width,
        pdf_height=native.pdf_height,
        image_width=width,
        image_height=height,
        rotation=native.rotation,
    )


def apply_signature(
    pdf_bytes: bytes,
    signature_path: Path,
    placement: PlacementRect,
) -> bytes:
    return apply_signatures(pdf_bytes, [(signature_path, placement)])


def capture_page_geometry(page: fitz.Page) -> dict:
    return {
        "mediabox": fitz.Rect(page.mediabox),
        "cropbox": fitz.Rect(page.cropbox),
        "rotation": page.rotation,
        "width": page.rect.width,
        "height": page.rect.height,
    }


def restore_page_geometry(page: fitz.Page, geometry: dict) -> None:
    page.set_mediabox(geometry["mediabox"])
    try:
        page.set_cropbox(geometry["cropbox"])
    except ValueError:
        pass
    if page.rotation != geometry["rotation"]:
        page.set_rotation(geometry["rotation"])


def page_size_label(pdf_width: float, pdf_height: float, rotation: int = 0) -> str:
    orientation = "landscape" if pdf_width > pdf_height else "portrait"
    rotate = f", rotated {rotation}°" if rotation else ""
    return f"{pdf_width:.0f} × {pdf_height:.0f} pt ({orientation}{rotate})"


def add_signed_timestamp(page: fitz.Page, timestamp: str) -> None:
    """Write the timestamp in the footer band so it does not cover body text."""
    from app.services.letterhead import content_box

    rect = page.rect
    body = content_box(rect.width, rect.height)
    box = fitz.Rect(rect.x1 - 230, body.y1 + 4, rect.x1 - 10, rect.y1 - 3)
    if box.width < 40 or box.height < 8:
        box = fitz.Rect(rect.x1 - 220, rect.y1 - 16, rect.x1 - 8, rect.y1 - 3)
    page.insert_textbox(
        box,
        timestamp,
        fontsize=7,
        fontname="helv",
        color=(0.35, 0.35, 0.35),
        align=2,
    )


def apply_signatures(
    pdf_bytes: bytes,
    stamps: list[tuple[Path, PlacementRect]],
    timestamp: str | None = None,
) -> bytes:
    """Overlay stamps without changing any page's size, crop, or rotation."""
    if not stamps and not timestamp:
        return pdf_bytes
    doc = open_pdf(pdf_bytes)
    try:
        geometries = [capture_page_geometry(page) for page in doc]
        touched_pages: set[int] = set()
        for signature_path, placement in stamps:
            page = doc[placement.page_number - 1]
            rect = fitz.Rect(placement.x0, placement.y0, placement.x1, placement.y1)
            page.insert_image(
                rect,
                filename=str(signature_path),
                keep_proportion=True,
                overlay=True,
            )
            touched_pages.add(placement.page_number - 1)
        if timestamp:
            for index in sorted(touched_pages) or range(doc.page_count):
                add_signed_timestamp(doc[index], timestamp)
        for page, geometry in zip(doc, geometries):
            restore_page_geometry(page, geometry)
        return doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()


def page_text_rects(pdf_bytes: bytes, page_number: int) -> list[fitz.Rect]:
    """Word boxes on a page. Empty / whitespace tokens are ignored."""
    doc = open_pdf(pdf_bytes)
    try:
        page = doc[page_number - 1]
        rects: list[fitz.Rect] = []
        for word in page.get_text("words"):
            text = str(word[4]).strip()
            if not text:
                continue
            rects.append(fitz.Rect(word[0], word[1], word[2], word[3]))
        return rects
    finally:
        doc.close()


def overlapping_reserved(
    placement: PlacementRect,
    page_width: float,
    page_height: float,
    min_area: float = 6.0,
) -> list:
    from app.services.letterhead import reserved_rects

    stamp = fitz.Rect(placement.x0, placement.y0, placement.x1, placement.y1)
    hits = []
    for rect in reserved_rects(page_width, page_height):
        inter = stamp & rect
        if not inter.is_empty and abs(inter) >= min_area:
            hits.append(rect)
    return hits


def overlapping_text(
    placement: PlacementRect,
    text_rects: list[fitz.Rect],
    min_area: float = 6.0,
) -> list[fitz.Rect]:
    """Return text boxes that actually intersect the stamp (not just touch)."""
    stamp = fitz.Rect(placement.x0, placement.y0, placement.x1, placement.y1)
    hits = []
    for rect in text_rects:
        inter = stamp & rect
        if inter.is_empty:
            continue
        if abs(inter) >= min_area:
            hits.append(rect)
    return hits


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


def looks_like_placeholder_signature(signature_path: Path) -> bool:
    """True for the 400x120 PNGs created by run.py when no real image exists."""
    try:
        with Image.open(signature_path) as image:
            return image.size == (400, 120)
    except OSError:
        return False


def signature_aspect_ratio(signature_path: Path) -> float:
    with Image.open(signature_path) as image:
        return image.height / image.width


def display_box_to_placement(
    box: dict[str, float],
    page_number: int,
    render: PageRender,
) -> PlacementRect:
    """Map a top-left display-pixel box onto PyMuPDF page points (also top-left)."""
    scale_x = render.pdf_width / render.image_width
    scale_y = render.pdf_height / render.image_height
    left = float(box["x"])
    top = float(box["y"])
    width = float(box["w"])
    height = float(box["h"])

    x0 = left * scale_x
    x1 = (left + width) * scale_x
    y0 = top * scale_y
    y1 = (top + height) * scale_y

    x0 = max(0.0, min(x0, render.pdf_width))
    x1 = max(0.0, min(x1, render.pdf_width))
    y0 = max(0.0, min(y0, render.pdf_height))
    y1 = max(0.0, min(y1, render.pdf_height))
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    return PlacementRect(page_number=page_number, x0=x0, y0=y0, x1=x1, y1=y1)


def click_to_placement(
    click_x: float,
    click_y: float,
    page_number: int,
    render: PageRender,
    width_pct: float,
    aspect_ratio: float,
) -> PlacementRect:
    """Map an image-pixel click (top-left origin) to a PDF-point placement rect.

    The click marks the *center* of the signature box; box size is derived
    from width_pct (of page width) and the signature's aspect ratio.
    """
    scale_x = render.pdf_width / render.image_width
    scale_y = render.pdf_height / render.image_height

    center_x = click_x * scale_x
    center_y = click_y * scale_y

    width_pts = render.pdf_width * width_pct / 100
    height_pts = width_pts * aspect_ratio

    x0 = center_x - width_pts / 2
    x1 = center_x + width_pts / 2
    y0 = center_y - height_pts / 2
    y1 = center_y + height_pts / 2

    if x0 < 0:
        x1 -= x0
        x0 = 0
    if x1 > render.pdf_width:
        x0 -= x1 - render.pdf_width
        x1 = render.pdf_width
    if y0 < 0:
        y1 -= y0
        y0 = 0
    if y1 > render.pdf_height:
        y0 -= y1 - render.pdf_height
        y1 = render.pdf_height

    x0 = max(0, x0)
    y0 = max(0, y0)

    return PlacementRect(page_number=page_number, x0=x0, y0=y0, x1=x1, y1=y1)

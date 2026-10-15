import hashlib
import io

import fitz
import pytest
from PIL import Image

from app.services.pdf_service import (
    EncryptedPDFError,
    apply_signature,
    apply_signatures,
    clamp_display_box,
    click_to_placement,
    display_box_to_placement,
    fit_display_size,
    open_pdf,
    overlapping_text,
    page_count,
    page_text_rects,
    render_page,
    render_page_for_display,
    sha256_bytes,
    signature_aspect_ratio,
)


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    doc = fitz.open()
    doc.new_page(width=595, height=842)  # A4 portrait, in points
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def sample_signature_path(tmp_path):
    path = tmp_path / "sig.png"
    Image.new("RGBA", (400, 100), (0, 0, 0, 0)).save(path)
    return path


def test_sha256_bytes_matches_hashlib():
    data = b"hello world"
    assert sha256_bytes(data) == hashlib.sha256(data).hexdigest()


def test_page_count(sample_pdf_bytes):
    assert page_count(sample_pdf_bytes) == 1


def test_signature_aspect_ratio(sample_signature_path):
    # 400x100 -> height/width = 0.25
    assert signature_aspect_ratio(sample_signature_path) == pytest.approx(0.25)


def test_click_to_placement_centers_on_click(sample_pdf_bytes):
    render = render_page(sample_pdf_bytes, 1)
    # Click at the exact center of the rendered image.
    cx, cy = render.image_width / 2, render.image_height / 2
    placement = click_to_placement(cx, cy, 1, render, width_pct=20, aspect_ratio=0.25)

    width_pts = render.pdf_width * 0.20
    height_pts = width_pts * 0.25
    expected_center_x = render.pdf_width / 2
    expected_center_y = render.pdf_height / 2

    assert placement.x0 == pytest.approx(expected_center_x - width_pts / 2, abs=0.5)
    assert placement.x1 == pytest.approx(expected_center_x + width_pts / 2, abs=0.5)
    assert placement.y0 == pytest.approx(expected_center_y - height_pts / 2, abs=0.5)
    assert placement.y1 == pytest.approx(expected_center_y + height_pts / 2, abs=0.5)


def test_click_to_placement_clamps_to_page_bounds(sample_pdf_bytes):
    render = render_page(sample_pdf_bytes, 1)
    # Click right at the top-left corner — box would go negative without clamping.
    placement = click_to_placement(0, 0, 1, render, width_pct=20, aspect_ratio=0.25)

    assert placement.x0 >= 0
    assert placement.y0 >= 0
    assert placement.x1 <= render.pdf_width
    assert placement.y1 <= render.pdf_height


def test_click_to_placement_clamps_at_bottom_right(sample_pdf_bytes):
    render = render_page(sample_pdf_bytes, 1)
    placement = click_to_placement(
        render.image_width, render.image_height, 1, render, width_pct=20, aspect_ratio=0.25
    )

    assert placement.x0 >= 0
    assert placement.y0 >= 0
    assert placement.x1 <= render.pdf_width
    assert placement.y1 <= render.pdf_height


def test_fit_display_size_keeps_full_a4_page_in_viewport():
    width, height = fit_display_size(595, 842)
    assert width <= 760
    assert height <= 860
    assert width / height == pytest.approx(595 / 842, rel=0.01)


def test_display_box_to_placement_maps_top_left_origin(sample_pdf_bytes):
    render = render_page_for_display(sample_pdf_bytes, 1)
    box = {"x": 0.0, "y": 0.0, "w": render.image_width / 5, "h": render.image_height / 10}
    placement = display_box_to_placement(box, 1, render)
    assert placement.x0 == pytest.approx(0.0, abs=0.6)
    assert placement.y0 == pytest.approx(0.0, abs=0.6)
    assert placement.x1 > placement.x0
    assert placement.y1 > placement.y0
    assert placement.y1 < render.pdf_height / 2


def test_applied_signature_stays_where_the_display_box_was(
    sample_pdf_bytes, sample_signature_path
):
    """Regression: confirm/download must not flip the stamp relative to the pad."""
    render = render_page_for_display(sample_pdf_bytes, 1)
    box = {
        "x": render.image_width * 0.55,
        "y": render.image_height * 0.62,
        "w": render.image_width * 0.22,
        "h": render.image_width * 0.22 * 0.25,
    }
    placement = display_box_to_placement(box, 1, render)
    signed = apply_signature(sample_pdf_bytes, sample_signature_path, placement)
    doc = fitz.open(stream=signed, filetype="pdf")
    try:
        xref = doc[0].get_images()[0][0]
        rect = doc[0].get_image_rects(xref)[0]
    finally:
        doc.close()

    assert rect.x0 == pytest.approx(placement.x0, abs=2.5)
    assert rect.y0 == pytest.approx(placement.y0, abs=2.5)
    assert rect.x1 == pytest.approx(placement.x1, abs=2.5)
    assert rect.y1 == pytest.approx(placement.y1, abs=2.5)


def test_clamp_display_box_keeps_signature_aspect():
    box = clamp_display_box(10, 10, 200, 999, 760, 860, aspect_ratio=0.25)
    assert box["h"] == pytest.approx(box["w"] * 0.25, abs=0.01)


def test_stamp_on_text_is_detected(sample_signature_path):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 120), "This heading must not be covered", fontsize=14)
    pdf_bytes = doc.tobytes()
    doc.close()
    render = render_page_for_display(pdf_bytes, 1)
    # Box covering the heading near the top of the page.
    box = {"x": 70, "y": 80, "w": 300, "h": 80}
    placement = display_box_to_placement(box, 1, render)
    hits = overlapping_text(placement, page_text_rects(pdf_bytes, 1))
    assert hits


def test_stamp_on_blank_area_is_clear(sample_signature_path):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 120), "Heading only at the top", fontsize=14)
    pdf_bytes = doc.tobytes()
    doc.close()
    render = render_page_for_display(pdf_bytes, 1)
    box = {
        "x": render.image_width * 0.15,
        "y": render.image_height * 0.75,
        "w": render.image_width * 0.2,
        "h": render.image_width * 0.2 * 0.25,
    }
    placement = display_box_to_placement(box, 1, render)
    hits = overlapping_text(placement, page_text_rects(pdf_bytes, 1))
    assert hits == []


def test_apply_signatures_preserves_non_a4_size_and_writes_timestamp(
    sample_signature_path,
):
    doc = fitz.open()
    page = doc.new_page(width=792, height=612)
    page.insert_text((72, 72), "Letter landscape")
    pdf_bytes = doc.tobytes()
    doc.close()
    from app.services.pdf_service import PlacementRect, capture_page_geometry

    before = fitz.open(stream=pdf_bytes, filetype="pdf")
    geo = capture_page_geometry(before[0])
    before.close()

    signed = apply_signatures(
        pdf_bytes,
        [
            (
                sample_signature_path,
                PlacementRect(page_number=1, x0=500, y0=500, x1=680, y1=560),
            )
        ],
        timestamp="Signed 2026-10-07 11:47 IST",
    )
    after = fitz.open(stream=signed, filetype="pdf")
    try:
        assert after[0].rect.width == pytest.approx(geo["width"], abs=0.5)
        assert after[0].rect.height == pytest.approx(geo["height"], abs=0.5)
        assert after[0].rotation == geo["rotation"]
        text = after[0].get_text()
        assert "Signed 2026-10-07" in text
    finally:
        after.close()


def test_default_a4_conversion_uses_specified_margins():
    from app.services.letterhead import (
        A4_HEIGHT,
        A4_WIDTH,
        MARGIN_BOTTOM_PT,
        MARGIN_TOP_PT,
        content_box,
        convert_to_a4,
    )

    doc = fitz.open()
    page = doc.new_page(width=400, height=400)
    page.insert_text((40, 80), "Body text only")
    pdf_bytes = doc.tobytes()
    doc.close()

    converted = convert_to_a4(pdf_bytes)
    out = fitz.open(stream=converted, filetype="pdf")
    try:
        assert out[0].rect.width == pytest.approx(A4_WIDTH, abs=1)
        assert out[0].rect.height == pytest.approx(A4_HEIGHT, abs=1)
        body = content_box(out[0].rect.width, out[0].rect.height)
        assert body.y0 == pytest.approx(MARGIN_TOP_PT, abs=0.5)
        assert out[0].rect.height - body.y1 == pytest.approx(MARGIN_BOTTOM_PT, abs=0.5)
        assert "Body text only" in out[0].get_text()
    finally:
        out.close()


def test_word_page_setup_and_letterhead_keep_size():
    from app.services.letterhead import apply_letterhead, convert_to_page_setup

    doc = fitz.open()
    page = doc.new_page(width=400, height=400)
    page.insert_text((40, 80), "Body text only")
    pdf_bytes = doc.tobytes()
    doc.close()

    converted = convert_to_page_setup(pdf_bytes, "Letter Landscape")
    out = fitz.open(stream=converted, filetype="pdf")
    try:
        assert out[0].rect.width == pytest.approx(792, abs=1)
        assert out[0].rect.height == pytest.approx(612, abs=1)
    finally:
        out.close()

    headed = apply_letterhead(converted, "Fund 1")
    headed_doc = fitz.open(stream=headed, filetype="pdf")
    try:
        assert headed_doc[0].rect.width == pytest.approx(792, abs=1)
        assert headed_doc[0].rect.height == pytest.approx(612, abs=1)
        assert "Body text only" in headed_doc[0].get_text()
        assert len(headed_doc[0].get_images()) >= 2
    finally:
        headed_doc.close()


def test_fund_three_letterhead_matches_stationery():
    from app.services.letterhead import (
        apply_letterhead,
        convert_to_a4,
        letterhead_footer_path,
        letterhead_header_path,
        render_letterhead_strips,
    )

    doc = fitz.open()
    doc.new_page(width=400, height=400)
    pdf_bytes = convert_to_a4(doc.tobytes())
    doc.close()
    headed = apply_letterhead(pdf_bytes, "Fund 3")
    out = fitz.open(stream=headed, filetype="pdf")
    try:
        assert len(out[0].get_images()) >= 2
    finally:
        out.close()
    header, footer = render_letterhead_strips("Fund 3")
    fund1_header, _fund1_footer = render_letterhead_strips("Fund 1")
    assert header == letterhead_header_path("Fund 3")
    assert footer == letterhead_footer_path("Fund 3")
    assert header.exists() and footer.exists()
    assert header.read_bytes() != fund1_header.read_bytes()


def _sample_docx_bytes(text: str = "Partnership addendum for testing") -> bytes:
    from docx import Document

    buffer = io.BytesIO()
    word = Document()
    word.add_paragraph(text)
    word.save(buffer)
    return buffer.getvalue()


def test_docx_ingest_becomes_a4():
    from app.services.letterhead import A4_HEIGHT, A4_WIDTH, ingest_upload

    pdf_bytes = ingest_upload("note.docx", _sample_docx_bytes())
    out = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        assert out[0].rect.width == pytest.approx(A4_WIDTH, abs=1)
        assert out[0].rect.height == pytest.approx(A4_HEIGHT, abs=1)
        assert "Partnership addendum" in out[0].get_text()
    finally:
        out.close()


def test_pdf_and_docx_both_take_letterhead():
    from app.services.letterhead import (
        A4_HEIGHT,
        A4_WIDTH,
        apply_letterhead,
        ingest_upload,
    )

    pdf_source = fitz.open()
    page = pdf_source.new_page(width=400, height=400)
    page.insert_text((40, 80), "PDF BODY LINE")
    pdf_in = pdf_source.tobytes()
    pdf_source.close()

    pdf_a4 = ingest_upload("memo.pdf", pdf_in)
    docx_a4 = ingest_upload("memo.docx", _sample_docx_bytes("DOCX BODY LINE"))
    for raw, marker in ((pdf_a4, "PDF BODY LINE"), (docx_a4, "DOCX BODY LINE")):
        headed = apply_letterhead(raw, "Fund 1")
        out = fitz.open(stream=headed, filetype="pdf")
        try:
            assert out[0].rect.width == pytest.approx(A4_WIDTH, abs=1)
            assert out[0].rect.height == pytest.approx(A4_HEIGHT, abs=1)
            assert marker in out[0].get_text()
            assert len(out[0].get_images()) >= 2
        finally:
            out.close()


def test_docx_fallback_without_word_still_converts(monkeypatch):
    import app.services.letterhead as letterhead

    monkeypatch.setattr(letterhead, "_word_com_to_pdf", lambda data, suffix: None)
    monkeypatch.setattr(letterhead, "_libreoffice_to_pdf", lambda data, suffix: None)
    pdf_bytes = letterhead.ingest_upload("note.docx", _sample_docx_bytes("FALLBACK WORD TEXT"))
    out = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        assert out[0].rect.width == pytest.approx(letterhead.A4_WIDTH, abs=1)
        assert "FALLBACK WORD TEXT" in out[0].get_text()
        headed = letterhead.apply_letterhead(pdf_bytes, "Fund 1")
    finally:
        out.close()
    headed_doc = fitz.open(stream=headed, filetype="pdf")
    try:
        assert "FALLBACK WORD TEXT" in headed_doc[0].get_text()
        assert len(headed_doc[0].get_images()) >= 2
    finally:
        headed_doc.close()


def test_sniff_pdf_magic_even_when_named_docx():
    from app.services.letterhead import ingest_upload

    doc = fitz.open()
    page = doc.new_page(width=400, height=400)
    page.insert_text((40, 80), "NAMED DOCX BUT PDF")
    data = doc.tobytes()
    doc.close()
    pdf_bytes = ingest_upload("wrong.docx", data)
    out = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        assert "NAMED DOCX BUT PDF" in out[0].get_text()
    finally:
        out.close()


def test_apply_signatures_on_two_pages(sample_signature_path):
    doc = fitz.open()
    doc.new_page(width=595, height=842)
    doc.new_page(width=595, height=842)
    pdf_bytes = doc.tobytes()
    doc.close()
    from app.services.pdf_service import PlacementRect

    stamps = [
        (
            sample_signature_path,
            PlacementRect(page_number=1, x0=80, y0=600, x1=220, y1=640),
        ),
        (
            sample_signature_path,
            PlacementRect(page_number=2, x0=80, y0=600, x1=220, y1=640),
        ),
    ]
    signed = apply_signatures(pdf_bytes, stamps)
    out = fitz.open(stream=signed, filetype="pdf")
    try:
        assert len(out[0].get_images()) == 1
        assert len(out[1].get_images()) == 1
    finally:
        out.close()


def test_encrypted_pdf_is_rejected():
    source = fitz.open()
    source.new_page()
    buffer = io.BytesIO()
    source.save(
        buffer,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw="secret",
        owner_pw="owner",
    )
    source.close()
    with pytest.raises(EncryptedPDFError):
        open_pdf(buffer.getvalue())


def test_apply_signature_leaves_original_untouched_and_embeds_image(
    sample_pdf_bytes, sample_signature_path
):
    render = render_page(sample_pdf_bytes, 1)
    placement = click_to_placement(
        render.image_width * 0.2, render.image_height * 0.8, 1, render, width_pct=20, aspect_ratio=0.25
    )

    original_hash = sha256_bytes(sample_pdf_bytes)
    signed_bytes = apply_signature(sample_pdf_bytes, sample_signature_path, placement)

    # Original bytes object must be unmodified.
    assert sha256_bytes(sample_pdf_bytes) == original_hash

    doc = fitz.open(stream=signed_bytes, filetype="pdf")
    try:
        assert len(doc[0].get_images()) == 1
    finally:
        doc.close()

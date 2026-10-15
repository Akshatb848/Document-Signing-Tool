#!/usr/bin/env python3
"""Regenerates the sample PDFs in this directory.

Usage:
    python data/samples/generate.py

Only plain ASCII punctuation is used in the body text — PyMuPDF's base
Helvetica font (fontname="helv") does not reliably render typographic
characters like em-dashes, so avoid them here.
"""

from __future__ import annotations

from pathlib import Path

import fitz

OUT = Path(__file__).resolve().parent


def add_page_header_footer(page: fitz.Page, title: str, page_num: int, total_pages: int) -> None:
    page.insert_text((72, 50), title, fontsize=9, color=(0.4, 0.4, 0.4))
    page.insert_text(
        (72, 780),
        f"Page {page_num} of {total_pages} - Sample document for testing only, not a real agreement",
        fontsize=8,
        color=(0.6, 0.6, 0.6),
    )


def textbox(page: fitz.Page, rect: fitz.Rect, text: str, fontsize: int = 11) -> None:
    page.insert_textbox(rect, text, fontsize=fontsize, fontname="helv")


def signature_block(page: fitz.Page, y: float, label: str) -> None:
    page.insert_text((72, y), f"{label}:", fontsize=11, fontname="hebo")
    page.draw_line((72, y + 40), (300, y + 40), color=(0.6, 0.6, 0.6), width=0.8)
    page.insert_text((72, y + 55), "Signature & Date", fontsize=9, color=(0.5, 0.5, 0.5))


def generate_partnership_addendum() -> None:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    add_page_header_footer(page, "YPEF Sample Partnership Agreement", 1, 1)
    page.insert_text((72, 100), "PARTNERSHIP AGREEMENT ADDENDUM", fontsize=18, fontname="hebo")
    page.insert_text(
        (72, 125),
        "YourNest Process Excellence Framework (YPEF) - Sample Document",
        fontsize=10,
        color=(0.4, 0.4, 0.4),
    )

    body = (
        "This is a sample document generated purely for testing the YPEF Partner "
        "Document Signing Tool end-to-end. It is not a real legal agreement and "
        "carries no legal effect.\n\n"
        "This addendum confirms the mutual understanding between the partners "
        "regarding operational responsibilities for the current fiscal year, "
        "including review cadence, reporting lines, and escalation paths for "
        "significant decisions. Nothing in this sample document should be relied "
        "upon for any business purpose.\n\n"
        "By signing below, the partner acknowledges review of this addendum."
    )
    textbox(page, fitz.Rect(72, 160, 523, 340), body)
    signature_block(page, 420, "Signature")

    doc.save(OUT / "sample_partnership_addendum.pdf")
    doc.close()


def generate_multi_page_agreement() -> None:
    doc = fitz.open()
    sections = [
        (
            "1. PURPOSE",
            (
                "This sample multi-page document exists to test page navigation and "
                "per-page signature placement in the YPEF Partner Document Signing Tool. "
                "It has no legal meaning.\n\n"
                "Use this file to confirm that: the page selector correctly switches "
                "the rendered preview, the click-to-place coordinates are page-specific "
                "(a placement made on page 1 should not leak onto page 2 or 3), and the "
                "final signed PDF only carries the signature image on the chosen page."
            ),
        ),
        (
            "2. OPERATIONAL TERMS",
            (
                "This page intentionally contains different content from page 1 so that "
                "a tester can visually confirm which page received the signature overlay "
                "in the downloaded PDF.\n\n"
                "Sample clause: partners agree to review portfolio decisions on a "
                "quarterly basis and to maintain the audit trail required under the "
                "YPEF signing process for every document signed on their behalf."
            ),
        ),
        (
            "3. SIGNATURE PAGE",
            (
                "This is the signature page. In a real workflow, the operator would "
                "typically select this page and place the partner's signature near "
                "the signature line below.\n\n"
                "This sample document was generated automatically for QA / demo "
                "purposes and should never be treated as a binding record."
            ),
        ),
    ]
    total = len(sections)
    for i, (heading, body) in enumerate(sections, start=1):
        page = doc.new_page(width=595, height=842)
        add_page_header_footer(page, "YPEF Sample Multi-Page Agreement", i, total)
        page.insert_text((72, 100), "SAMPLE MULTI-PAGE PARTNERSHIP DOCUMENT", fontsize=16, fontname="hebo")
        page.insert_text((72, 125), heading, fontsize=12, fontname="hebo", color=(0.2, 0.2, 0.5))
        textbox(page, fitz.Rect(72, 150, 523, 350), body)
        if i == total:
            signature_block(page, 420, "Signature")

    doc.save(OUT / "sample_multi_page_agreement.pdf")
    doc.close()


def generate_tri_partner_resolution() -> None:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    add_page_header_footer(page, "YPEF Sample Tri-Partner Resolution", 1, 1)
    page.insert_text((72, 100), "BOARD RESOLUTION - SAMPLE", fontsize=18, fontname="hebo")
    page.insert_text(
        (72, 125), "Requires signature from all three partners", fontsize=10, color=(0.4, 0.4, 0.4)
    )

    body = (
        "This sample resolution is used to test signing the same uploaded document "
        "multiple times in sequence - once per partner (Sanjay Pande, Girish "
        "Shivani, Sunil K Goyal) - producing three separate signed output files "
        "and three audit log entries that all reference the same original "
        "document hash.\n\n"
        "This is not a real board resolution."
    )
    textbox(page, fitz.Rect(72, 160, 523, 280), body)

    y = 340.0
    for name in ("Sanjay Pande", "Girish Shivani", "Sunil K Goyal"):
        signature_block(page, y, name)
        y += 110

    doc.save(OUT / "sample_tri_partner_resolution.pdf")
    doc.close()


def generate_capital_call_notice() -> None:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    add_page_header_footer(page, "YPEF Sample Capital Call Notice", 1, 1)
    page.insert_text((72, 100), "CAPITAL CALL NOTICE - SAMPLE", fontsize=18, fontname="hebo")
    page.insert_text(
        (72, 125),
        "Place the signature on the right-hand block to test off-center placement",
        fontsize=10,
        color=(0.4, 0.4, 0.4),
    )
    body = (
        "This one-page notice is for testing a signature placed on the right "
        "side of the page, rather than the default lower-left area.\n\n"
        "Sample call amount: INR 1,00,00,000 (illustrative only).\n"
        "Due date: 15 October 2026 (illustrative only).\n\n"
        "This is not a real capital call and creates no payment obligation."
    )
    textbox(page, fitz.Rect(72, 160, 523, 320), body)
    page.insert_text((320, 420), "Authorized signatory:", fontsize=11, fontname="hebo")
    page.draw_line((320, 460), (523, 460), color=(0.6, 0.6, 0.6), width=0.8)
    page.insert_text((320, 475), "Signature & Date (right side)", fontsize=9, color=(0.5, 0.5, 0.5))
    doc.save(OUT / "sample_capital_call_notice.pdf")
    doc.close()


def generate_landscape_cover_note() -> None:
    doc = fitz.open()
    page = doc.new_page(width=842, height=595)
    page.insert_text((72, 40), "YPEF Sample Landscape Cover Note", fontsize=9, color=(0.4, 0.4, 0.4))
    page.insert_text(
        (72, 560),
        "Page 1 of 1 - Sample document for testing only, not a real agreement",
        fontsize=8,
        color=(0.6, 0.6, 0.6),
    )
    page.insert_text((72, 90), "LANDSCAPE COVER NOTE - SAMPLE", fontsize=18, fontname="hebo")
    page.insert_text(
        (72, 115),
        "A4 landscape - use this to confirm placement still maps correctly on a wide page",
        fontsize=10,
        color=(0.4, 0.4, 0.4),
    )
    body = (
        "This file is a single landscape page. Upload it and place a signature "
        "near the line on the lower right. Confirm the overlay sits on the line "
        "in the downloaded PDF and is not stretched or shifted.\n\n"
        "This is not a real cover note."
    )
    textbox(page, fitz.Rect(72, 150, 770, 280), body)
    page.insert_text((520, 380), "Partner signature:", fontsize=11, fontname="hebo")
    page.draw_line((520, 420), (750, 420), color=(0.6, 0.6, 0.6), width=0.8)
    page.insert_text((520, 435), "Signature & Date", fontsize=9, color=(0.5, 0.5, 0.5))
    doc.save(OUT / "sample_landscape_cover_note.pdf")
    doc.close()


def add_page_header_footer_any(
    page: fitz.Page, title: str, page_num: int, total_pages: int
) -> None:
    rect = page.rect
    page.insert_text((72, 40), title, fontsize=9, color=(0.4, 0.4, 0.4))
    page.insert_text(
        (72, rect.y1 - 28),
        f"Page {page_num} of {total_pages} - Sample document for testing only, not a real agreement",
        fontsize=8,
        color=(0.6, 0.6, 0.6),
    )


def generate_pack_document(spec: dict) -> None:
    """Build one multi-page QA PDF from a spec dict."""
    width = spec["width"]
    height = spec["height"]
    pages = spec["pages"]
    title = spec["title"]
    filename = spec["filename"]
    doc = fitz.open()
    for i in range(1, pages + 1):
        page = doc.new_page(width=width, height=height)
        add_page_header_footer_any(page, f"YPEF {title}", i, pages)
        page.insert_text((72, 88), title.upper(), fontsize=16, fontname="hebo")
        page.insert_text(
            (72, 112),
            f"{spec['subtitle']}  |  {width:.0f} x {height:.0f} pt  |  page {i}/{pages}",
            fontsize=10,
            color=(0.35, 0.35, 0.35),
        )
        body = (
            f"This is sample pack document {spec['index']:02d} of 20, generated for "
            "multi-page testing of the YPEF signing tool. It is not a real agreement.\n\n"
            f"{spec['purpose']}\n\n"
            f"Section on this page: {spec['section_names'][i - 1]}. Place stamps only "
            "on blank signature lines, never on this body text."
        )
        textbox(page, fitz.Rect(72, 140, width - 72, min(height - 220, 360)), body)
        if i in spec["sign_pages"]:
            y = height - 180
            signature_block(page, y, spec["sign_label"])
            if spec.get("second_sign"):
                page.insert_text((width - 280, y), spec["second_sign"] + ":", fontsize=11, fontname="hebo")
                page.draw_line((width - 280, y + 40), (width - 72, y + 40), color=(0.6, 0.6, 0.6), width=0.8)
    doc.save(OUT / filename)
    doc.close()


A4_P = (595.28, 841.89)
A4_L = (841.89, 595.28)
LTR_P = (612.0, 792.0)
LTR_L = (792.0, 612.0)
LEGAL_P = (612.0, 1008.0)
A3_P = (841.89, 1190.55)

PACK_SPECS: list[dict] = [
    {
        "index": 1,
        "filename": "sample_pack_01_ic_memo.pdf",
        "title": "Investment Committee Memo",
        "subtitle": "A4 portrait, 4 pages",
        "pages": 4,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [4],
        "sign_label": "IC Chair",
        "purpose": "Sign only the last page. Confirm pages 1-3 stay unsigned.",
        "section_names": ["Background", "Thesis", "Risks", "Decision / signature"],
    },
    {
        "index": 2,
        "filename": "sample_pack_02_shareholders_agreement.pdf",
        "title": "Shareholders Agreement Extract",
        "subtitle": "A4 portrait, 6 pages",
        "pages": 6,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [6],
        "sign_label": "Partner",
        "purpose": "Longer pack to test page selector and convert-to-A4 letterhead.",
        "section_names": ["Parties", "Capital", "Governance", "Transfer", "Exit", "Signature"],
    },
    {
        "index": 3,
        "filename": "sample_pack_03_quarterly_report.pdf",
        "title": "Quarterly Portfolio Report",
        "subtitle": "A4 landscape, 5 pages",
        "pages": 5,
        "width": A4_L[0],
        "height": A4_L[1],
        "sign_pages": [5],
        "sign_label": "Fund stamp + partner",
        "purpose": "Landscape multi-page. Convert to A4 Portrait then apply letterhead.",
        "section_names": ["Cover", "NAV", "Exits", "Pipeline", "Attestation"],
    },
    {
        "index": 4,
        "filename": "sample_pack_04_side_letter.pdf",
        "title": "Investor Side Letter",
        "subtitle": "Letter portrait, 2 pages",
        "pages": 2,
        "width": LTR_P[0],
        "height": LTR_P[1],
        "sign_pages": [2],
        "sign_label": "Authorized signatory",
        "purpose": "US Letter size. Confirm conversion to Word Letter Portrait.",
        "section_names": ["Terms", "Execution"],
    },
    {
        "index": 5,
        "filename": "sample_pack_05_legal_opinion.pdf",
        "title": "Legal Opinion Pack",
        "subtitle": "Legal portrait, 8 pages",
        "pages": 8,
        "width": LEGAL_P[0],
        "height": LEGAL_P[1],
        "sign_pages": [8],
        "sign_label": "Counsel",
        "purpose": "Tall Legal pages. After convert, size must be the chosen Word setup.",
        "section_names": [f"Opinion part {n}" for n in range(1, 8)] + ["Signature"],
    },
    {
        "index": 6,
        "filename": "sample_pack_06_board_minutes.pdf",
        "title": "Board Minutes",
        "subtitle": "A4 portrait, 3 pages, two sign lines on last page",
        "pages": 3,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [3],
        "sign_label": "Director 1",
        "second_sign": "Director 2",
        "purpose": "Place two partner signatures on the last page without overlapping text.",
        "section_names": ["Attendance", "Resolutions", "Sign-off"],
    },
    {
        "index": 7,
        "filename": "sample_pack_07_term_sheet.pdf",
        "title": "Term Sheet",
        "subtitle": "A4 portrait, 2 pages",
        "pages": 2,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [1, 2],
        "sign_label": "Initials / signature",
        "purpose": "Signature line on every page to test multi-stamp on multiple pages.",
        "section_names": ["Commercial terms", "Conditions precedent"],
    },
    {
        "index": 8,
        "filename": "sample_pack_08_kyc_pack.pdf",
        "title": "KYC Information Pack",
        "subtitle": "A4 portrait, 7 pages",
        "pages": 7,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [7],
        "sign_label": "Compliance",
        "purpose": "Many pages, single signature at end. Check page jumps in the UI.",
        "section_names": [f"KYC schedule {n}" for n in range(1, 7)] + ["Declaration"],
    },
    {
        "index": 9,
        "filename": "sample_pack_09_fund_iv_drawdown.pdf",
        "title": "Fund IV Drawdown Notice",
        "subtitle": "A4 portrait, 3 pages + fund stamp",
        "pages": 3,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [3],
        "sign_label": "Partner",
        "purpose": "Use Fund 4 stamp plus a partner signature on page 3.",
        "section_names": ["Call notice", "Bank details", "Acknowledgement"],
    },
    {
        "index": 10,
        "filename": "sample_pack_10_amc_policy.pdf",
        "title": "AMC Policy Note",
        "subtitle": "A4 portrait, 4 pages",
        "pages": 4,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [4],
        "sign_label": "AMC stamp / partner",
        "purpose": "Apply AMC letterhead after Word convert, then stamp the last page.",
        "section_names": ["Scope", "Controls", "Exceptions", "Approval"],
    },
    {
        "index": 11,
        "filename": "sample_pack_11_continuation_consent.pdf",
        "title": "Continuation Fund Consent",
        "subtitle": "Letter portrait, 5 pages",
        "pages": 5,
        "width": LTR_P[0],
        "height": LTR_P[1],
        "sign_pages": [5],
        "sign_label": "LP / partner",
        "purpose": "Continuation Fund letterhead + stamp. Letter size source document.",
        "section_names": ["Background", "Roll-over", "Economics", "Tax", "Consent"],
    },
    {
        "index": 12,
        "filename": "sample_pack_12_valuation_committee.pdf",
        "title": "Valuation Committee Paper",
        "subtitle": "A4 landscape, 4 pages",
        "pages": 4,
        "width": A4_L[0],
        "height": A4_L[1],
        "sign_pages": [4],
        "sign_label": "Committee chair",
        "purpose": "Landscape source, convert to A4 Portrait, confirm tables still fit in body.",
        "section_names": ["Holdings", "Marks", "Sensitivity", "Sign-off"],
    },
    {
        "index": 13,
        "filename": "sample_pack_13_esop_approval.pdf",
        "title": "ESOP Approval Note",
        "subtitle": "A4 portrait, 2 pages, dual last-page lines",
        "pages": 2,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [2],
        "sign_label": "Founder",
        "second_sign": "Investor director",
        "purpose": "Two signatures on page 2 without covering the heading text.",
        "section_names": ["Pool summary", "Approvals"],
    },
    {
        "index": 14,
        "filename": "sample_pack_14_audit_response.pdf",
        "title": "Statutory Audit Response",
        "subtitle": "A4 portrait, 9 pages",
        "pages": 9,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [9],
        "sign_label": "CFO / partner",
        "purpose": "Long document. Confirm convert still finishes and last-page sign works.",
        "section_names": [f"Query {n}" for n in range(1, 9)] + ["Management sign-off"],
    },
    {
        "index": 15,
        "filename": "sample_pack_15_a3_portfolio_map.pdf",
        "title": "A3 Portfolio Map",
        "subtitle": "A3 portrait, 2 pages",
        "pages": 2,
        "width": A3_P[0],
        "height": A3_P[1],
        "sign_pages": [2],
        "sign_label": "Partner",
        "purpose": "Oversize A3 source. Convert down to A4 and check letterhead still aligns.",
        "section_names": ["Map", "Notes and signature"],
    },
    {
        "index": 16,
        "filename": "sample_pack_16_letterhead_stress.pdf",
        "title": "Letterhead Stress Pack",
        "subtitle": "A4 portrait, 3 pages, dense last-page lines",
        "pages": 3,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [1, 2, 3],
        "sign_label": "Initials",
        "purpose": "Stamp/sign every page after letterhead. Nothing should sit on header/footer.",
        "section_names": ["Intro", "Body", "Close"],
    },
    {
        "index": 17,
        "filename": "sample_pack_17_mixed_signatories.pdf",
        "title": "Mixed Signatory Pack",
        "subtitle": "A4 portrait, 4 pages",
        "pages": 4,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [2, 4],
        "sign_label": "Signatory",
        "purpose": "Sign pages 2 and 4 only. Page 3 must remain clean.",
        "section_names": ["Cover", "First execution", "Schedules", "Second execution"],
    },
    {
        "index": 18,
        "filename": "sample_pack_18_fund2_closing.pdf",
        "title": "Fund II Closing Binder Extract",
        "subtitle": "Letter landscape, 6 pages",
        "pages": 6,
        "width": LTR_L[0],
        "height": LTR_L[1],
        "sign_pages": [6],
        "sign_label": "Partner",
        "purpose": "Letter landscape source. Convert to Letter Portrait or A4 and apply Fund 2 letterhead.",
        "section_names": ["Index", "SPA", "Disclosure", "W&I", "Funds flow", "Closing signatures"],
    },
    {
        "index": 19,
        "filename": "sample_pack_19_angel_followon.pdf",
        "title": "Angel Follow-on Note",
        "subtitle": "A4 portrait, 3 pages",
        "pages": 3,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [3],
        "sign_label": "Angel Fund partner",
        "purpose": "Use Fund 1 letterhead (Angel Fund sample) plus partner signature.",
        "section_names": ["Round", "Cap table", "Approval"],
    },
    {
        "index": 20,
        "filename": "sample_pack_20_twelve_page_im.pdf",
        "title": "Information Memorandum Extract",
        "subtitle": "A4 portrait, 12 pages",
        "pages": 12,
        "width": A4_P[0],
        "height": A4_P[1],
        "sign_pages": [12],
        "sign_label": "Authorized partner",
        "purpose": "Largest pack. Stress-test page navigation, convert, letterhead, and final-page signing.",
        "section_names": [f"IM section {n}" for n in range(1, 12)] + ["Execution page"],
    },
]


def generate_sample_pack() -> None:
    for spec in PACK_SPECS:
        generate_pack_document(spec)


def generate_us_letter_landscape() -> None:
    """US Letter landscape (792 x 612 pt) — not A4 — to verify size is preserved."""
    doc = fitz.open()
    page = doc.new_page(width=792, height=612)
    page.insert_text((72, 40), "YPEF Sample US Letter Landscape", fontsize=9, color=(0.4, 0.4, 0.4))
    page.insert_text((72, 90), "US LETTER LANDSCAPE - SAMPLE", fontsize=18, fontname="hebo")
    page.insert_text(
        (72, 115),
        "792 x 612 pt. After signing, this page must still be Letter landscape.",
        fontsize=10,
        color=(0.4, 0.4, 0.4),
    )
    textbox(
        page,
        fitz.Rect(72, 150, 720, 280),
        "Use this file to confirm stamps and signatures work on a non-A4 page "
        "and that orientation is unchanged in the downloaded PDF.",
    )
    page.insert_text((520, 400), "Stamp / signature:", fontsize=11, fontname="hebo")
    page.draw_line((520, 440), (720, 440), color=(0.6, 0.6, 0.6), width=0.8)
    doc.save(OUT / "sample_us_letter_landscape.pdf")
    doc.close()


def main() -> None:
    generate_partnership_addendum()
    generate_multi_page_agreement()
    generate_tri_partner_resolution()
    generate_capital_call_notice()
    generate_landscape_cover_note()
    generate_us_letter_landscape()
    generate_sample_pack()
    print("Generated:")
    for path in sorted(OUT.glob("*.pdf")):
        print(f" - {path.name} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

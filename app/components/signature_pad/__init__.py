"""Drag-and-drop signature overlay over a fitted page preview."""

from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components

_FRONTEND = Path(__file__).resolve().parent / "frontend"

_signature_pad = components.declare_component(
    "signature_pad",
    path=str(_FRONTEND),
)


def signature_pad(
    *,
    page_image: str,
    width: int,
    height: int,
    stamps: list[dict],
    active_id: str,
    key: str,
    hint: str = (
        "Drag each signature onto a blank line. Use the corner to resize. "
        "Red outline means the stamp is sitting on text."
    ),
) -> dict | None:
    return _signature_pad(
        page_image=page_image,
        width=int(width),
        height=int(height),
        stamps=stamps,
        active_id=active_id,
        hint=hint,
        key=key,
    )

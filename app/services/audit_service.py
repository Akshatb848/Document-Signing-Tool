"""Append-only CSV audit trail."""

from __future__ import annotations

import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.config import AUDIT_COLUMNS, AUDIT_CSV_PATH, ensure_data_dirs
from app.services.pdf_service import PlacementRect

IST = timezone(timedelta(hours=5, minutes=30))


def _now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _ensure_audit_file() -> None:
    ensure_data_dirs()
    if AUDIT_CSV_PATH.exists():
        return
    with AUDIT_CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_COLUMNS)
        writer.writeheader()


def append_audit_record(
    *,
    log_id: str,
    operator: str,
    document_filename: str,
    document_hash: str,
    partner_signed: str,
    placement: PlacementRect,
    output_filename: str,
    email_status: str,
) -> str:
    _ensure_audit_file()
    record = {
        "log_id": log_id,
        "timestamp": _now_ist(),
        "operator": operator,
        "document_filename": document_filename,
        "document_hash": document_hash,
        "partner_signed": partner_signed,
        "page_number": placement.page_number,
        "position": placement.format_position(),
        "output_filename": output_filename,
        "email_status": email_status,
    }
    with AUDIT_CSV_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_COLUMNS)
        writer.writerow(record)
    return log_id


def read_audit_log() -> list[dict[str, str]]:
    if not AUDIT_CSV_PATH.exists():
        return []
    with AUDIT_CSV_PATH.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

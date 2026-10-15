"""Append-only, hash-chained CSV audit trail.

Every record's hash covers its own fields plus the previous record's hash,
so any row edited outside this module (e.g. opened in Excel and resaved)
breaks the chain from that point forward — verify_audit_log_integrity()
detects this. The file is only ever opened in append mode: no row is ever
rewritten. An email status becoming known after the fact (send succeeds/
fails, or a manual retry) is recorded as a new row linked to the original
signing event via parent_log_id, never as an edit of the original row.
"""

from __future__ import annotations

import csv
import hashlib
import threading
from datetime import datetime, timezone, timedelta

from app.config import AUDIT_CSV_PATH, ensure_data_dirs
from app.services.pdf_service import PlacementRect

IST = timezone(timedelta(hours=5, minutes=30))
GENESIS_HASH = "0" * 64

FIELDNAMES = [
    "log_id",
    "parent_log_id",
    "timestamp",
    "operator",
    "document_filename",
    "document_hash",
    "partner_signed",
    "fund_stamp",
    "letterhead",
    "page_setup",
    "signed_timestamp",
    "page_number",
    "position",
    "output_filename",
    "email_status",
    "prev_hash",
    "record_hash",
]

_RECORD_FIELDS = (
    "log_id",
    "parent_log_id",
    "timestamp",
    "operator",
    "document_filename",
    "document_hash",
    "partner_signed",
    "fund_stamp",
    "letterhead",
    "page_setup",
    "signed_timestamp",
    "page_number",
    "position",
    "output_filename",
    "email_status",
)

# Guards read-last-hash-then-append so two concurrent signing actions (from
# different browser sessions hitting this same process) can't compute the
# same prev_hash and fork the chain. This module is a normal Python import
# (unlike app/main.py, which Streamlit re-executes on every rerun), so a
# plain module-level lock is created once per process and stays valid.
_lock = threading.Lock()


def _now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _ensure_file() -> None:
    ensure_data_dirs()
    if not AUDIT_CSV_PATH.exists():
        with AUDIT_CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=FIELDNAMES).writeheader()
        return
    with AUDIT_CSV_PATH.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        existing = reader.fieldnames or []
        rows = list(reader)
    if list(existing) == FIELDNAMES:
        return
    migrated = []
    prev = GENESIS_HASH
    for row in rows:
        record = {field: row.get(field, "") for field in _RECORD_FIELDS}
        new_row = dict(record)
        new_row["prev_hash"] = prev
        new_row["record_hash"] = _record_hash(prev, record)
        prev = new_row["record_hash"]
        migrated.append(new_row)
    with AUDIT_CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(migrated)


def _read_all_rows() -> list[dict]:
    _ensure_file()
    with AUDIT_CSV_PATH.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _record_hash(prev_hash: str, record: dict) -> str:
    canonical = (
        "|".join(str(record.get(field, "")) for field in _RECORD_FIELDS) + "|" + prev_hash
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _append_row(record: dict) -> None:
    with _lock:
        rows = _read_all_rows()
        prev_hash = rows[-1]["record_hash"] if rows else GENESIS_HASH
        row = dict(record)
        row["prev_hash"] = prev_hash
        row["record_hash"] = _record_hash(prev_hash, record)
        with AUDIT_CSV_PATH.open("a", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=FIELDNAMES).writerow(row)


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
    fund_stamp: str = "",
    letterhead: str = "",
    page_setup: str = "",
    signed_timestamp: str = "",
) -> str:
    """Record a new signing event. Must be called, and must succeed, before
    the signed PDF is persisted or the partner is emailed (brief §10: the
    log is the source of truth)."""
    _append_row(
        {
            "log_id": log_id,
            "parent_log_id": "",
            "timestamp": _now_ist(),
            "operator": operator,
            "document_filename": document_filename,
            "document_hash": document_hash,
            "partner_signed": partner_signed,
            "fund_stamp": fund_stamp,
            "letterhead": letterhead,
            "page_setup": page_setup,
            "signed_timestamp": signed_timestamp,
            "page_number": placement.page_number,
            "position": placement.format_position(),
            "output_filename": output_filename,
            "email_status": email_status,
        }
    )
    return log_id


def record_email_status(original_log_id: str, email_status: str) -> None:
    """Append a follow-up row recording an email outcome (initial send or a
    later retry) for an existing signing event, without editing the
    original row."""
    original = next(
        (
            row
            for row in _read_all_rows()
            if row["log_id"] == original_log_id and not row["parent_log_id"]
        ),
        None,
    )
    if original is None:
        return
    _append_row(
        {
            "log_id": f"{original_log_id}#{int(datetime.now(IST).timestamp() * 1000)}",
            "parent_log_id": original_log_id,
            "timestamp": _now_ist(),
            "operator": original["operator"],
            "document_filename": original["document_filename"],
            "document_hash": original["document_hash"],
            "partner_signed": original.get("partner_signed", ""),
            "fund_stamp": original.get("fund_stamp", ""),
            "letterhead": original.get("letterhead", ""),
            "page_setup": original.get("page_setup", ""),
            "signed_timestamp": original.get("signed_timestamp", ""),
            "page_number": original["page_number"],
            "position": original["position"],
            "output_filename": original["output_filename"],
            "email_status": email_status,
        }
    )


def read_audit_log() -> list[dict[str, str]]:
    """One row per signing event, reflecting its most recent known
    email_status (i.e. the latest row in that event's chain)."""
    latest_by_event: dict[str, dict] = {}
    order: list[str] = []
    for row in _read_all_rows():
        event_key = row["parent_log_id"] or row["log_id"]
        if event_key not in latest_by_event:
            order.append(event_key)
        latest_by_event[event_key] = row

    display_fields = _RECORD_FIELDS[2:]  # skip log_id/parent_log_id, added back below
    result = []
    for event_key in order:
        row = latest_by_event[event_key]
        entry = {"log_id": event_key}
        entry.update({field: row.get(field, "") for field in display_fields})
        result.append(entry)
    return result


def verify_audit_log_integrity() -> tuple[bool, str]:
    """Walk the full hash chain (every row, not just latest-per-event) and
    confirm nothing was altered outside this module."""
    rows = _read_all_rows()
    prev_hash = GENESIS_HASH
    for index, row in enumerate(rows, start=1):
        record = {field: row.get(field, "") for field in _RECORD_FIELDS}
        expected = _record_hash(prev_hash, record)
        if row["prev_hash"] != prev_hash or row["record_hash"] != expected:
            return False, f"Chain broken at log_id={row['log_id']} (row {index})"
        prev_hash = row["record_hash"]
    return True, f"OK — {len(rows)} record(s) verified"

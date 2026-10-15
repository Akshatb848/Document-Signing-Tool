import pytest

import app.services.audit_service as audit_service
from app.services.pdf_service import PlacementRect


@pytest.fixture(autouse=True)
def isolated_csv(tmp_path, monkeypatch):
    csv_path = tmp_path / "audit_log.csv"
    monkeypatch.setattr(audit_service, "AUDIT_CSV_PATH", csv_path)
    return csv_path


def _placement() -> PlacementRect:
    return PlacementRect(page_number=1, x0=10, y0=20, x1=110, y1=60)


def test_append_and_read_round_trip():
    log_id = audit_service.append_audit_record(
        log_id="evt-1",
        operator="Sanjay Jha",
        document_filename="doc.pdf",
        document_hash="deadbeef",
        partner_signed="Sanjay Pande",
        placement=_placement(),
        output_filename="doc_signed.pdf",
        email_status="pending",
        fund_stamp="Fund 1",
        letterhead="Fund 1",
        page_setup="A4 Portrait",
        signed_timestamp="Signed 2026-10-07 12:00 IST",
    )
    assert log_id == "evt-1"

    rows = audit_service.read_audit_log()
    assert len(rows) == 1
    assert rows[0]["log_id"] == "evt-1"
    assert rows[0]["email_status"] == "pending"
    assert rows[0]["fund_stamp"] == "Fund 1"
    assert rows[0]["letterhead"] == "Fund 1"
    assert rows[0]["page_setup"] == "A4 Portrait"
    assert rows[0]["signed_timestamp"] == "Signed 2026-10-07 12:00 IST"


def test_file_is_a_plain_csv(isolated_csv):
    audit_service.append_audit_record(
        log_id="evt-1",
        operator="Sanjay Jha",
        document_filename="doc.pdf",
        document_hash="deadbeef",
        partner_signed="Sanjay Pande",
        placement=_placement(),
        output_filename="doc_signed.pdf",
        email_status="pending",
    )
    assert isolated_csv.suffix == ".csv"
    text = isolated_csv.read_text(encoding="utf-8")
    header = text.splitlines()[0]
    assert "log_id,parent_log_id,timestamp" in header
    assert "fund_stamp" in header
    assert "letterhead" in header
    assert "signed_timestamp" in header


def test_email_status_followup_updates_visible_status_without_extra_event():
    audit_service.append_audit_record(
        log_id="evt-2",
        operator="Sanjay Jha",
        document_filename="doc.pdf",
        document_hash="deadbeef",
        partner_signed="Sanjay Pande",
        placement=_placement(),
        output_filename="doc_signed.pdf",
        email_status="pending",
    )
    audit_service.record_email_status("evt-2", "sent at 2026-08-20 12:00:00 IST")

    rows = audit_service.read_audit_log()
    # Still exactly one *event* row shown, but reflecting the latest status.
    assert len(rows) == 1
    assert rows[0]["log_id"] == "evt-2"
    assert rows[0]["email_status"] == "sent at 2026-08-20 12:00:00 IST"


def test_multiple_events_and_retries_count_correctly():
    for i in range(3):
        audit_service.append_audit_record(
            log_id=f"evt-{i}",
            operator="Sanjay Jha",
            document_filename=f"doc{i}.pdf",
            document_hash="deadbeef",
            partner_signed="Sanjay Pande",
            placement=_placement(),
            output_filename=f"doc{i}_signed.pdf",
            email_status="pending",
        )
    audit_service.record_email_status("evt-1", "failed: smtp timeout")
    audit_service.record_email_status("evt-1", "retried: sent")

    rows = audit_service.read_audit_log()
    assert len(rows) == 3  # still 3 signing events, not 5 rows
    by_id = {row["log_id"]: row for row in rows}
    assert by_id["evt-1"]["email_status"] == "retried: sent"
    assert by_id["evt-0"]["email_status"] == "pending"


def test_integrity_ok_on_untampered_chain():
    for i in range(5):
        audit_service.append_audit_record(
            log_id=f"evt-{i}",
            operator="Sanjay Jha",
            document_filename=f"doc{i}.pdf",
            document_hash="deadbeef",
            partner_signed="Sanjay Pande",
            placement=_placement(),
            output_filename=f"doc{i}_signed.pdf",
            email_status="pending",
        )
    intact, _ = audit_service.verify_audit_log_integrity()
    assert intact is True


def test_integrity_detects_direct_tampering(isolated_csv):
    audit_service.append_audit_record(
        log_id="evt-1",
        operator="Sanjay Jha",
        document_filename="doc.pdf",
        document_hash="deadbeef",
        partner_signed="Sanjay Pande",
        placement=_placement(),
        output_filename="doc_signed.pdf",
        email_status="pending",
    )
    audit_service.append_audit_record(
        log_id="evt-2",
        operator="Sanjay Jha",
        document_filename="doc2.pdf",
        document_hash="cafebabe",
        partner_signed="Girish Shivani",
        placement=_placement(),
        output_filename="doc2_signed.pdf",
        email_status="pending",
    )

    # Simulate someone bypassing the app and hand-editing the CSV directly
    # (e.g. opening it in a spreadsheet and changing a cell).
    text = isolated_csv.read_text(encoding="utf-8")
    tampered = text.replace("Sanjay Pande", "Sunil K Goyal", 1)
    isolated_csv.write_text(tampered, encoding="utf-8")

    intact, detail = audit_service.verify_audit_log_integrity()
    assert intact is False


def test_no_update_or_delete_exposed_in_module_api():
    exported = {name for name in dir(audit_service) if not name.startswith("_")}
    assert not any(name.lower() in ("update", "delete", "edit") for name in exported)

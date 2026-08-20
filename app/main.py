"""YPEF Partner Document Signing Tool — Streamlit application."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import streamlit as st

from app.config import (
    AUDIT_CSV_PATH,
    OUTPUT_DIR,
    PARTNERS,
    ensure_data_dirs,
    get_settings,
    partner_signature_path,
)
from app.services.audit_service import append_audit_record, read_audit_log
from app.services.email_service import send_partner_notification
from app.services.pdf_service import (
    PlacementRect,
    apply_signature,
    build_preview_image,
    page_count,
    render_page,
    save_pdf,
    sha256_bytes,
    signature_aspect_ratio,
)

IST = timezone(timedelta(hours=5, minutes=30))

st.set_page_config(
    page_title="YPEF Document Signing",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _init_session_state() -> None:
    defaults = {
        "authenticated": False,
        "step": 1,
        "pdf_bytes": None,
        "pdf_filename": "",
        "pdf_hash": "",
        "partner": None,
        "page_number": 1,
        "placement": None,
        "signed_pdf_bytes": None,
        "signed_filename": "",
        "log_id": "",
        "email_status": "",
        "upload_key": 0,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _reset_workflow() -> None:
    upload_key = st.session_state.get("upload_key", 0) + 1
    for key in (
        "step",
        "pdf_bytes",
        "pdf_filename",
        "pdf_hash",
        "partner",
        "page_number",
        "placement",
        "signed_pdf_bytes",
        "signed_filename",
        "log_id",
        "email_status",
    ):
        st.session_state.pop(key, None)
    _init_session_state()
    st.session_state["step"] = 1
    st.session_state["upload_key"] = upload_key


def _login_gate() -> bool:
    settings = get_settings()
    if st.session_state.authenticated:
        return True

    st.title("YPEF Partner Document Signing")
    st.caption("Authorized operators only")
    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
        if submitted and password == settings.app_password:
            st.session_state.authenticated = True
            st.rerun()
        elif submitted:
            st.error("Invalid password.")
    return False


def _sidebar() -> None:
    settings = get_settings()
    with st.sidebar:
        st.header("Session")
        st.write(f"**Operator:** {settings.operator_name}")
        st.write(f"**Step:** {st.session_state.step} of 4")
        if st.button("Start new document", use_container_width=True):
            _reset_workflow()
            st.rerun()

        st.divider()
        st.subheader("Audit log")
        st.caption(str(AUDIT_CSV_PATH))
        log_rows = read_audit_log()
        st.metric("Total signing events", len(log_rows))
        if log_rows:
            st.dataframe(log_rows[-10:], use_container_width=True, hide_index=True)

        st.divider()
        if settings.email_enabled:
            st.success("Email notifications enabled")
        else:
            st.info("Email disabled (configure SMTP in `.env`)")


def _missing_signatures() -> list[str]:
    missing = []
    for name in PARTNERS:
        if not partner_signature_path(name).exists():
            missing.append(name)
    return missing


def _step_upload() -> None:
    st.subheader("1. Upload PDF")
    uploaded = st.file_uploader(
        "Select a PDF document",
        type=["pdf"],
        key=f"uploader_{st.session_state.upload_key}",
    )
    if uploaded is None:
        st.info("Upload a partnership document to begin.")
        return

    pdf_bytes = uploaded.getvalue()
    st.session_state.pdf_bytes = pdf_bytes
    st.session_state.pdf_filename = uploaded.name
    st.session_state.pdf_hash = sha256_bytes(pdf_bytes)
    total_pages = page_count(pdf_bytes)

    st.success(f"Uploaded **{uploaded.name}** ({total_pages} page{'s' if total_pages != 1 else ''})")
    st.caption(f"SHA-256: `{st.session_state.pdf_hash}`")

    if st.button("Continue to signature placement →", type="primary"):
        st.session_state.step = 2
        st.rerun()


def _step_place() -> None:
    st.subheader("2. Select partner & place signature")
    pdf_bytes = st.session_state.pdf_bytes
    if not pdf_bytes:
        st.warning("Upload a PDF first.")
        st.session_state.step = 1
        st.rerun()
        return

    missing = _missing_signatures()
    if missing:
        st.error("Missing signature images for: " + ", ".join(missing))
        st.caption(f"Add PNG files under `{Path('data/signatures').resolve()}`")
        return

    total_pages = page_count(pdf_bytes)
    col1, col2 = st.columns([1, 2])

    with col1:
        partner = st.selectbox("Partner signature", list(PARTNERS.keys()))
        page_number = st.number_input(
            "Page number",
            min_value=1,
            max_value=total_pages,
            value=st.session_state.page_number,
            step=1,
        )

        render = render_page(pdf_bytes, page_number)
        st.caption(f"Page size: {render.pdf_width:.0f} × {render.pdf_height:.0f} pt")

        signature_path = partner_signature_path(partner)
        aspect_ratio = signature_aspect_ratio(signature_path)

        st.markdown("**Signature position**")
        left_pct = st.slider("Horizontal position (% from left edge)", 0, 100, 10)
        top_pct = st.slider("Vertical position (% from top edge)", 0, 100, 80)
        width_pct = st.slider("Signature width (% of page width)", 5, 60, 20)

        width_pts = render.pdf_width * width_pct / 100
        height_pts = width_pts * aspect_ratio
        x0 = render.pdf_width * left_pct / 100
        x1 = min(x0 + width_pts, render.pdf_width)
        y1 = render.pdf_height * (1 - top_pct / 100)
        y0 = max(y1 - height_pts, 0)

        placement = PlacementRect(page_number=page_number, x0=x0, y0=y0, x1=x1, y1=y1)

        with st.expander("Placement coordinates (PDF points)", expanded=False):
            st.json(placement.as_dict())

    with col2:
        preview = build_preview_image(pdf_bytes, signature_path, placement)
        st.image(preview, caption="Live preview with signature overlay", use_container_width=True)

    st.session_state.partner = partner
    st.session_state.page_number = page_number
    st.session_state.placement = placement

    if st.button("Continue to confirmation →", type="primary"):
        st.session_state.step = 3
        st.rerun()


def _step_confirm() -> None:
    st.subheader("3. Confirm & sign")
    pdf_bytes = st.session_state.pdf_bytes
    partner = st.session_state.partner
    placement = st.session_state.placement

    if not pdf_bytes or not partner or not placement:
        st.warning("Complete signature placement before confirming.")
        st.session_state.step = 2
        st.rerun()
        return

    settings = get_settings()
    signature_path = partner_signature_path(partner)

    st.markdown("Review the details below before finalizing.")
    summary = st.container(border=True)
    with summary:
        cols = st.columns(2)
        cols[0].markdown(f"**Document:** {st.session_state.pdf_filename}")
        cols[0].markdown(f"**Partner:** {partner}")
        cols[0].markdown(f"**Page:** {placement.page_number}")
        cols[0].markdown(f"**Operator:** {settings.operator_name}")
        cols[1].markdown(f"**Position:** `{placement.format_position()}`")
        cols[1].markdown(f"**Document hash:** `{st.session_state.pdf_hash[:16]}…`")
        cols[1].markdown(f"**Timestamp:** {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")

    preview = build_preview_image(pdf_bytes, signature_path, placement)
    st.image(preview, caption="Confirmation preview", use_container_width=True)

    confirm = st.checkbox(
        "I confirm the signature placement and partner selection are correct.",
        value=False,
    )

    col_back, col_sign = st.columns(2)
    with col_back:
        if st.button("← Back to placement"):
            st.session_state.step = 2
            st.rerun()
    with col_sign:
        if st.button("Confirm & apply signature", type="primary", disabled=not confirm):
            _finalize_signing()


def _finalize_signing() -> None:
    settings = get_settings()
    pdf_bytes = st.session_state.pdf_bytes
    partner = st.session_state.partner
    placement = st.session_state.placement
    assert pdf_bytes and partner and placement

    signature_path = partner_signature_path(partner)
    signed_bytes = apply_signature(pdf_bytes, signature_path, placement)

    stem = Path(st.session_state.pdf_filename).stem
    timestamp = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
    partner_slug = partner.lower().replace(" ", "_")
    signed_filename = f"{stem}_signed_{partner_slug}_{timestamp}.pdf"
    output_path = OUTPUT_DIR / signed_filename
    save_pdf(signed_bytes, output_path)

    log_id = str(uuid.uuid4())
    email_status = send_partner_notification(
        settings,
        partner_name=partner,
        partner_email=PARTNERS[partner]["email"],
        document_filename=st.session_state.pdf_filename,
        operator_name=settings.operator_name,
        log_id=log_id,
    )

    append_audit_record(
        log_id=log_id,
        operator=settings.operator_name,
        document_filename=st.session_state.pdf_filename,
        document_hash=st.session_state.pdf_hash,
        partner_signed=partner,
        placement=placement,
        output_filename=signed_filename,
        email_status=email_status,
    )

    st.session_state.signed_pdf_bytes = signed_bytes
    st.session_state.signed_filename = signed_filename
    st.session_state.log_id = log_id
    st.session_state.email_status = email_status
    st.session_state.step = 4
    st.rerun()


def _step_complete() -> None:
    st.subheader("4. Download signed document")
    signed_bytes = st.session_state.signed_pdf_bytes
    if not signed_bytes:
        st.warning("No signed document available.")
        st.session_state.step = 1
        st.rerun()
        return

    st.success("Document signed successfully.")
    st.markdown(
        f"- **Audit ID:** `{st.session_state.log_id}`\n"
        f"- **Output file:** `{st.session_state.signed_filename}`\n"
        f"- **Email status:** {st.session_state.email_status}"
    )

    st.download_button(
        label="Download signed PDF",
        data=signed_bytes,
        file_name=st.session_state.signed_filename,
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

    st.caption(f"Saved copy: `{OUTPUT_DIR / st.session_state.signed_filename}`")

    if st.session_state.email_status.startswith("failed"):
        st.warning("Partner email failed. Audit log records the failure.")
        if st.button("Retry email notification"):
            settings = get_settings()
            status = send_partner_notification(
                settings,
                partner_name=st.session_state.partner,
                partner_email=PARTNERS[st.session_state.partner]["email"],
                document_filename=st.session_state.pdf_filename,
                operator_name=settings.operator_name,
                log_id=st.session_state.log_id,
            )
            st.session_state.email_status = f"retried: {status}"
            st.rerun()

    if st.button("Sign another document"):
        _reset_workflow()
        st.rerun()


def main() -> None:
    ensure_data_dirs()
    _init_session_state()

    if not _login_gate():
        return

    st.title("YPEF Partner Document Signing")
    st.caption("Upload → Place → Confirm → Download")

    _sidebar()

    steps = {
        1: _step_upload,
        2: _step_place,
        3: _step_confirm,
        4: _step_complete,
    }
    steps[st.session_state.step]()


if __name__ == "__main__":
    main()

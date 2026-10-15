"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SIGNATURES_DIR = DATA_DIR / "signatures"
STAMPS_DIR = DATA_DIR / "stamps"
LETTERHEADS_DIR = DATA_DIR / "letterheads"
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "output"
AUDIT_DIR = DATA_DIR / "audit"
AUDIT_CSV_PATH = AUDIT_DIR / "audit_log.csv"

# High-res render, then downscaled to fit the operator viewport.
PDF_RENDER_SCALE = 2.0
DISPLAY_MAX_WIDTH = 760
DISPLAY_MAX_HEIGHT = 860
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_PDF_PAGES = 50

PARTNERS: dict[str, dict[str, str]] = {
    "Sanjay Pande": {
        "signature_file": "sanjay_pande.png",
        "email": "sanjay.pande@yournest.in",
    },
    "Girish Shivani": {
        "signature_file": "girish_shivani.png",
        "email": "girish.shivani@yournest.in",
    },
    "Sunil K Goyal": {
        "signature_file": "sunil_k_goyal.png",
        "email": "sunil.k.goyal@yournest.in",
    },
}

FUNDS: dict[str, str] = {
    "Fund 1": "fund_1.png",
    "Fund 2": "fund_2.png",
    "Fund 3": "fund_3.png",
    "Fund 4": "fund_4.png",
    "Continuation Fund": "continuation_fund.png",
    "AMC": "amc.png",
}

KIND_SIGNATURE = "signature"
KIND_FUND = "fund"
KIND_LETTERHEAD_HEADER = "letterhead_header"
KIND_LETTERHEAD_FOOTER = "letterhead_footer"
LETTERHEAD_KINDS = {KIND_LETTERHEAD_HEADER, KIND_LETTERHEAD_FOOTER}


def _load_dotenv() -> None:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_password: str
    operator_name: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_use_tls: bool

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)


def _setting(key: str, default: str = "") -> str:
    try:
        import streamlit as st

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.environ.get(key, default)


def get_settings() -> Settings:
    return Settings(
        app_password=_setting("APP_PASSWORD", "change-me"),
        operator_name=_setting("OPERATOR_NAME", "Sanjay Jha"),
        smtp_host=_setting("SMTP_HOST", ""),
        smtp_port=int(_setting("SMTP_PORT", "587")),
        smtp_user=_setting("SMTP_USER", ""),
        smtp_password=_setting("SMTP_PASSWORD", ""),
        smtp_from=_setting("SMTP_FROM", ""),
        smtp_use_tls=_setting("SMTP_USE_TLS", "true").lower() == "true",
    )


def ensure_data_dirs() -> None:
    for path in (
        SIGNATURES_DIR,
        STAMPS_DIR,
        LETTERHEADS_DIR,
        UPLOADS_DIR,
        OUTPUT_DIR,
        AUDIT_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def partner_signature_path(partner_name: str) -> Path:
    partner = PARTNERS[partner_name]
    return SIGNATURES_DIR / partner["signature_file"]


def fund_stamp_path(fund_name: str) -> Path:
    return STAMPS_DIR / FUNDS[fund_name]


def asset_path(kind: str, name: str) -> Path:
    from app.services.letterhead import letterhead_footer_path, letterhead_header_path

    if kind == KIND_FUND:
        return fund_stamp_path(name)
    if kind == KIND_LETTERHEAD_HEADER:
        return letterhead_header_path(name)
    if kind == KIND_LETTERHEAD_FOOTER:
        return letterhead_footer_path(name)
    return partner_signature_path(name)

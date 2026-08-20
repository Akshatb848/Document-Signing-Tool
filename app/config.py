"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SIGNATURES_DIR = DATA_DIR / "signatures"
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "output"
AUDIT_DIR = DATA_DIR / "audit"
AUDIT_CSV_PATH = AUDIT_DIR / "audit_log.csv"

# Render scale: higher = sharper preview canvas (2.0 works well for placement)
PDF_RENDER_SCALE = 2.0

AUDIT_COLUMNS = [
    "log_id",
    "timestamp",
    "operator",
    "document_filename",
    "document_hash",
    "partner_signed",
    "page_number",
    "position",
    "output_filename",
    "email_status",
]

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


def get_settings() -> Settings:
    return Settings(
        app_password=os.environ.get("APP_PASSWORD", "change-me"),
        operator_name=os.environ.get("OPERATOR_NAME", "Sanjay Jha"),
        smtp_host=os.environ.get("SMTP_HOST", ""),
        smtp_port=int(os.environ.get("SMTP_PORT", "587")),
        smtp_user=os.environ.get("SMTP_USER", ""),
        smtp_password=os.environ.get("SMTP_PASSWORD", ""),
        smtp_from=os.environ.get("SMTP_FROM", ""),
        smtp_use_tls=os.environ.get("SMTP_USE_TLS", "true").lower() == "true",
    )


def ensure_data_dirs() -> None:
    for path in (SIGNATURES_DIR, UPLOADS_DIR, OUTPUT_DIR, AUDIT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def partner_signature_path(partner_name: str) -> Path:
    partner = PARTNERS[partner_name]
    return SIGNATURES_DIR / partner["signature_file"]

#!/usr/bin/env python3
"""
YPEF Partner Document Signing Tool — launcher.

Installs dependencies if needed, ensures data directories and placeholder
signatures exist, then starts the Streamlit app.

Usage:
    python run.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIREMENTS = ROOT / "requirements.txt"
APP_ENTRY = ROOT / "app" / "main.py"


def ensure_dependencies() -> None:
    required = ("streamlit", "fitz", "PIL", "pandas", "docx")
    missing = []
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    if not missing:
        return
    print("Installing dependencies from requirements.txt …")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        cwd=ROOT,
    )


def _load_font(size: int):
    from PIL import ImageFont

    for name in ("arial.ttf", "arialbd.ttf", "C:\\Windows\\Fonts\\arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def ensure_placeholder_signatures() -> None:
    from PIL import Image, ImageDraw

    signatures_dir = ROOT / "data" / "signatures"
    signatures_dir.mkdir(parents=True, exist_ok=True)

    partners = {
        "sanjay_pande.png": "Sanjay Pande",
        "girish_shivani.png": "Girish Shivani",
        "sunil_k_goyal.png": "Sunil K Goyal",
    }

    for filename, label in partners.items():
        path = signatures_dir / filename
        if path.exists():
            continue
        image = Image.new("RGBA", (400, 120), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, 399, 119], outline=(26, 115, 232, 255), width=2)
        font = _load_font(28)
        small = _load_font(14)
        draw.text((20, 40), label, fill=(26, 115, 232, 255), font=font)
        draw.text((20, 75), "(Replace with actual signature PNG)", fill=(120, 120, 120, 255), font=small)
        image.save(path, format="PNG")
        print(f"Created placeholder signature: {path}")


def ensure_placeholder_fund_stamps() -> None:
    from PIL import Image, ImageDraw

    stamps_dir = ROOT / "data" / "stamps"
    stamps_dir.mkdir(parents=True, exist_ok=True)
    funds = {
        "fund_1.png": "FUND 1",
        "fund_2.png": "FUND 2",
        "fund_3.png": "FUND 3",
        "fund_4.png": "FUND 4",
        "continuation_fund.png": "CONTINUATION",
        "amc.png": "AMC",
    }
    for filename, label in funds.items():
        path = stamps_dir / filename
        if path.exists():
            continue
        image = Image.new("RGBA", (280, 280), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 271, 271], outline=(15, 76, 129, 255), width=8)
        draw.ellipse([22, 22, 257, 257], outline=(15, 76, 129, 200), width=2)
        title = _load_font(22)
        small = _load_font(14)
        draw.text((140, 108), "YOURNEST", fill=(15, 76, 129, 255), font=small, anchor="mm")
        draw.text((140, 148), label, fill=(15, 76, 129, 255), font=title, anchor="mm")
        draw.text((140, 188), "STAMP", fill=(15, 76, 129, 180), font=small, anchor="mm")
        image.save(path, format="PNG")
        print(f"Created placeholder fund stamp: {path}")


def ensure_env_template() -> None:
    env_path = ROOT / ".env"
    example_path = ROOT / ".env.example"
    if not env_path.exists() and example_path.exists():
        env_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
        print("Created .env from .env.example — update APP_PASSWORD before use.")


def main() -> None:
    if not APP_ENTRY.exists():
        raise SystemExit(f"App entry not found: {APP_ENTRY}")

    ensure_dependencies()
    ensure_env_template()

    sys.path.insert(0, str(ROOT))
    ensure_placeholder_signatures()
    ensure_placeholder_fund_stamps()
    from app.services.letterhead import ensure_letterhead_assets

    ensure_letterhead_assets()

    print("Starting YPEF Partner Document Signing Tool …")
    print("Press Ctrl+C to stop.\n")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(APP_ENTRY),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=ROOT,
        check=False,
    )


if __name__ == "__main__":
    main()

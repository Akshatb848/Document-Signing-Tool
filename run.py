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
    required = ("streamlit", "fitz", "PIL", "pandas")
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


def ensure_placeholder_signatures() -> None:
    from PIL import Image, ImageDraw, ImageFont

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
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except OSError:
            font = ImageFont.load_default()
        draw.text((20, 40), label, fill=(26, 115, 232, 255), font=font)
        draw.text((20, 75), "(Replace with actual signature PNG)", fill=(120, 120, 120, 255), font=font)
        image.save(path, format="PNG")
        print(f"Created placeholder signature: {path}")


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

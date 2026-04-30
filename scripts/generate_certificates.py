"""Manual certificate batch generator.

Reads app/utils/certificate_gen/names.csv (no header row required):

    Фамилия Имя Отчество, M|F[, track_slug]

Gender is case-insensitive. Track slug is optional; defaults to «Форум КБК'26».
Generated PDFs are written to app/utils/certificate_gen/output/.

Usage (from repo root):
    python scripts/generate_certificates.py
    python scripts/generate_certificates.py --csv path/to/other.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.utils.certificate_gen.generator import CertificateGenerator, CertificateGenerationError

_TEMPLATE_DIR = REPO_ROOT / "app" / "utils" / "certificate_gen"
_OUTPUT_DIR = _TEMPLATE_DIR / "output"


def _name_patronymic(full_name: str) -> str:
    parts = full_name.strip().split()
    if len(parts) >= 3:
        return f"{parts[1]} {parts[2]}"
    if len(parts) == 2:
        return parts[1]
    return full_name


def _build_filename(full_name: str) -> str:
    parts = full_name.strip().split()
    last_name = parts[0] if parts else "Участник"
    first_initial = parts[1][0] if len(parts) > 1 else ""
    safe_last = re.sub(r"[^\w]", "", last_name, flags=re.UNICODE)
    safe_initial = re.sub(r"[^\w]", "", first_initial, flags=re.UNICODE)
    return f"{safe_last}{safe_initial}_КБК_Сертификат_фотовидео_волонтер.pdf"


def _get_generator(gender: str) -> CertificateGenerator:
    template = (
        _TEMPLATE_DIR / "certificate_participant_m.html"
        if gender.upper() == "M"
        else _TEMPLATE_DIR / "certificate_participant_f.html"
    )
    return CertificateGenerator(
        output_dir=_OUTPUT_DIR,
        template_path=template,
        page_style=None,
    )


def generate_all(csv_path: Path) -> None:
    if not csv_path.exists():
        print(f"[ERROR] CSV not found: {csv_path}")
        sys.exit(1)

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for raw in csv.reader(f):
            stripped = [c.strip() for c in raw]
            if not stripped or not stripped[0]:
                continue
            rows.append(stripped)

    if not rows:
        print("[ERROR] CSV is empty.")
        sys.exit(1)

    print(f"Found {len(rows)} entries in {csv_path.name}\n")

    ok = skipped = errors = 0

    for i, cols in enumerate(rows, 1):
        full_name = cols[0]
        gender = cols[1].upper() if len(cols) > 1 else "M"
        filename = _build_filename(full_name)
        out_path = _OUTPUT_DIR / filename

        if out_path.exists():
            print(f"[{i:>3}/{len(rows)}] SKIP (exists)  {filename}")
            skipped += 1
            continue

        try:
            gen = _get_generator(gender)
            io_name = _name_patronymic(full_name)
            gen.generate(
                full_name,
                output_filename=filename,
                substitutions={"ИО_PLACEHOLDER": io_name},
            )
            print(f"[{i:>3}/{len(rows)}] OK            {filename}")
            ok += 1
        except CertificateGenerationError as exc:
            print(f"[{i:>3}/{len(rows)}] ERROR         {full_name!r}: {exc}")
            errors += 1

    print(f"\nDone: {ok} generated, {skipped} skipped, {errors} errors.")
    print(f"Output: {_OUTPUT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch certificate generator")
    parser.add_argument(
        "--csv",
        type=Path,
        default=_TEMPLATE_DIR / "names.csv",
        help="Path to names CSV (default: app/utils/certificate_gen/names.csv)",
    )
    args = parser.parse_args()
    generate_all(args.csv)

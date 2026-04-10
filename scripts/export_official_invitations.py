#!/usr/bin/env python3
"""
Export site_registrations WHERE official_invitation=TRUE to a CSV file.

Usage:
    python3 scripts/export_official_invitations.py [output.csv]

If no output path is given, the file is saved as:
    storage/official_invitations_<YYYYMMDD_HHMMSS>.csv
"""

import asyncio
import csv
import sys
from datetime import datetime
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import load_config


async def export(output_path: Path) -> None:
    config = load_config()
    db = config.db

    dsn = (
        f"postgresql://{db.user}:{db.password}"
        f"@{db.host}:{db.port}/{db.database}"
    )

    conn = await asyncpg.connect(dsn=dsn)
    try:
        rows = await conn.fetch(
            "SELECT * FROM site_registrations WHERE official_invitation = TRUE"
        )
    finally:
        await conn.close()

    if not rows:
        print("No rows returned — CSV not written.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows([dict(row) for row in rows])

    print(f"Exported {len(rows)} row(s) → {output_path}")


def main() -> None:
    if len(sys.argv) > 1:
        output_path = Path(sys.argv[1])
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path("storage") / f"official_invitations_{timestamp}.csv"

    asyncio.run(export(output_path))


if __name__ == "__main__":
    main()

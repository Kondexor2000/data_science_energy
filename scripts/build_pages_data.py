"""Fetch and export the processed Poland dataset for the static GitHub Pages site."""

from __future__ import annotations

import json
from pathlib import Path

from zielona_polska.pipeline import load_data


def main() -> None:
    output = Path("docs/data/poland_energy.json")
    data = load_data(refresh=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        data.to_json(orient="records", force_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exported {len(data)} rows to {output}")


if __name__ == "__main__":
    main()

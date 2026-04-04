#!/usr/bin/env python3
"""Merge en.json with translated partials (config, options, entity) into de.json, fr.json, …

Run from repo root:
  python custom_components/visionect_joan/translations/merge_locales.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCALES = ("de", "fr", "es", "nl", "cs")


def main() -> None:
    base = json.loads((ROOT / "en.json").read_text(encoding="utf-8"))
    for lang in LOCALES:
        partial_path = ROOT / f"{lang}.partial.json"
        if not partial_path.is_file():
            print(f"skip {lang}: missing {partial_path.name}")
            continue
        partial = json.loads(partial_path.read_text(encoding="utf-8"))
        out = json.loads(json.dumps(base))
        for key in ("config", "options", "entity"):
            if key in partial:
                out[key] = partial[key]
        (ROOT / f"{lang}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {lang}.json")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Merge en.json with translated partials into de.json, fr.json, es.json, nl.json, cs.json.

Deep-merges ``config``, ``options``, ``entity``, and ``issues`` so new English keys
are kept when a partial has not translated them yet.

Run from this directory or repo root:
  python translations/merge_locales.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
LOCALES = ("de", "fr", "es", "nl", "cs")
MERGE_KEYS = ("config", "options", "entity", "issues", "services")


def deep_merge(base: Any, overlay: Any) -> Any:
    """Recursively merge overlay onto a copy of base (dicts only)."""
    if not isinstance(base, dict) or not isinstance(overlay, dict):
        return overlay
    out = dict(base)
    for key, value in overlay.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def main() -> None:
    base = json.loads((ROOT / "en.json").read_text(encoding="utf-8"))
    for lang in LOCALES:
        partial_path = ROOT / f"{lang}.partial.json"
        if not partial_path.is_file():
            print(f"skip {lang}: missing {partial_path.name}")
            continue
        partial = json.loads(partial_path.read_text(encoding="utf-8"))
        out = json.loads(json.dumps(base))
        for key in MERGE_KEYS:
            if key in partial:
                out[key] = deep_merge(out.get(key) or {}, partial[key])
        (ROOT / f"{lang}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {lang}.json (deep-merge)")


if __name__ == "__main__":
    main()

"""Heuristics for Joan 6\" vs 13\" screen sizing (generated HTML, low-battery screen, etc.).

Matches the Visionect Server Management API **Device** object (``GET /api/device/{Uuid}``):
``Displays[].Width`` / ``Height`` (px), and optional text hints in ``Options`` (e.g. ``Revision``).
See: https://docs.visionect.com/VisionectSoftwareSuite/ManagementInterface.html
"""

from __future__ import annotations

# Minimum longer edge (px) to treat as large-format tablet (Joan 13 class).
_JOAN13_MIN_MAX_DIMENSION = 1000

# Substrings in name / model fields that suggest a 13" class device.
_JOAN13_HINTS = (
    "joan 13",
    "joan13",
    "13 pro",
    "13\"",
    "13 inch",
    "13-inch",
    "vtablet 13",
    "ep13",
    "j13 ",
    " j13",
)


def infer_screen_size_from_device(device_details: dict | None) -> str:
    """Guess ``joan6`` vs ``joan13`` from Visionect device detail payload."""
    if not device_details or not isinstance(device_details, dict):
        return "joan6"

    displays = device_details.get("Displays")
    if isinstance(displays, list) and displays:
        d0 = displays[0]
        if isinstance(d0, dict):
            w = d0.get("Width") or d0.get("NativeWidth") or 0
            h = d0.get("Height") or d0.get("NativeHeight") or 0
            try:
                wi, hi = int(w), int(h)
                if wi > 0 and hi > 0 and max(wi, hi) >= _JOAN13_MIN_MAX_DIMENSION:
                    return "joan13"
            except (TypeError, ValueError):
                pass
            res = d0.get("Resolution") or d0.get("NativeResolution")
            if isinstance(res, str):
                norm = res.lower().replace("*", "x")
                if "x" in norm:
                    try:
                        parts = norm.split("x")
                        if len(parts) >= 2:
                            wi = int(float(parts[0].strip()))
                            hi = int(float(parts[1].strip()))
                            if max(wi, hi) >= _JOAN13_MIN_MAX_DIMENSION:
                                return "joan13"
                    except (TypeError, ValueError, IndexError):
                        pass

    opts = device_details.get("Options")
    if isinstance(opts, dict):
        # Options.Revision = hardware revision name (official API); also Name, Firmware, etc.
        text_keys = (
            "Name",
            "Revision",
            "Firmware",
            "Type",
            "Model",
            "Hardware",
            "Product",
            "DeviceType",
        )
        parts = [str(opts.get(key, "")).lower() for key in text_keys]
        blob = " ".join(parts)
        if any(h in blob for h in _JOAN13_HINTS):
            return "joan13"

    return "joan6"

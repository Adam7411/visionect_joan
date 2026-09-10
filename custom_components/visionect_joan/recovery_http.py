"""HTTP recovery page: list predefined views as links (VSS Default URL fallback)."""

from __future__ import annotations

import html
import logging
from typing import TYPE_CHECKING
from urllib.parse import urlencode, urlparse

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.network import get_url

from .const import (
    DOMAIN,
    CONF_RECOVERY_PAGE_TOKEN,
    CONF_VIEWS,
    CONF_TABLET_LANGUAGE,
    resolve_tablet_content_lang,
)
from .notification_i18n import ntr

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.helpers.network import get_internal_url
except ImportError:
    get_internal_url = None


def build_vss_settings_url(host_raw: str) -> str:
    """Visionect Software Suite web UI → Settings (same port rules as VisionectAPI)."""
    url = (host_raw or "").strip()
    if not url:
        return "http://127.0.0.1:8081/settings"
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    parsed = urlparse(url)
    scheme = parsed.scheme or "http"
    hostname = parsed.hostname or ""
    port = parsed.port
    if port is None:
        port = 443 if scheme == "https" else 8081
    if not hostname:
        return "http://127.0.0.1:8081/settings"
    if ":" in hostname and not hostname.startswith("["):
        host_fmt = f"[{hostname}]"
    else:
        host_fmt = hostname
    if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
        base = f"{scheme}://{host_fmt}".rstrip("/")
    else:
        base = f"{scheme}://{host_fmt}:{port}".rstrip("/")
    return f"{base}/settings"


def build_recovery_page_url(hass: HomeAssistant, entry_id: str, token: str) -> str:
    """Full URL for VSS Default URL: entry, token, and device placeholder for sticky view choice."""
    try:
        base = (get_internal_url(hass) if get_internal_url else None) or get_url(hass)
    except Exception:
        base = get_url(hass)
    base = (base or "").rstrip("/")
    q = urlencode({"entry": entry_id, "token": token.strip()})
    return f"{base}/api/visionect_joan/recovery?{q}&device={{uuid}}"


def _parse_views_from_entry_options(raw) -> list[dict]:
    """Build [{'name','url'}, ...] from config entry options (tolerates bad rows)."""
    out: list[dict] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            url = str(item.get("url", "")).strip()
            if name and url:
                out.append({"name": name, "url": url})
        return out
    if isinstance(raw, str):
        for line in raw.strip().splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            n, u = line.split(":", 1)
            n, u = n.strip(), u.strip()
            if n and u:
                out.append({"name": n, "url": u})
    return out


def _views_for_recovery(hass: HomeAssistant, entry_id: str, entry) -> list[dict]:
    """Prefer runtime slot; fall back to entry.options so recovery works if slot is missing/stale."""
    slot = (hass.data.get(DOMAIN) or {}).get(entry_id) or {}
    raw = slot.get("views")
    if isinstance(raw, list):
        cleaned = [v for v in raw if isinstance(v, dict)]
        if cleaned:
            return cleaned
    return _parse_views_from_entry_options((entry.options or {}).get(CONF_VIEWS))


def _normalized_recovery_views(views: list[dict]) -> list[dict]:
    out: list[dict] = []
    for v in views:
        if not isinstance(v, dict):
            continue
        name = str(v.get("name", "")).strip()
        url = str(v.get("url", "")).strip()
        if name and url:
            out.append({"name": name, "url": url})
    return out


def _recovery_lang(hass: HomeAssistant, entry_id: str, entry) -> str:
    slot = (hass.data.get(DOMAIN) or {}).get(entry_id) or {}
    tablet = slot.get("tablet_language")
    if tablet is None:
        tablet = (entry.options or {}).get(CONF_TABLET_LANGUAGE, "auto")
    return resolve_tablet_content_lang(tablet, getattr(hass.config, "language", None))


def _recovery_html(
    hass: HomeAssistant,
    *,
    entry_id: str,
    token: str,
    device: str,
    views: list[dict],
    lang: str,
) -> str:
    lang_html = html.escape(lang[:8] if lang else "en")
    title = ntr(lang, "recovery_html_title")
    no_views = ntr(lang, "recovery_html_no_views")
    sticky = ntr(lang, "recovery_html_sticky_hint")

    rows: list[str] = []
    for idx, v in enumerate(views):
        name = str(v.get("name", "")).strip()
        url = str(v.get("url", "")).strip()
        if not name or not url:
            continue
        if device:
            q = urlencode(
                {
                    "entry": entry_id,
                    "token": token,
                    "device": device,
                    "i": str(idx),
                }
            )
            href = f"/api/visionect_joan/recovery/choose?{q}"
        else:
            href = url
        rows.append(
            f'<a class="btn" href="{html.escape(href, quote=True)}">{html.escape(name)}</a>'
        )

    if not rows:
        body = f'<p class="hint">{html.escape(no_views)}</p>'
    else:
        body = "\n".join(rows)

    sticky_block = ""
    if not device:
        sticky_block = f'<p class="sticky-hint">{html.escape(sticky)}</p>'

    return f"""<!DOCTYPE html>
<html lang="{lang_html}">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --fs-base: clamp(1.08rem, 3.8vw + 0.52rem, 1.62rem);
      --fs-h1: clamp(1.32rem, 5vw + 0.58rem, 2.2rem);
      --pad: clamp(0.8rem, 3vw, 2.1rem);
      --btn-pad-y: clamp(0.78rem, 2.8vw, 1.45rem);
      --btn-pad-x: clamp(0.9rem, 3vw, 1.65rem);
      --gap: clamp(0.58rem, 2.1vw, 1.12rem);
      --border: clamp(2px, 0.42vw, 5px);
      --maxw: min(96vw, 46rem);
    }}
    @media (min-width: 900px) {{
      :root {{
        --fs-base: clamp(1.18rem, 1.45vw + 0.95rem, 1.95rem);
        --fs-h1: clamp(1.55rem, 1.75vw + 1.1rem, 2.75rem);
        --btn-pad-y: clamp(0.85rem, 2.2vw, 1.7rem);
        --maxw: min(94vw, 54rem);
      }}
    }}
    /* Large tablets / Joan 13 Pro: stronger scale (still skips narrow Joan 6 portrait). */
    @media (min-width: 1024px) {{
      :root {{
        --fs-base: clamp(1.22rem, 1.85vw + 0.85rem, 2.5rem);
        --fs-h1: clamp(1.62rem, 2.6vw + 1rem, 3.65rem);
        --btn-pad-y: clamp(0.95rem, 2.4vw, 2.15rem);
        --btn-pad-x: clamp(1rem, 2vw, 2.1rem);
        --gap: clamp(0.68rem, 1.6vw, 1.35rem);
        --border: clamp(2px, 0.35vw, 6px);
        --maxw: min(92vw, 60rem);
      }}
    }}
    @media (min-width: 1280px) {{
      :root {{
        --fs-base: clamp(1.28rem, 1.5vw + 1rem, 2.85rem);
        --fs-h1: clamp(1.75rem, 2.2vw + 1.15rem, 4.25rem);
        --btn-pad-y: clamp(1.05rem, 2vw, 2.5rem);
        --btn-pad-x: clamp(1.05rem, 1.75vw, 2.35rem);
        --gap: clamp(0.72rem, 1.35vw, 1.45rem);
        --maxw: min(92vw, 72rem);
      }}
    }}
    @media (min-width: 1600px) {{
      :root {{
        --fs-base: clamp(1.35rem, 1.25vw + 1.1rem, 3.15rem);
        --fs-h1: clamp(1.88rem, 1.85vw + 1.3rem, 4.75rem);
        --btn-pad-y: clamp(1.12rem, 1.65vw, 2.85rem);
        --btn-pad-x: clamp(1.1rem, 1.4vw, 2.65rem);
        --maxw: min(90vw, 82rem);
      }}
    }}
    body {{
      font-family: system-ui, Segoe UI, sans-serif;
      margin: var(--pad) auto;
      max-width: var(--maxw);
      font-size: var(--fs-base);
      line-height: 1.35;
      box-sizing: border-box;
    }}
    h1 {{
      font-size: var(--fs-h1);
      margin: 0 0 var(--gap);
      line-height: 1.2;
    }}
    p.hint, p.sticky-hint {{
      color: #333;
      font-size: var(--fs-base);
      margin: 0 0 var(--gap);
    }}
    p.sticky-hint {{ opacity: 0.92; }}
    a.btn {{
      display: block;
      padding: var(--btn-pad-y) var(--btn-pad-x);
      margin: var(--gap) 0;
      border: var(--border) solid #000;
      text-align: center;
      color: #000;
      text-decoration: none;
      font-weight: 600;
      font-size: var(--fs-base);
    }}
    a.btn:active {{ background: #eee; }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  {sticky_block}
  {body}
</body>
</html>"""


class VisionectJoanRecoveryView(HomeAssistantView):
    """Unauthenticated GET page for Joan after VSS fallback (token query param)."""

    url = "/api/visionect_joan/recovery"
    name = "api:visionect_joan:recovery"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.StreamResponse:
        entry_id = (request.query.get("entry") or "").strip()
        token = (request.query.get("token") or "").strip()
        device = (request.query.get("device") or "").strip()
        if not entry_id or not token:
            return web.Response(
                status=400,
                text="Missing entry or token query parameter.",
                content_type="text/plain",
                charset="utf-8",
            )

        entry = self.hass.config_entries.async_get_entry(entry_id)
        if not entry or entry.domain != DOMAIN:
            return web.Response(
                status=404,
                text="Unknown config entry.",
                content_type="text/plain",
                charset="utf-8",
            )

        expected = str((entry.options or {}).get(CONF_RECOVERY_PAGE_TOKEN, "")).strip()
        if not expected or token != expected:
            _LOGGER.warning("Visionect recovery page: invalid or missing token for entry %s", entry_id)
            return web.Response(
                status=401,
                text="Unauthorized.",
                content_type="text/plain",
                charset="utf-8",
            )

        try:
            lang = _recovery_lang(self.hass, entry_id, entry)
            raw_views = _views_for_recovery(self.hass, entry_id, entry)
            views = _normalized_recovery_views(raw_views)
            page = _recovery_html(
                self.hass,
                entry_id=entry_id,
                token=token,
                device=device,
                views=views,
                lang=lang,
            )
            return web.Response(
                text=page,
                content_type="text/html",
                charset="utf-8",
                headers={"Cache-Control": "no-store"},
            )
        except Exception as err:
            _LOGGER.exception("Visionect recovery page failed for entry %s: %s", entry_id, err)
            return web.Response(
                status=500,
                text="Recovery page error (see Home Assistant log).",
                content_type="text/plain",
                charset="utf-8",
            )


class VisionectJoanRecoveryChooseView(HomeAssistantView):
    """Set WebKit session URL on VSS for a device, then redirect to the chosen view."""

    url = "/api/visionect_joan/recovery/choose"
    name = "api:visionect_joan:recovery_choose"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.StreamResponse:
        entry_id = (request.query.get("entry") or "").strip()
        token = (request.query.get("token") or "").strip()
        device = (request.query.get("device") or "").strip()
        idx_raw = (request.query.get("i") or "").strip()

        def _plain(status: int, lang: str, key: str) -> web.Response:
            return web.Response(
                status=status,
                text=ntr(lang, key),
                content_type="text/plain",
                charset="utf-8",
            )

        if not entry_id or not token or not device or not idx_raw:
            return web.Response(
                status=400,
                text="Missing entry, token, device, or view index.",
                content_type="text/plain",
                charset="utf-8",
            )

        entry = self.hass.config_entries.async_get_entry(entry_id)
        lang = "en"
        if entry and entry.domain == DOMAIN:
            lang = _recovery_lang(self.hass, entry_id, entry)

        if not entry or entry.domain != DOMAIN:
            return _plain(404, lang, "recovery_apply_bad_request")

        expected = str((entry.options or {}).get(CONF_RECOVERY_PAGE_TOKEN, "")).strip()
        if not expected or token != expected:
            _LOGGER.warning("Visionect recovery choose: invalid token for entry %s", entry_id)
            return _plain(403, lang, "recovery_apply_forbidden")

        try:
            index = int(idx_raw)
        except ValueError:
            return _plain(400, lang, "recovery_apply_bad_index")

        raw_views = _views_for_recovery(self.hass, entry_id, entry)
        views = _normalized_recovery_views(raw_views)
        if index < 0 or index >= len(views):
            return _plain(400, lang, "recovery_apply_bad_index")

        target_url = views[index]["url"]
        slot = (self.hass.data.get(DOMAIN) or {}).get(entry_id) or {}
        api = slot.get("api")
        if api is None:
            return _plain(503, lang, "recovery_apply_no_api")

        ok = await api.async_set_device_url(device, target_url, force=True)
        if not ok:
            _LOGGER.warning(
                "Visionect recovery choose: async_set_device_url failed for device %s", device
            )
            return _plain(502, lang, "recovery_apply_set_url_failed")

        restarted = await api.async_restart_session(device, silent=True)
        if not restarted:
            _LOGGER.debug("Visionect recovery choose: session restart failed for %s (URL was set)", device)

        return web.HTTPFound(location=target_url)


class VisionectJoanRecoveryApplyBackView(HomeAssistantView):
    """Set WebKit session URL on VSS to provided target, then redirect there."""

    url = "/api/visionect_joan/recovery/apply"
    name = "api:visionect_joan:recovery_apply"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.StreamResponse:
        entry_id = (request.query.get("entry") or "").strip()
        token = (request.query.get("token") or "").strip()
        device = (request.query.get("device") or "").strip()
        target_url = (request.query.get("target") or "").strip()

        def _plain(status: int, lang: str, key: str) -> web.Response:
            return web.Response(
                status=status,
                text=ntr(lang, key),
                content_type="text/plain",
                charset="utf-8",
            )

        if not entry_id or not token or not device or not target_url:
            return web.Response(
                status=400,
                text="Missing entry, token, device, or target URL.",
                content_type="text/plain",
                charset="utf-8",
            )
        parsed_target = urlparse(target_url)
        if parsed_target.scheme not in ("http", "https", "data"):
            return web.Response(
                status=400,
                text="Unsupported target URL scheme.",
                content_type="text/plain",
                charset="utf-8",
            )
        if parsed_target.scheme in ("http", "https") and not parsed_target.netloc:
            return web.Response(
                status=400,
                text="Invalid absolute target URL.",
                content_type="text/plain",
                charset="utf-8",
            )

        entry = self.hass.config_entries.async_get_entry(entry_id)
        lang = "en"
        if entry and entry.domain == DOMAIN:
            lang = _recovery_lang(self.hass, entry_id, entry)

        if not entry or entry.domain != DOMAIN:
            return _plain(404, lang, "recovery_apply_bad_request")

        expected = str((entry.options or {}).get(CONF_RECOVERY_PAGE_TOKEN, "")).strip()
        if not expected or token != expected:
            _LOGGER.warning("Visionect recovery apply: invalid token for entry %s", entry_id)
            return _plain(403, lang, "recovery_apply_forbidden")

        slot = (self.hass.data.get(DOMAIN) or {}).get(entry_id) or {}
        api = slot.get("api")
        if api is None:
            return _plain(503, lang, "recovery_apply_no_api")

        ok = await api.async_set_device_url(device, target_url, force=True)
        if not ok:
            _LOGGER.warning(
                "Visionect recovery apply: async_set_device_url failed for device %s", device
            )
            return _plain(502, lang, "recovery_apply_set_url_failed")

        # User returned to dashboard — drop cached overlay URLs so automations cannot re-push weather.
        cache = slot.get("screen_render_cache")
        if isinstance(cache, dict):
            nu = device.strip().lower()
            needle = f":{nu}:"
            overlay_prefixes = ("send_weather:", "send_calendar:", "send_energy_panel:")
            for key in list(cache.keys()):
                if needle in key and key.startswith(overlay_prefixes):
                    cache.pop(key, None)

        restarted = await api.async_restart_session(device, silent=True)
        if not restarted:
            _LOGGER.debug("Visionect recovery apply: session restart failed for %s (URL was set)", device)

        return web.HTTPFound(location=target_url)

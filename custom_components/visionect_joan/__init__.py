import logging
import urllib.parse
import voluptuous as vol
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
import uuid
import hashlib
from functools import partial
import asyncio
import time
import feedparser
import json
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, ATTR_DEVICE_ID, EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util
from homeassistant.components.camera import async_get_image
from homeassistant.components.persistent_notification import async_create as async_create_persistent_notification
from homeassistant.helpers.network import get_url
from homeassistant.components.recorder import history, get_instance
from homeassistant.helpers.event import async_track_time_interval, async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.helpers.aiohttp_client import async_get_clientsession

try:
    from homeassistant.helpers.network import get_internal_url
except ImportError:
    get_internal_url = None

from .api import VisionectAPI
from .notification_i18n import (
    ntr,
    context_truncation_suffix,
    build_ollama_diagnostic_prompt,
    build_ollama_rewrite_prompt,
)
from .const import (
    DOMAIN, CONF_API_KEY, CONF_API_SECRET, SCAN_INTERVAL,
    UNKNOWN_STRINGS, DISPLAY_ROTATIONS, SERVICE_FORCE_REFRESH, SERVICE_CLEAR_DISPLAY,
    SERVICE_SLEEP_DEVICE, SERVICE_WAKE_DEVICE, SERVICE_SEND_QR_CODE, EVENT_COMMAND_RESULT,
    NETWORK_RETRY_DELAY, ATTR_PREDEFINED_URL,
    CONF_VIEWS, CONF_MAIN_MENU_URL, CONF_CLEANUP_MAX_AGE, CONF_CLEANUP_INTERVAL,
    SERVICE_SEND_KEYPAD, SUPPORTED_IMAGE_FORMATS, SERVICE_SEND_BUTTON_PANEL,
    CONF_TABLET_LANGUAGE, CONF_RECOVERY_PROBE_URL, API_TCLV_PARAM,
    CONF_OLLAMA_ENABLED, CONF_OLLAMA_URL, CONF_OLLAMA_API_KEY,
    CONF_OLLAMA_MODEL, CONF_OLLAMA_INTERVAL_MIN,
    CONF_BATTERY_LOW_THRESHOLD_PCT,
    CONF_BATTERY_TABLET_ALERT_ENABLED,
    CONF_BATTERY_HA_LOW_NOTIFICATION_ENABLED,
    CONF_BATTERY_HA_FULL_NOTIFICATION_ENABLED,
    resolve_tablet_content_lang,
)
from .html_generator import (
    create_status_panel_url, create_text_message_url, create_todo_list_url,
    create_rss_feed_url, create_energy_panel_url, create_qr_code_url,
    create_calendar_url, create_monthly_calendar_url, create_weather_url,
    create_weather_calendar_url,
    create_simple_cache_buster, _generate_graph_image,
    _add_interactive_layer_to_url, _get_lang, create_keypad_url,
    create_button_panel_url,
    create_crypto_panel_url, create_exchange_rates_url, async_get_icon_as_base64,
)
from .screen_layout import infer_screen_size_from_device

_LOGGER = logging.getLogger(__name__)


def _tablet_notify_lang(hass: HomeAssistant) -> str:
    """Content language for Visionect persistent notifications (matches tablet / HA locale)."""
    slot = hass.data.get(DOMAIN) or {}
    return resolve_tablet_content_lang(
        slot.get("tablet_language", "auto"),
        getattr(hass.config, "language", None),
    )


PLATFORMS = ["sensor", "binary_sensor", "number", "text", "button", "select", "camera"]
URL_LENGTH_LIMIT = 4096
CACHE_DIR_NAME = "visionect_cache"

def _parse_views(views_data) -> list[dict]:
    if isinstance(views_data, list): return views_data
    if isinstance(views_data, str):
        views = []
        for line in views_data.strip().splitlines():
            if ":" in line:
                n, u = line.split(":", 1)
                views.append({"name": n.strip(), "url": u.strip()})
        return views
    return []


def get_effective_screen_size(
    hass: HomeAssistant,
    entry_id: str,
    uuid_val: str,
    device_details: dict | None,
) -> str:
    """Return ``joan6`` or ``joan13`` for generated pages (prefs per device, else API heuristic)."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry_id) or {}
    prefs = entry_data.get("prefs") or {}
    if not isinstance(prefs, dict):
        prefs = {}
    raw = (prefs.get("screen_size_by_uuid") or {}).get(uuid_val)
    if raw is not None:
        s = str(raw).strip().lower()
        if s in ("joan6", "joan13"):
            return s
    if device_details:
        return infer_screen_size_from_device(device_details)
    return "joan6"


def _collect_recovery_uuids_from_device_list(devices) -> list[str]:
    """UUIDs for session restart after VSS/HA recovery.

    The /api/device/ summary often omits ``State``; treating missing state as
    eligible matches coordinator full fetches. Only explicitly offline devices
    are skipped to avoid noisy 500s on devices with no session.
    """
    uuids: list[str] = []
    for device_entry in devices or []:
        if isinstance(device_entry, str):
            u = str(device_entry).strip().rstrip("/")
            if u:
                uuids.append(u)
            continue
        u = str(device_entry.get("Uuid", "")).strip().rstrip("/")
        if not u:
            continue
        state_val = str(device_entry.get("State", "")).strip().lower()
        if state_val == "offline":
            continue
        uuids.append(u)
    # Stable de-dupe for batch API
    return list(dict.fromkeys(uuids))


def _resolve_recovery_probe_url(
    entry: ConfigEntry,
    main_menu_fallback: str | None,
) -> str | None:
    """HTTP(S) URL to poll before restarting Joan sessions (e.g. AppDaemon dashboard)."""
    explicit = entry.options.get(CONF_RECOVERY_PROBE_URL)
    if explicit is not None:
        u = str(explicit).strip()
        if u.lower().startswith(("http://", "https://")):
            return u
    if main_menu_fallback:
        u = str(main_menu_fallback).strip()
        if u.lower().startswith(("http://", "https://")):
            return u
    return None


async def _async_wait_for_recovery_probe(
    hass: HomeAssistant,
    url: str,
    log_ctx: str,
    *,
    total_timeout_s: float = 240.0,
    interval_s: float = 3.0,
) -> bool:
    """GET url until HTTP status < 500 or timeout (handles AppDaemon after host reboot)."""
    session = async_get_clientsession(hass)
    deadline = time.monotonic() + total_timeout_s
    attempt = 0
    while time.monotonic() < deadline:
        if hass.is_stopping:
            return False
        attempt += 1
        try:
            async with session.get(
                url,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=12),
            ) as resp:
                if resp.status < 500:
                    _LOGGER.info(
                        "%s: recovery HTTP probe OK %s (status %s, attempt %d)",
                        log_ctx,
                        url,
                        resp.status,
                        attempt,
                    )
                    return True
                _LOGGER.debug(
                    "%s: recovery HTTP probe %s status %s",
                    log_ctx,
                    url,
                    resp.status,
                )
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
            _LOGGER.debug(
                "%s: recovery HTTP probe attempt %d failed: %s",
                log_ctx,
                attempt,
                err,
            )
        await asyncio.sleep(interval_s)
    _LOGGER.warning(
        "%s: recovery HTTP probe timeout (%.0fs) for %s — continuing session restart",
        log_ctx,
        total_timeout_s,
        url,
    )
    return False


def _read_last_lines(path: Path, max_lines: int = 120) -> str:
    """Read only tail lines from a UTF-8 log file."""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return "".join(lines[-max_lines:])
    except OSError:
        return ""


def _build_log_derived_metrics(collected_logs: list[tuple[str, str]]) -> str:
    """Create compact derived counters from raw log snippets."""
    all_text = "\n".join(content for _, content in collected_logs).lower()
    if not all_text.strip():
        return ""

    def _cnt(token: str) -> int:
        return all_text.count(token)

    metrics = {
        "errors": _cnt("[error]") + _cnt(" error: "),
        "warnings": _cnt("[warning]") + _cnt(" warning: "),
        "session_restart_calls": _cnt("/api/session/restart"),
        "device_reboots": _cnt("/api/device/reboot"),
        "disconnected_events": _cnt("disconnected"),
        "connection_refused": _cnt("connection refused"),
        "orphans_checks": _cnt("/api/orphans") + _cnt("orphaned check"),
        "wk_rpc_failed": _cnt("wk-process rpc failed"),
        "pv3_connections": _cnt("new pv3 connection"),
    }
    return ", ".join(f"{k}={v}" for k, v in metrics.items())


def _vss_status_str(status: dict, key: str) -> str:
    if not isinstance(status, dict):
        return ""
    v = status.get(key)
    if v is None:
        return ""
    s = str(v).strip()
    if not s or s.lower() in UNKNOWN_STRINGS:
        return ""
    return s


def _vss_error_code_is_nonzero(code_raw: str) -> bool:
    if not str(code_raw).strip():
        return False
    t = str(code_raw).strip().lower()
    if t in ("0", "0x0", "0x00", "00", "n/a"):
        return False
    if t.startswith("0x") and len(t) > 2:
        try:
            return int(t, 16) != 0
        except ValueError:
            return True
    try:
        return int(t, 10) != 0
    except ValueError:
        return True


def _build_visionect_incident_summary(devices: list, *, language: str) -> list[str]:
    """Short list of offline devices and online anomalies for the LLM (must cite UUIDs)."""
    pl = language == "pl"
    offline_rows: list[str] = []
    online_issue_rows: list[str] = []

    for dev in devices:
        if not isinstance(dev, dict):
            continue
        u = str(dev.get("Uuid", "")).strip()
        if not u:
            continue
        opts = dev.get("Options") if isinstance(dev.get("Options"), dict) else {}
        disp_name = str(opts.get("Name", "")).strip() if opts else ""
        state = str(dev.get("State", "")).strip().lower()
        st = dev.get("Status") if isinstance(dev.get("Status"), dict) else {}
        ec = _vss_status_str(st, "ErrorCode")
        cr = _vss_status_str(st, "ConnectReason")
        batt = _vss_status_str(st, "Battery")

        cr_l = cr.strip().lower() if cr else ""
        heartbeat_ok = cr_l in ("", "heartbeat")

        u_label = f"{u} ({disp_name})" if disp_name else u

        if state == "offline":
            bits = [u_label]
            if batt:
                bits.append(f"bateria {batt}%" if pl else f"battery {batt}%")
            if ec:
                bits.append(f"ErrorCode={ec}")
            if cr:
                bits.append(f"ConnectReason={cr}")
            offline_rows.append("  • " + " | ".join(bits))
        elif state == "online":
            bits_on: list[str] = []
            if _vss_error_code_is_nonzero(ec):
                bits_on.append(f"ErrorCode={ec}")
            if not heartbeat_ok and cr:
                bits_on.append(f"ConnectReason={cr}")
            if bits_on:
                online_issue_rows.append(
                    f"  • {u_label} | online | " + " | ".join(bits_on)
                )

    lines: list[str] = []
    if pl:
        lines.append("[_incydenty — obowiązkowo użyj pełnych UUID poniżej w PROBLEM / PRZYCZYNA / KROKI]")
        if not offline_rows and not online_issue_rows:
            lines.append("Brak urządzeń offline; online: brak ErrorCode≠0 i brak nietypowego ConnectReason (wszystko heartbeat lub puste).")
        else:
            if offline_rows:
                lines.append(f"OFFLINE ({len(offline_rows)} urząd.):")
                lines.extend(offline_rows)
            if online_issue_rows:
                lines.append(
                    f"ONLINE, ale status do wyjaśnienia ({len(online_issue_rows)} urząd.):"
                )
                lines.extend(online_issue_rows)
    else:
        lines.append("[_incidents — you MUST include full UUIDs below in PROBLEM / CAUSE / STEPS]")
        if not offline_rows and not online_issue_rows:
            lines.append("No offline devices; online: no non-zero ErrorCode and no unusual ConnectReason.")
        else:
            if offline_rows:
                lines.append(f"OFFLINE ({len(offline_rows)}):")
                lines.extend(offline_rows)
            if online_issue_rows:
                lines.append(f"ONLINE with status anomalies ({len(online_issue_rows)}):")
                lines.extend(online_issue_rows)
    lines.append("")
    return lines


def _format_visionect_devices_for_ai(
    devices: list,
    orphans: dict | None,
    *,
    language: str,
    max_chars: int = 12000,
) -> str:
    """Human-readable device roster for Ollama / notifications (Visionect /api/device fields)."""
    pl = language == "pl"
    o_map = orphans if isinstance(orphans, dict) else {}
    rot_pl = {"0": "portret", "1": "krajobraz 90°", "2": "portret 180°", "3": "krajobraz 270°"}

    online = offline = no_state = 0
    for d in devices:
        if not isinstance(d, dict):
            continue
        st = str(d.get("State", "")).strip().lower()
        if st == "online":
            online += 1
        elif st == "offline":
            offline += 1
        else:
            no_state += 1

    if pl:
        lines: list[str] = [
            "[Visionect — stan z API serwera VSS]",
            "",
            f"Łącznie urządzeń: {len(devices)}. Online: {online}, offline: {offline}, "
            f"bez pola „State”: {no_state}. Problematyczne (endpoint /api/orphans): {len(o_map)}.",
            "",
        ]
        lines.extend(_build_visionect_incident_summary(devices, language=language))
        lines.extend(
            [
                "Poniżej skrócony opis urządzeń (UUID, stan, sesja, wybrane statusy, ewentualnie opcje snu/pollingu, ekrany).",
                "",
            ]
        )
    else:
        lines = [
            "[Visionect — VSS server API snapshot]",
            "",
            f"Total devices: {len(devices)}. Online: {online}, offline: {offline}, "
            f"missing State field: {no_state}. Problematic (/api/orphans): {len(o_map)}.",
            "",
        ]
        lines.extend(_build_visionect_incident_summary(devices, language=language))
        lines.extend(
            [
                "Compact per-device view (UUID, state, session, selected status fields, sleep/poll options if set, displays).",
                "",
            ]
        )

    # Omit duplicate / noisy fields for notifications (firmware & revision already implied elsewhere; link type, versions clutter).
    status_order = [
        ("Battery", "Bateria (%)", "Battery (%)"),
        ("ExternalBattery", "Bateria zewnętrzna", "External battery"),
        ("Charger", "Ładowanie", "Charger"),
        ("RSSI", "RSSI (siła sygnału)", "RSSI"),
        ("Temperature", "Temperatura (°C)", "Temperature (°C)"),
        ("ErrorCode", "Kod błędu", "Error code"),
        ("ConnectReason", "Powód połączenia", "Connect reason"),
        ("LastStatus", "Ostatni status (serwer)", "Last status (server)"),
        ("Push", "Push", "Push"),
        ("PrematureWakeup", "Przedwczesne wybudzenie", "Premature wakeup"),
        ("IPAddress", "Adres IP", "IP address"),
        ("DisplayStateCRC", "CRC stanu ekranu", "Display state CRC"),
        ("BatteryVoltage", "Napięcie baterii (szac.)", "Battery voltage (est.)"),
    ]
    opt_order = [
        ("RequestedFirmware", "Żądany firmware", "Requested firmware"),
        ("PollingTime", "Polling (czas)", "Polling time"),
        ("SleepSchedule", "Harmonogram snu (min)", "Sleep schedule (min)"),
        ("PeriodicSleep", "Sen okresowy", "Periodic sleep"),
        ("ScheduledWakeup", "Planowane wybudzenie", "Scheduled wakeup"),
    ]

    for idx, dev in enumerate(devices, start=1):
        if not isinstance(dev, dict):
            continue
        block: list[str] = []
        if pl:
            block.append(f"── Urządzenie {idx}/{len(devices)} ──")
        else:
            block.append(f"── Device {idx}/{len(devices)} ──")

        u = str(dev.get("Uuid", "")).strip()
        if u:
            block.append(f"  UUID: {u}")
        sid = str(dev.get("SessionId", "")).strip()
        if sid:
            lbl = "ID sesji WebKit" if pl else "WebKit session ID"
            block.append(f"  {lbl}: {sid}")
        state = str(dev.get("State", "")).strip()
        if state:
            block.append(f"  {'Stan' if pl else 'State'}: {state}")

        st = dev.get("Status") or {}
        if isinstance(st, dict) and st:
            block.append(f"  {'Status' if pl else 'Status'}:")
            for key, pl_lbl, en_lbl in status_order:
                val = _vss_status_str(st, key)
                if val:
                    block.append(f"    • {pl_lbl if pl else en_lbl}: {val}")

        opts = dev.get("Options") or {}
        if isinstance(opts, dict) and opts:
            opt_lines: list[str] = []
            for key, pl_lbl, en_lbl in opt_order:
                val = _vss_status_str(opts, key)
                if val:
                    opt_lines.append(f"    • {pl_lbl if pl else en_lbl}: {val}")
            if opt_lines:
                block.append(f"  {'Opcje' if pl else 'Options'}:")
                block.extend(opt_lines)

        displays = dev.get("Displays")
        if isinstance(displays, list) and displays:
            block.append(f"  {'Ekrany' if pl else 'Displays'}:")
            for disp in displays:
                if not isinstance(disp, dict):
                    continue
                did = disp.get("Id", 0)
                w = disp.get("Width", "?")
                h = disp.get("Height", "?")
                rot = str(disp.get("Rotation", "")).strip()
                if pl:
                    rtxt = rot_pl.get(rot, DISPLAY_ROTATIONS.get(rot, rot or "—"))
                else:
                    rtxt = DISPLAY_ROTATIONS.get(rot, rot or "—")
                block.append(f"    • #{did}: {w}×{h} px, {'obrót' if pl else 'rotation'} {rtxt}")

        block.append("")
        chunk = "\n".join(block)
        if len("\n".join(lines)) + len(chunk) > max_chars:
            if pl:
                lines.append("… (lista skrócona — brak miejsca na pozostałe urządzenia)")
            else:
                lines.append("… (truncated — remaining devices omitted)")
            break
        lines.append(chunk)

    if o_map:
        lines.append("")
        if pl:
            lines.append("Problematyczne UUID (orphans /api/orphans):")
        else:
            lines.append("Problematic UUIDs (orphans /api/orphans):")
        for ouid, oerr in list(o_map.items())[:50]:
            lines.append(f"  • {ouid}: {oerr}")
        if len(o_map) > 50:
            lines.append(f"  … (+{len(o_map) - 50} więcej)" if pl else f"  … (+{len(o_map) - 50} more)")

    return "\n".join(lines).strip()


def _truncate_at_line_boundary(text: str, max_len: int, suffix: str) -> str:
    """Cut at last newline before max_len so values are not split mid-token."""
    if len(text) <= max_len:
        return text
    budget = max_len - len(suffix)
    if budget < 20:
        return suffix.strip()
    head = text[:budget]
    nl = head.rfind("\n")
    if nl >= budget // 2:
        head = head[:nl]
    return head.rstrip() + "\n" + suffix


def _build_ollama_context_for_notification(
    payload_parts: list[str],
    *,
    language: str,
    max_total: int = 14000,
    max_per_section: int = 12000,
) -> str:
    """Human-readable excerpt of what was sent to the model (for HA notification)."""
    suffix_part = context_truncation_suffix(language)
    trimmed: list[str] = []
    for part in payload_parts:
        p = str(part).strip()
        if len(p) > max_per_section:
            p = _truncate_at_line_boundary(p, max_per_section, suffix_part)
        trimmed.append(p)
    raw = "\n\n".join(trimmed)
    if len(raw) > max_total:
        raw = _truncate_at_line_boundary(raw, max_total, suffix_part)
    return raw


async def _async_ollama_analyze_logs(
    hass: HomeAssistant,
    *,
    base_url: str,
    model: str,
    api_key: str | None,
    log_dirs: list[Path],
    extra_sections: list[str] | None = None,
    language: str = "pl",
) -> tuple[str | None, str]:
    """Ask Ollama for short diagnosis; returns (analysis_text, context_excerpt_for_ui)."""
    files = ("admin.log", "engine.log", "gateway.log", "networkmanager.log")
    payload_parts: list[str] = []
    collected_logs: list[tuple[str, str]] = []
    for name in files:
        content = ""
        chosen_path: Path | None = None
        for d in log_dirs:
            p = d / name
            if p.exists():
                chosen_path = p
                content = await asyncio.to_thread(_read_last_lines, p, 120)
                if content.strip():
                    break
        if content.strip():
            path_info = f" ({chosen_path})" if chosen_path else ""
            collected_logs.append((name, content.strip()))
            payload_parts.append(f"[{name}{path_info}]\n{content.strip()}")

    derived = _build_log_derived_metrics(collected_logs)
    if derived:
        payload_parts.append(f"[derived_metrics]\n{derived}")

    if extra_sections:
        payload_parts.extend([s for s in extra_sections if str(s).strip()])

    if not payload_parts:
        return None, ""

    context_for_ui = _build_ollama_context_for_notification(payload_parts, language=language)

    prompt = build_ollama_diagnostic_prompt(language, payload_parts)

    base = base_url.rstrip("/")
    chat_url = f"{base}/api/chat"
    session = async_get_clientsession(hass)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    async with session.post(
        chat_url,
        json=body,
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=90),
    ) as resp:
        if resp.status >= 400:
            txt = await resp.text()
            raise RuntimeError(f"Ollama HTTP {resp.status}: {txt[:200]}")
        data = await resp.json()

    msg = data.get("message", {})
    content = str(msg.get("content", "")).strip()
    if not content:
        return None, context_for_ui

    rewrite_prompt = build_ollama_rewrite_prompt(language, content)
    rewrite_body = {
        "model": model,
        "messages": [{"role": "user", "content": rewrite_prompt}],
        "stream": False,
    }
    async with session.post(
        chat_url,
        json=rewrite_body,
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=60),
    ) as resp:
        if resp.status < 400:
            rewritten = await resp.json()
            content2 = str(rewritten.get("message", {}).get("content", "")).strip()
            if content2:
                return content2, context_for_ui

    return content, context_for_ui


# Constants for attributes
ATTR_ADD_BACK_BUTTON = "add_back_button"
ATTR_CLICK_ANYWHERE_TO_RETURN = "click_anywhere_to_return"
ATTR_CLICK_ANYWHERE_TO_ACTION = "click_anywhere_to_action"
ATTR_BACK_BUTTON_URL = "back_button_url"
ATTR_ACTION_WEBHOOK_ID = "action_webhook_id"
ATTR_ACTION_WEBHOOK_2_ID = "action_webhook_2_id"
ATTR_SMALL_SCREEN = "small_screen_optimized"  # backwards compat alias
ATTR_SCREEN_SIZE = "screen_size"
ATTR_AUTO_RETURN_SECONDS = "auto_return_seconds"

ATTR_URL = "url"
ATTR_MESSAGE = "message"
ATTR_TEXT_COLOR = "text_color"
ATTR_BACKGROUND_COLOR = "background_color"
ATTR_TEXT_SIZE = "text_size"
ATTR_TEXT_ALIGN = "text_align"
ATTR_FONT_FAMILY = "font_family"
ATTR_FONT_WEIGHT = "font_weight"
ATTR_DISPLAY_ROTATION = "display_rotation"
ATTR_LAYOUT = "layout"
ATTR_IMAGE_URL = "image_url"
ATTR_IMAGE_ZOOM = "image_zoom"
ATTR_DURATION = "duration"
ATTR_DATA = "data"
ATTR_BOX_SIZE = "box_size"
ATTR_BORDER = "border"
ATTR_FILL_COLOR = "fill_color"
ATTR_BACK_COLOR = "back_color"
ATTR_QR_MESSAGE_TEXT_SIZE = "qr_message_text_size"
ATTR_QR_MESSAGE_POSITION = "qr_message_position"
ATTR_CALENDAR_ENTITY = "calendar_entity"
ATTR_DURATION_DAYS = "duration_days"
ATTR_DISPLAY_STYLE = "display_style"
ATTR_WEATHER_ENTITY = "weather_entity"
ATTR_POWER_USAGE_ENTITY = "power_usage_entity"
ATTR_DAILY_CONSUMPTION_ENTITY = "daily_consumption_entity"
ATTR_DAILY_PRODUCTION_ENTITY = "daily_production_entity"
ATTR_DAILY_GRID_IMPORT_ENTITY = "daily_grid_import_entity"
ATTR_DAILY_GRID_EXPORT_ENTITY = "daily_grid_export_entity"
ATTR_TODO_ENTITY = "todo_entity"
ATTR_TITLE = "title"
ATTR_CAMERA_ENTITY = "camera_entity"
ATTR_CAPTION = "caption"
ATTR_ENTITIES = "entities"
ATTR_DURATION_HOURS = "duration_hours"
ATTR_GRAPH_TYPE = "graph_type"
ATTR_SHOW_POINTS = "show_points"
ATTR_ENERGY_THEME = "theme"
ATTR_COINS = "coins"
ATTR_VS_CURRENCY = "vs_currency"
ATTR_BASE_CURRENCY = "base_currency"
ATTR_CURRENCIES = "currencies"
ATTR_HISTORY_HOURS = "history_hours"
ATTR_HISTORY_DAYS = "history_days"
ATTR_SHOW_HEADER = "show_header"
ATTR_HEART_BEAT_INTERVAL = "heart_beat_interval"
ATTR_NETWORK_ERROR_RETRY_INTERVAL = "network_error_retry_interval"
ATTR_SYSTEM_SCREENS = "system_screens"
ATTR_TOUCH_MODE = "touch_mode"
ATTR_POWER_SAVING_MODE = "power_saving_mode"

SAFE_HEART_BEAT_OPTIONS = [1, 2, 3, 4, 5, 10, 15, 30, 60]
SAFE_NETWORK_RETRY_OPTIONS = [1, 2, 3, 5, 10, 15, 30]

# CoinGecko symbol → ID map (common coins; user can also pass IDs directly)
CRYPTO_SYMBOL_MAP = {
    "BTC": "bitcoin",       "ETH": "ethereum",       "BNB": "binancecoin",
    "SOL": "solana",        "ADA": "cardano",         "XRP": "ripple",
    "DOT": "polkadot",      "DOGE": "dogecoin",       "AVAX": "avalanche-2",
    "MATIC": "matic-network","LINK": "chainlink",     "LTC": "litecoin",
    "UNI": "uniswap",       "ATOM": "cosmos",         "NEAR": "near",
    "TRX": "tron",          "SHIB": "shiba-inu",      "XLM": "stellar",
    "BCH": "bitcoin-cash",  "ETC": "ethereum-classic","APT": "aptos",
    "OP": "optimism",       "ARB": "arbitrum",        "FTM": "fantom",
    "USDT": "tether",       "USDC": "usd-coin",       "TON": "the-open-network",
    "ICP": "internet-computer", "INJ": "injective-protocol", "RNDR": "render-token",
    "PEPE": "pepe",         "WIF": "dogwifcoin",      "BONK": "bonk",
    "FET": "fetch-ai",      "TIA": "celestia",        "KAS": "kaspa",
    "LDO": "lido-dao",      "AR": "arweave",          "FIL": "filecoin",
    "STX": "stacks",        "XMR": "monero",          "VET": "vechain",
}

# Services
SERVICE_SET_URL = "set_url"
SERVICE_SEND_TEXT = "send_text"
SERVICE_SET_DISPLAY_ROTATION = "set_display_rotation"
SERVICE_SEND_CALENDAR = "send_calendar"
SERVICE_SEND_WEATHER = "send_weather"
SERVICE_SEND_ENERGY_PANEL = "send_energy_panel"
SERVICE_SEND_TODO_LIST = "send_todo_list"
SERVICE_SEND_CAMERA_SNAPSHOT = "send_camera_snapshot"
SERVICE_SEND_STATUS_PANEL = "send_status_panel"
SERVICE_SEND_SENSOR_GRAPH = "send_sensor_graph"
SERVICE_SEND_RSS_FEED = "send_rss_feed"
SERVICE_CLEAR_WEB_CACHE = "clear_web_cache"
SERVICE_START_SLIDESHOW = "start_slideshow"
SERVICE_SEND_IMAGE_URL = "send_image_url"
SERVICE_SET_SESSION_OPTIONS = "set_session_options"
SERVICE_SEND_CRYPTO = "send_crypto"
SERVICE_READ_SAFE_DEVICE_CONFIG = "read_safe_device_config"
SERVICE_APPLY_SAFE_DEVICE_CONFIG = "apply_safe_device_config"
SERVICE_RESTORE_SAFE_DEVICE_CONFIG = "restore_safe_device_config"

EINK_COLORS = ["black", "white"]
FONT_WEIGHTS = ["normal", "bold"]
LAYOUT_OPTIONS = ["text_only", "image_top", "image_bottom", "image_left", "image_right", "image_only"]

THEMED_FONTS = {
    "Modern": "'Trebuchet MS', Helvetica, sans-serif",
    "Readable": "Verdana, Geneva, sans-serif",
    "Archivo Black": "'Archivo Black', sans-serif",
    "Arbutus": "'Arbutus', serif",
    "Asimovian": "'Asimovian', sans-serif",
    "Bangers": "'Bangers', cursive",
    "Blaka": "'Blaka', cursive",
    "Bungee": "'Bungee', cursive",
    "Bungee Shade": "'Bungee Shade', cursive",
    "Cherry Bomb One": "'Cherry Bomb One', cursive",
    "Cinzel Decorative": "'Cinzel Decorative', serif",
    "Damion": "'Damion', cursive",
    "Diplomata SC": "'Diplomata SC', cursive",
    "Fascinate": "'Fascinate', cursive",
    "Joti One": "'Joti One', cursive",
    "Libertinus Keyboard": "'Libertinus Keyboard', serif",
    "MedievalSharp": "'MedievalSharp', cursive",
    "Michroma": "'Michroma', sans-serif",
    "New Rocker": "'New Rocker', cursive",
    "Rubik Wet Paint": "'Rubik Wet Paint', cursive",
    "Spicy Rice": "'Spicy Rice', cursive",
    "Story Script": "'Story Script', cursive",
}

INTERACTIVE_SCHEMA_EXTENSION = {
    vol.Optional(ATTR_ADD_BACK_BUTTON, default=False): cv.boolean,
    vol.Optional(ATTR_CLICK_ANYWHERE_TO_RETURN, default=False): cv.boolean,
    vol.Optional(ATTR_CLICK_ANYWHERE_TO_ACTION, default=False): cv.boolean,
    vol.Optional(ATTR_BACK_BUTTON_URL): cv.string,
    vol.Optional(ATTR_ACTION_WEBHOOK_ID): cv.string,
    vol.Optional(ATTR_ACTION_WEBHOOK_2_ID): cv.string,
    vol.Optional(ATTR_SCREEN_SIZE, default="joan6"): vol.In(["joan6", "joan13"]),
    vol.Optional(ATTR_AUTO_RETURN_SECONDS, default=0): vol.Coerce(int),
}

SERVICE_DEVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): vol.Any(cv.string, [cv.string]),
})

SERVICE_SET_URL_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): vol.Any(cv.string, [cv.string]),
    vol.Optional(ATTR_URL): cv.string,
    vol.Optional(ATTR_PREDEFINED_URL): cv.string,
})

SERVICE_SEND_TEXT_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): vol.Any(cv.string, [cv.string]),
    vol.Required(ATTR_MESSAGE): cv.template,
    vol.Optional(ATTR_TEXT_COLOR, default="black"): vol.In(EINK_COLORS),
    vol.Optional(ATTR_BACKGROUND_COLOR, default="white"): vol.In(EINK_COLORS),
    vol.Optional(ATTR_TEXT_SIZE, default=28): vol.All(vol.Coerce(int), vol.Range(min=10, max=150)),
    vol.Optional(ATTR_TEXT_ALIGN, default="center"): vol.In(["left", "center", "right"]),
    vol.Optional(ATTR_FONT_FAMILY, default="Modern"): vol.In(list(THEMED_FONTS.keys())),
    vol.Optional(ATTR_FONT_WEIGHT, default="normal"): vol.In(FONT_WEIGHTS),
    vol.Optional(ATTR_LAYOUT, default="text_only"): vol.In(LAYOUT_OPTIONS),
    vol.Optional(ATTR_IMAGE_URL): cv.string,
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=10, max=200)),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SET_DISPLAY_ROTATION_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): vol.Any(cv.string, [cv.string]),
    vol.Required(ATTR_DISPLAY_ROTATION): vol.In(list(DISPLAY_ROTATIONS.keys())),
})

SERVICE_SLEEP_DEVICE_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional(ATTR_DURATION, default=3600): vol.All(vol.Coerce(int), vol.Range(min=1)),
})

SERVICE_SEND_QR_CODE_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_DATA): cv.string,
    vol.Optional(ATTR_MESSAGE, default=""): cv.string,
    vol.Optional(ATTR_QR_MESSAGE_TEXT_SIZE, default=24): vol.All(vol.Coerce(int), vol.Range(min=10, max=100)),
    vol.Optional(ATTR_QR_MESSAGE_POSITION, default="below"): vol.In(["below", "above"]),
    vol.Optional(ATTR_BOX_SIZE, default=10): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
    vol.Optional(ATTR_BORDER, default=4): vol.All(vol.Coerce(int), vol.Range(min=0, max=10)),
    vol.Optional(ATTR_FILL_COLOR, default="black"): vol.In(EINK_COLORS),
    vol.Optional(ATTR_BACK_COLOR, default="white"): vol.In(EINK_COLORS),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_CALENDAR_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_CALENDAR_ENTITY): vol.Any(cv.entity_id, cv.entity_ids),
    vol.Optional(ATTR_DURATION_DAYS, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
    vol.Optional(ATTR_DISPLAY_STYLE, default="modern"): vol.In(["modern", "minimalist", "monthly_grid", "weather_calendar"]),
    vol.Optional(ATTR_WEATHER_ENTITY): cv.entity_id,
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_WEATHER_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_WEATHER_ENTITY): cv.entity_id,
    vol.Optional(ATTR_LAYOUT, default="detailed_summary"): vol.In([
        "detailed_summary", "daily_forecast_list", "weather_graph_panel"
    ]),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_ENERGY_PANEL_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional(ATTR_POWER_USAGE_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_CONSUMPTION_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_PRODUCTION_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_GRID_IMPORT_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_GRID_EXPORT_ENTITY): cv.entity_id,
    vol.Optional(ATTR_ENERGY_THEME, default="classic"): vol.In(["classic", "eink_donut"]),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_TODO_LIST_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_TODO_ENTITY): cv.entity_id,
    vol.Optional(ATTR_TITLE): cv.string,
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_CAMERA_SNAPSHOT_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_CAMERA_ENTITY): cv.entity_id,
    vol.Optional(ATTR_CAPTION): cv.template,
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=10, max=200)),
    vol.Optional(ATTR_DISPLAY_ROTATION, default="0"): vol.In(["0", "90", "180", "270"]),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_STATUS_PANEL_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional(ATTR_TITLE, default="Status Panel"): cv.string,
    vol.Required(ATTR_ENTITIES): cv.entity_ids,
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_SENSOR_GRAPH_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_ENTITIES): cv.entity_ids,
    vol.Optional(ATTR_DURATION_HOURS, default=24): vol.All(vol.Coerce(int), vol.Range(min=1, max=48)),
    vol.Optional(ATTR_GRAPH_TYPE, default="line"): vol.In(["line", "bar"]),
    vol.Optional(ATTR_SHOW_POINTS, default=False): cv.boolean,
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=10, max=200)),
    vol.Optional(ATTR_DISPLAY_ROTATION, default="0"): vol.In(["0", "90", "180", "270"]),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_RSS_FEED_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required("feed_url"): cv.url,
    vol.Optional("title", default="News"): cv.string,
    vol.Optional("max_items", default=5): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_CLEAR_WEB_CACHE_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional("restart_session", default=False): cv.boolean,
})

SERVICE_START_SLIDESHOW_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required("views"): vol.Any([cv.string], cv.string),
    vol.Optional("seconds_per_slide", default=30): vol.All(vol.Coerce(int), vol.Range(min=3, max=3600)),
    vol.Optional("loop", default=True): cv.boolean,
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_IMAGE_URL_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_IMAGE_URL): cv.string,
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=10, max=200)),
    vol.Optional(ATTR_DISPLAY_ROTATION, default="0"): vol.In(["0", "90", "180", "270"]),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SET_SESSION_OPTIONS_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional("encoding"): cv.string,
    vol.Optional("dithering"): cv.string,
})

SERVICE_SEND_KEYPAD_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_TITLE, default="Enter PIN"): cv.string,
    vol.Required(ATTR_ACTION_WEBHOOK_ID): cv.string,
})

BUTTON_PANEL_SCHEMA_DICT = {
    vol.Optional("title"): vol.Any(None, cv.string),
    **INTERACTIVE_SCHEMA_EXTENSION,
}
for i in range(1, 13):
    BUTTON_PANEL_SCHEMA_DICT[vol.Optional(f"button_{i}_webhook_id")] = cv.string
    BUTTON_PANEL_SCHEMA_DICT[vol.Optional(f"button_{i}_name")] = cv.string
    BUTTON_PANEL_SCHEMA_DICT[vol.Optional(f"button_{i}_icon")] = cv.string

SERVICE_SEND_BUTTON_PANEL_SCHEMA = SERVICE_DEVICE_SCHEMA.extend(BUTTON_PANEL_SCHEMA_DICT)

SERVICE_SEND_CRYPTO_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_COINS): [cv.string],  # CoinGecko IDs or common symbols: ["bitcoin","ETH"]
    vol.Optional(ATTR_VS_CURRENCY, default="usd"): cv.string,  # e.g. usd, eur, pln
    vol.Optional(ATTR_HISTORY_HOURS, default=24): vol.All(vol.Coerce(int), vol.Range(min=0, max=168)),
    vol.Optional(ATTR_SHOW_HEADER, default=True): cv.boolean,
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_APPLY_SAFE_DEVICE_CONFIG_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional(ATTR_HEART_BEAT_INTERVAL, default="3"): vol.In([str(v) for v in SAFE_HEART_BEAT_OPTIONS]),
    vol.Optional(ATTR_SYSTEM_SCREENS): vol.In(["0", "1", "2", "3"]),
    vol.Optional(ATTR_TOUCH_MODE): vol.In(["0", "1", "3"]),
})

def _schedule_media_cleanup(hass: HomeAssistant) -> None:
    interval_h = max(1, int(hass.data[DOMAIN]["cleanup_interval_hours"]))
    async def _periodic_cleanup(now=None):
        await _async_cleanup_media_files(hass)
    hass.async_create_task(_periodic_cleanup())
    async_track_time_interval(hass, _periodic_cleanup, timedelta(hours=interval_h))

async def _async_cleanup_media_files(hass: HomeAssistant) -> None:
    MEDIA_PREFIXES = ("visionect_snapshot_", "visionect_graph_")
    max_age_h = max(1, int(hass.data[DOMAIN]["cleanup_max_age_hours"]))
    cutoff = dt_util.utcnow() - timedelta(hours=max_age_h)
    
    paths_to_clean = [Path(hass.config.path("www"))]
    cache_path = Path(hass.config.path(f"www/{CACHE_DIR_NAME}"))
    if cache_path.exists():
        paths_to_clean.append(cache_path)

    def _cleanup():
        removed = 0
        for directory in paths_to_clean:
            if not directory.exists():
                continue
            for p in directory.iterdir():
                if not p.is_file():
                    continue
                if directory.name == "www" and not p.name.startswith(MEDIA_PREFIXES):
                    continue
                try:
                    mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
                    if mtime < cutoff:
                        p.unlink(missing_ok=True)
                        removed += 1
                except Exception:
                    continue
        return removed
    
    removed = await hass.async_add_executor_job(_cleanup)
    if isinstance(removed, int) and removed > 0:
        _LOGGER.info("Visionect cleanup: removed %s old media/cache files.", removed)

async def _process_final_url(hass: HomeAssistant, url: str) -> str:
    if len(url) <= URL_LENGTH_LIMIT and not url.startswith("data:text/html,"):
        return url
    
    if not url.startswith("data:text/html,"):
        return url
        
    try:
        encoded_content = url[len("data:text/html,"):]
        html_content = urllib.parse.unquote(encoded_content)
        content_hash = hashlib.md5(html_content.encode("utf-8")).hexdigest()
        filename = f"{content_hash}.html"
        www_path = Path(hass.config.path("www"))
        cache_dir = www_path / CACHE_DIR_NAME
        
        def _write_file():
            cache_dir.mkdir(parents=True, exist_ok=True)
            file_path = cache_dir / filename
            if not file_path.exists():
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
        
        await hass.async_add_executor_job(_write_file)
        
        try:
            base_url = get_internal_url(hass) if get_internal_url else get_url(hass)
        except Exception:
            base_url = get_url(hass)
            
        final_file_url = f"{base_url}/local/{CACHE_DIR_NAME}/{filename}"
        return create_simple_cache_buster(final_file_url)
    except Exception as e:
        _LOGGER.error("Failed to save HTML to file: %s", e)
        return url

async def _is_low_battery_cache_screen(hass: HomeAssistant, url: str) -> bool:
    """Best-effort detection of generated low-battery cache screen."""
    try:
        parsed = urllib.parse.urlparse(url or "")
        path = parsed.path or ""
        if f"/local/{CACHE_DIR_NAME}/" not in path or not path.endswith(".html"):
            return False

        filename = Path(path).name
        file_path = Path(hass.config.path("www")) / CACHE_DIR_NAME / filename
        if not file_path.exists():
            return False

        def _read_text() -> str:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        html_text = await hass.async_add_executor_job(_read_text)
        markers = (
            "LOW BATTERY",
            "NISKI POZIOM BATERII",
            "Please connect charger.",
            "Podłącz ładowarkę.",
        )
        return any(m in html_text for m in markers)
    except Exception:
        return False

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN in config: hass.data[DOMAIN]["yaml_config"] = config[DOMAIN]
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Starting setup of Visionect Joan config entry.")
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    yaml_config = hass.data[DOMAIN].get("yaml_config", {})
    views_data_from_options = entry.options.get(CONF_VIEWS, [])
    views = _parse_views(views_data_from_options)
    if not views:
        views = yaml_config.get("views", [])

    main_menu = entry.options.get(CONF_MAIN_MENU_URL, yaml_config.get("main_menu_url"))
    cleanup_age = entry.options.get(CONF_CLEANUP_MAX_AGE, yaml_config.get("cleanup_max_age_hours", 24))
    cleanup_interval = entry.options.get(CONF_CLEANUP_INTERVAL, yaml_config.get("cleanup_interval_hours", 6))
    ollama_enabled = bool(entry.options.get(CONF_OLLAMA_ENABLED, False))
    ollama_url = str(entry.options.get(CONF_OLLAMA_URL, "http://127.0.0.1:11434")).strip()
    ollama_api_key = str(entry.options.get(CONF_OLLAMA_API_KEY, "")).strip()
    ollama_model = str(entry.options.get(CONF_OLLAMA_MODEL, "llama3.1:8b")).strip()
    ollama_interval_min = int(entry.options.get(CONF_OLLAMA_INTERVAL_MIN, 10))



    hass.data[DOMAIN]["views"] = views
    hass.data[DOMAIN]["main_menu_url"] = main_menu
    hass.data[DOMAIN]["cleanup_max_age_hours"] = cleanup_age
    hass.data[DOMAIN]["cleanup_interval_hours"] = cleanup_interval
    hass.data[DOMAIN]["tablet_language"] = entry.options.get(CONF_TABLET_LANGUAGE, "auto")

    _schedule_media_cleanup(hass)

    api = VisionectAPI(
        hass,
        entry.data[CONF_HOST],
        entry.data.get(CONF_USERNAME),
        entry.data.get(CONF_PASSWORD),
        entry.data.get(CONF_API_KEY),
        entry.data.get(CONF_API_SECRET),
    )
    if not await api.async_test_authentication():
        _LOGGER.error("Authentication failed. Cannot load integration.")
        return False

    # Used to tune WebKit/HA warm-up delays after hassio.host_reboot (HA + VSS on same host).
    entry_setup_utc = dt_util.utcnow()

    guard_state = hass.data[DOMAIN].setdefault("guard_state", {
        "low_battery_notified": set(),
        "low_battery_tablet_alerted": set(),
        "full_charge_notified": set(),
        "offline_notified": set(),
        "last_seen": {},
        "low_battery_prev_url": {},
        "low_battery_svg_next_alt": {},
    })
    guard_state.setdefault("low_battery_svg_next_alt", {})

    async def async_update_data():
        try:
            # Pobierz listę wszystkich urządzeń
            devices_summary = await api.async_get_all_devices()
            if not devices_summary:
                return {}
            
            # Pobierz listę orphans (problematycznych sesji)
            orphans = await api.async_get_orphans()
            
            data = {}
            for device_entry in devices_summary:
                if isinstance(device_entry, str):
                    uuid_val = str(device_entry).strip().rstrip("/")
                    device_details = await api.async_get_device_data(uuid_val)
                else:
                    uuid_val = str(device_entry.get("Uuid", "")).strip().rstrip("/")
                    device_details = device_entry

                if not uuid_val or not device_details: continue

                # ALWAYS fetch the full device data to merge it with SessionOptions
                device_details = await api.async_get_device_data(uuid_val)
                if not device_details: continue

                # Dodaj informację o orphan status
                if uuid_val in orphans:
                     device_details["OrphanError"] = orphans[uuid_val]
                else:
                     device_details["OrphanError"] = None

                # Status urządzenia - dokumentacja Visionect definiuje tylko: online/offline
                state_val = device_details.get("State", "").lower()
                is_online = state_val == "online"
                
                now_utc = datetime.now(timezone.utc)
                if is_online:
                    guard_state["last_seen"][uuid_val] = now_utc
                    if uuid_val in guard_state["offline_notified"]:
                        guard_state["offline_notified"].discard(uuid_val)
                elif uuid_val not in guard_state["last_seen"]:
                    # Inicjalizacja czasu "od startu HA", jeśli tablet nie był online
                    guard_state["last_seen"][uuid_val] = now_utc

                device_name = device_details.get("Options", {}).get("Name") or f"Device {uuid_val}"

                # Battery guards (threshold 5/10/15 % and optional tablet / HA notifications)
                try:
                    battery = device_details.get("Status", {}).get("Battery")
                    if battery is not None:
                        batt_val = float(battery)
                        status_data = device_details.get("Status", {}) or {}
                        is_charging_raw = str(status_data.get("IsCharging", "")).strip().lower()
                        charger_raw = str(status_data.get("Charger", "")).strip().lower()
                        is_charging = (
                            is_charging_raw in {"1", "true", "yes", "on", "charging"}
                            or charger_raw in {"1", "true", "yes", "on", "charging", "ac", "usb", "plugged", "plugged_in"}
                        )

                        _opts = entry.options
                        battery_low_thr = float(_opts.get(CONF_BATTERY_LOW_THRESHOLD_PCT, 10))
                        battery_tablet_on = bool(_opts.get(CONF_BATTERY_TABLET_ALERT_ENABLED, True))
                        battery_ha_low_on = bool(_opts.get(CONF_BATTERY_HA_LOW_NOTIFICATION_ENABLED, True))
                        battery_ha_full_on = bool(_opts.get(CONF_BATTERY_HA_FULL_NOTIFICATION_ENABLED, True))
                        battery_clear_threshold = max(20.0, battery_low_thr + 5.0)

                        if battery_ha_low_on and batt_val <= battery_low_thr:
                            if uuid_val not in guard_state["low_battery_notified"]:
                                _LOGGER.info(
                                    "Battery guard (HA notify) for %s (<=%s%%)",
                                    device_name,
                                    int(battery_low_thr),
                                )
                                guard_state["low_battery_notified"].add(uuid_val)
                                try:
                                    nlang = _tablet_notify_lang(hass)
                                    notif_msg = ntr(
                                        nlang,
                                        "battery_low_message",
                                        device_name=device_name,
                                        pct=batt_val,
                                    )
                                    notif_title = ntr(nlang, "battery_low_title")
                                    async_create_persistent_notification(
                                        hass,
                                        notif_msg,
                                        title=notif_title,
                                        notification_id=f"visionect_battery_{uuid_val}",
                                    )
                                except Exception as notify_err:
                                    _LOGGER.debug(
                                        "Could not create low-battery persistent notification for %s: %s",
                                        device_name,
                                        notify_err,
                                    )

                        # Full-screen low battery on tablet (alternating battery.svg / battery2.svg)
                        if battery_tablet_on and batt_val <= battery_low_thr:
                            if uuid_val not in guard_state["low_battery_tablet_alerted"]:
                                prev_url = str(device_details.get("Config", {}).get("Url", "")).strip()
                                if prev_url:
                                    guard_state["low_battery_prev_url"][uuid_val] = prev_url

                                nlang = _tablet_notify_lang(hass)
                                low_batt_msg = (
                                    f"{ntr(nlang, 'battery_tablet_heading')}\n\n"
                                    f"{device_name}\n"
                                    f"{ntr(nlang, 'battery_tablet_battery', pct=batt_val)}\n\n"
                                    f"{ntr(nlang, 'battery_tablet_footer')}"
                                )

                                svg_alt = guard_state["low_battery_svg_next_alt"]
                                use_b2 = bool(svg_alt.get(uuid_val, False))
                                svg_name = "battery2.svg" if use_b2 else "battery.svg"
                                svg_alt[uuid_val] = not use_b2

                                battery_icon_url = await async_get_icon_as_base64(hass, svg_name)
                                low_batt_url = create_text_message_url(
                                    message=low_batt_msg,
                                    text_color="black",
                                    background_color="white",
                                    text_size="44px",
                                    text_align="center",
                                    font_family_key="Readable",
                                    font_weight="bold",
                                    layout="image_top",
                                    image_url=battery_icon_url,
                                    image_zoom=50,
                                    screen_size=get_effective_screen_size(
                                        hass, entry.entry_id, uuid_val, device_details
                                    ),
                                )
                                final_low_batt_url = await _process_final_url(hass, low_batt_url)
                                await api.async_set_device_url(uuid_val, final_low_batt_url)
                                guard_state["low_battery_tablet_alerted"].add(uuid_val)
                        elif battery_tablet_on and (batt_val >= battery_clear_threshold or is_charging):
                            if uuid_val in guard_state["low_battery_tablet_alerted"]:
                                guard_state["low_battery_tablet_alerted"].discard(uuid_val)
                                prev_url = guard_state["low_battery_prev_url"].pop(uuid_val, None)
                                if prev_url:
                                    await api.async_set_device_url(uuid_val, prev_url)

                        # Safety-net after HA restart: if alert screen is still displayed at high battery,
                        # restore a sensible fallback target even when in-memory state was lost.
                        if batt_val >= 30.0:
                            current_url = str(device_details.get("Config", {}).get("Url", "")).strip()
                            if current_url and await _is_low_battery_cache_screen(hass, current_url):
                                restore_url = guard_state["low_battery_prev_url"].get(uuid_val)
                                if not restore_url:
                                    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
                                    prefs = entry_data.get("prefs", {})
                                    restore_url = prefs.get("back_targets", {}).get(uuid_val) or entry_data.get("main_menu_url")
                                if not restore_url:
                                    restore_url = main_menu
                                if restore_url:
                                    _LOGGER.info("Restoring view for %s after stale low-battery screen.", device_name)
                                    await api.async_set_device_url(uuid_val, restore_url)
                                    guard_state["low_battery_tablet_alerted"].discard(uuid_val)
                                    guard_state["low_battery_prev_url"].pop(uuid_val, None)

                        # Notify when battery is full while still charging (one-time until unplugged)
                        if battery_ha_full_on and batt_val >= 90.0 and is_charging:
                            if uuid_val not in guard_state["full_charge_notified"]:
                                nlang = _tablet_notify_lang(hass)
                                full_msg = ntr(
                                    nlang,
                                    "battery_full_message",
                                    device_name=device_name,
                                    pct=batt_val,
                                )
                                full_title = ntr(nlang, "battery_full_title")
                                try:
                                    async_create_persistent_notification(
                                        hass,
                                        full_msg,
                                        title=full_title,
                                        notification_id=f"visionect_full_charge_{uuid_val}",
                                    )
                                except Exception as notify_err:
                                    _LOGGER.debug(
                                        "Could not create full-charge persistent notification for %s: %s",
                                        device_name,
                                        notify_err,
                                    )
                                guard_state["full_charge_notified"].add(uuid_val)
                        elif not is_charging or batt_val < 85.0:
                            if uuid_val in guard_state["full_charge_notified"]:
                                guard_state["full_charge_notified"].discard(uuid_val)

                        if batt_val >= battery_clear_threshold or is_charging:
                            if uuid_val in guard_state["low_battery_notified"]:
                                guard_state["low_battery_notified"].discard(uuid_val)
                except (ValueError, TypeError):
                    pass

                # Strażnik Połączenia (> 4h offline)
                offline_duration = now_utc - guard_state["last_seen"][uuid_val]
                if offline_duration > timedelta(hours=4):
                    if uuid_val not in guard_state["offline_notified"]:
                        _LOGGER.info(f"Connection guard triggered for {device_name} (>4h offline)")
                        guard_state["offline_notified"].add(uuid_val)
                        try:
                            olang = _tablet_notify_lang(hass)
                            async_create_persistent_notification(
                                hass,
                                ntr(olang, "offline_message", device_name=device_name),
                                title=ntr(olang, "offline_title"),
                                notification_id=f"visionect_offline_{uuid_val}",
                            )
                        except Exception as notify_err:
                            _LOGGER.debug(
                                "Could not create offline persistent notification for %s: %s",
                                device_name,
                                notify_err,
                            )
                
                # VSS sam zarządza urządzeniami przez DeviceStatePolling - nie wysyłaj niepotrzebnych TCLV
                # które mogą zakłócać pracę e-ink i zużywać baterię
                
                final_data = device_details
                if "Config" not in final_data: final_data["Config"] = {}
                if device_name and device_name.lower() not in UNKNOWN_STRINGS:
                    final_data["Config"]["Name"] = device_name
                final_data["Options"] = device_details.get("Options", {})
                final_data["LastUpdated"] = now_utc
                data[uuid_val] = final_data
            return data
        except Exception as e:
            _LOGGER.error(f"Error during data update: {e}")
            raise UpdateFailed(f"Connection to VSS failed: {e}")

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=f"visionect_{entry.entry_id}",
        update_method=async_update_data, update_interval=SCAN_INTERVAL
    )
    coordinator.config_entry = entry
    # POPRAWKA: Przypisujemy API do koordynatora, aby encje (np. Button) miały do niego dostęp
    coordinator.api = api
    
    await coordinator.async_config_entry_first_refresh()

    async def _async_gather_recovery_uuids(
        devices_list: list | None = None,
    ) -> list[str]:
        """Resolve device UUIDs for session restart; reuse API list when already fetched."""
        devices = (
            list(devices_list)
            if devices_list is not None
            else (await api.async_get_all_devices() or [])
        )
        uuids = _collect_recovery_uuids_from_device_list(devices)
        if not uuids and coordinator.data:
            uuids = []
            for u, d in coordinator.data.items():
                st = str(d.get("State", "")).strip().lower()
                if st == "offline":
                    continue
                if st == "online" or st == "":
                    uuids.append(u)
            uuids = list(dict.fromkeys(uuids))
            if uuids:
                _LOGGER.info(
                    "Recovery: using %d device(s) from coordinator (API list had no eligible UUIDs).",
                    len(uuids),
                )
        return uuids

    debounce_key = entry.entry_id

    async def _async_run_session_batch_recovery(
        uuids: list[str],
        warmup_s: int,
        log_ctx: str,
        *,
        respect_debounce: bool,
    ) -> bool:
        """Restart WebKit sessions on VSS (same effect as *force_refresh* for all listed UUIDs)."""
        if not uuids:
            return True
        deb = hass.data.setdefault(DOMAIN, {}).setdefault("_recovery_debounce", {})
        now_m = time.monotonic()
        if respect_debounce:
            last_m = deb.get(debounce_key, 0.0)
            if now_m - last_m < 90.0:
                _LOGGER.debug(
                    "%s: skip (recovery %.0fs ago)",
                    log_ctx,
                    now_m - last_m,
                )
                return True
        probe_url = _resolve_recovery_probe_url(entry, main_menu)
        if probe_url:
            probe_ok = await _async_wait_for_recovery_probe(
                hass, probe_url, log_ctx, total_timeout_s=240.0
            )
            # Short settle for WebKit / proxy; longer if probe never saw OK
            await asyncio.sleep(15 if probe_ok else min(warmup_s, 75))
        else:
            _LOGGER.info(
                "%s: waiting %ds, then restarting sessions for %d device(s)",
                log_ctx,
                warmup_s,
                len(uuids),
            )
            await asyncio.sleep(warmup_s)
        for u in uuids:
            await api.async_set_session_options(u, encoding="4")
        await asyncio.sleep(2)
        ok = await api.async_restart_sessions_batch(uuids)
        if ok:
            _LOGGER.info("%s: session batch restart OK (%d)", log_ctx, len(uuids))
            deb[debounce_key] = time.monotonic()
            await coordinator.async_request_refresh()
        else:
            _LOGGER.warning(
                "%s: session batch restart FAILED (%d) — tablets may keep HA connection error",
                log_ctx,
                len(uuids),
            )
        return ok

    # After hassio.host_reboot, VSS may respond before HA serves :8123; tablets load dashboard URL → connection refused.
    def _schedule_host_reboot_safety_net(delay_s: float, label: str):
        async def _cb(_now: datetime) -> None:
            if hass.is_stopping:
                return
            if hass.data.get(DOMAIN, {}).get(entry.entry_id) is None:
                return
            uuids = await _async_gather_recovery_uuids()
            if not uuids:
                _LOGGER.debug("HostRebootSafetyNet/%s: no UUIDs, skip", label)
                return
            age_s = (dt_util.utcnow() - entry_setup_utc).total_seconds()
            warm_s = 75 if age_s < 7200 else 45
            await _async_run_session_batch_recovery(
                uuids,
                warm_s,
                f"HostRebootSafetyNet/{label}",
                respect_debounce=True,
            )

        return async_call_later(hass, delay_s, _cb)

    # Staggered nets: early AppDaemon may be up while tablets lack Wi‑Fi (e.g. AdGuard/router flap).
    entry.async_on_unload(_schedule_host_reboot_safety_net(300, "5m"))
    entry.async_on_unload(_schedule_host_reboot_safety_net(480, "8m"))
    entry.async_on_unload(_schedule_host_reboot_safety_net(600, "10m"))

    # WATCHDOG: monitors VSS health; after outage (or first boot) restarts sessions when API is back.
    wd_state = {"quick_warmup": False}

    async def _async_vss_watchdog():
        """Watches VSS API and handles auto-restarts when VSS recovers."""
        vss_was_offline = True
        recovery_attempts_no_uuids = 0
        MAX_RECOVERY_ATTEMPTS_NO_UUIDS = 28  # 28 * 15s ≈ 7 min

        while True:
            try:
                await asyncio.sleep(15)

                is_healthy = await api.async_check_health()

                if is_healthy and vss_was_offline:
                    _LOGGER.info("VSS Watchdog: VSS is online; evaluating post-recovery session restart...")
                    devices = await api.async_get_all_devices() or []
                    uuids = await _async_gather_recovery_uuids(devices)

                    if uuids:
                        age_s = (dt_util.utcnow() - entry_setup_utc).total_seconds()
                        if wd_state["quick_warmup"]:
                            warm_s = 15
                        else:
                            # Longer wait soon after config entry load (typical after full OS reboot + slow HA bind).
                            warm_s = 105 if age_s < 2700 else 50
                        ok = await _async_run_session_batch_recovery(
                            uuids,
                            warm_s,
                            "VSS Watchdog",
                            respect_debounce=False,
                        )
                        if ok:
                            vss_was_offline = False
                            recovery_attempts_no_uuids = 0
                            wd_state["quick_warmup"] = False
                        else:
                            wd_state["quick_warmup"] = True
                    elif not devices:
                        _LOGGER.debug("VSS Watchdog: no devices returned by API; clearing recovery flag.")
                        vss_was_offline = False
                        recovery_attempts_no_uuids = 0
                        wd_state["quick_warmup"] = False
                    else:
                        recovery_attempts_no_uuids += 1
                        if recovery_attempts_no_uuids >= MAX_RECOVERY_ATTEMPTS_NO_UUIDS:
                            _LOGGER.warning(
                                "VSS Watchdog: no UUIDs for session restart after %d attempts; clearing recovery flag.",
                                recovery_attempts_no_uuids,
                            )
                            vss_was_offline = False
                            recovery_attempts_no_uuids = 0
                            wd_state["quick_warmup"] = False
                        else:
                            _LOGGER.info(
                                "VSS Watchdog: no UUIDs for restart yet (%d/%d); keeping recovery pending.",
                                recovery_attempts_no_uuids,
                                MAX_RECOVERY_ATTEMPTS_NO_UUIDS,
                            )

                elif not is_healthy:
                    if not vss_was_offline:
                        _LOGGER.warning("VSS Watchdog: VSS went offline. Waiting for recovery...")
                    vss_was_offline = True
                    recovery_attempts_no_uuids = 0
                    wd_state["quick_warmup"] = False

            except asyncio.CancelledError:
                break
            except Exception as e:
                if not vss_was_offline:
                    _LOGGER.warning(f"VSS Watchdog connection error: {e}")
                vss_was_offline = True
                recovery_attempts_no_uuids = 0
                wd_state["quick_warmup"] = False

    entry.async_create_background_task(hass, _async_vss_watchdog(), "visionect_vss_watchdog")

    store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}_prefs.json")
    prefs = await store.async_load() or {}
    if not isinstance(prefs, dict):
        prefs = {}
    prefs.setdefault("back_targets", {})
    prefs.setdefault("screen_size_by_uuid", {})

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "prefs_store": store,
        "prefs": prefs,
        "views": views,
        "main_menu_url": main_menu,
        "tablet_language": entry.options.get(CONF_TABLET_LANGUAGE, "auto"),
        "safe_config_state": {"last_read": {}, "last_backup": {}},
    }

    if ollama_enabled and ollama_url and ollama_model:
        # Prefer logs shipped with / copied into the component (logi/) so HA sees them without
        # host mounts; then add-on share and standard VSS paths (first non-empty file wins per name).
        log_dirs = [
            Path(__file__).resolve().parent / "logi",
            Path("/config/custom_components/visionect_joan/logi"),
            Path("/share/visionect/logs"),
            Path("/var/log/vss"),
        ]
        ai_state = {"running": False}
        ai_warned = {"missing_logs": False}
        ai_lang = resolve_tablet_content_lang(
            entry.options.get(CONF_TABLET_LANGUAGE, "auto"),
            getattr(hass.config, "language", None),
        )
        ai_title = ntr(ai_lang, "ollama_title")

        async def _async_ollama_tick(_now: datetime) -> None:
            if hass.is_stopping or ai_state["running"]:
                return
            ai_state["running"] = True
            try:
                extra_sections: list[str] = []
                # Readable roster from Visionect Management API (/api/device, /api/orphans).
                # Always attached so the model (and notification) see all devices, not only when log files are missing.
                try:
                    devices = await api.async_get_all_devices() or []
                    orphans = await api.async_get_orphans() or {}
                    api_text = _format_visionect_devices_for_ai(
                        devices, orphans, language=ai_lang, max_chars=12000
                    )
                    if api_text:
                        extra_sections.append(api_text)
                except Exception as api_err:
                    extra_sections.append(ntr(ai_lang, "ollama_api_error", err=api_err))
                analysis, context_excerpt = await _async_ollama_analyze_logs(
                    hass,
                    base_url=ollama_url,
                    model=ollama_model,
                    api_key=ollama_api_key or None,
                    log_dirs=log_dirs,
                    extra_sections=extra_sections,
                    language=ai_lang,
                )
                if analysis:
                    sep = ntr(ai_lang, "ollama_sep")
                    body = f"Model: `{ollama_model}`\n\n{analysis}\n\n{sep}\n{context_excerpt}"
                    async_create_persistent_notification(
                        hass,
                        body,
                        title=ai_title,
                        notification_id=f"{DOMAIN}_ollama_analysis_{entry.entry_id}",
                    )
                else:
                    if not ai_warned["missing_logs"]:
                        async_create_persistent_notification(
                            hass,
                            ntr(ai_lang, "ollama_no_data"),
                            title=ai_title,
                            notification_id=f"{DOMAIN}_ollama_analysis_{entry.entry_id}",
                        )
                        ai_warned["missing_logs"] = True
            except Exception as err:
                _LOGGER.warning("Ollama diagnostics failed: %s", err)
                async_create_persistent_notification(
                    hass,
                    ntr(ai_lang, "ollama_error", err=err),
                    title=ai_title,
                    notification_id=f"{DOMAIN}_ollama_analysis_{entry.entry_id}",
                )
            finally:
                ai_state["running"] = False

        remove_ai = async_track_time_interval(
            hass,
            _async_ollama_tick,
            timedelta(minutes=max(2, ollama_interval_min)),
        )
        entry.async_on_unload(remove_ai)

    device_reg = dr.async_get(hass)

    def _get_url_from_predefined(predefined_name: str | None) -> str | None:
        if not predefined_name: return None
        candidate = str(predefined_name).strip()
        if candidate.startswith(("http", "data:")): return candidate
        for view in views or []:
            if str(view.get("name", "")).strip().lower() == candidate.lower():
                return view.get("url")
        return None

    def _get_url_from_params(call_data: dict, url_key: str, predefined_key: str) -> str | None:
        direct_url = call_data.get(url_key)
        if direct_url:
            direct_url = str(direct_url).strip()
            if direct_url.startswith(("http", "data:")): return direct_url
            resolved = _get_url_from_predefined(direct_url)
            if resolved: return resolved
        return _get_url_from_predefined(call_data.get(predefined_key))

    def _get_prefs() -> dict:
        return hass.data[DOMAIN][entry.entry_id].setdefault(
            "prefs", {"back_targets": {}, "screen_size_by_uuid": {}}
        )

    def _get_back_url_for_uuid(device_uuid: str, call_data: dict) -> str | None:
        back_url = call_data.get(ATTR_BACK_BUTTON_URL)
        if back_url:
            if not back_url.startswith(("http", "data:")):
                resolved = _get_url_from_predefined(back_url)
                if resolved: return resolved
            return back_url
        prefs_local = _get_prefs()
        stored_url = prefs_local.get("back_targets", {}).get(device_uuid)
        if stored_url: return stored_url
        return main_menu

    def _effective_add_back_button(call: ServiceCall, back_url: str | None) -> bool:
        cd = call.data
        if cd.get(ATTR_CLICK_ANYWHERE_TO_RETURN) or cd.get(ATTR_CLICK_ANYWHERE_TO_ACTION): return False
        if cd.get(ATTR_ADD_BACK_BUTTON): return True
        if cd.get(ATTR_BACK_BUTTON_URL): return True
        if call.service == SERVICE_SEND_KEYPAD and cd.get(ATTR_ADD_BACK_BUTTON) and back_url: return True
        return False

    async def get_uuids_from_call(call: ServiceCall) -> list[str]:
        device_ids = call.data.get(ATTR_DEVICE_ID)
        if isinstance(device_ids, str): device_ids = [device_ids]
        if not device_ids: return []
        uuids_list = []
        for device_id in device_ids:
            device_entry = device_reg.async_get(device_id)
            if device_entry and (uuid_val := next((i[1] for i in device_entry.identifiers if i[0] == DOMAIN), None)):
                uuids_list.append(uuid_val)
        return uuids_list

    async def handle_set_url(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        original_url = _get_url_from_params(call.data, ATTR_URL, ATTR_PREDEFINED_URL)
        if not original_url:
            _LOGGER.error("No URL provided for set_url.")
            return
        
        final_url = await _process_final_url(hass, original_url)
        if not final_url.startswith("data:text/html,"):
            final_url = create_simple_cache_buster(final_url)
            
        tasks = [api.async_set_device_url(uuid, final_url) for uuid in uuids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, uuid_val in enumerate(uuids):
            status = "success" if results[i] is True else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SET_URL, "status": status})
        await coordinator.async_request_refresh()

    async def handle_send_text(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        message_template = call.data[ATTR_MESSAGE]
        if isinstance(message_template, Template): message_template.hass = hass
        message = message_template.async_render(parse_result=False) if isinstance(message_template, Template) else message_template
        
        img_url = call.data.get(ATTR_IMAGE_URL)
        if img_url and not api.validate_image_url(img_url):
            _LOGGER.warning(f"Invalid image URL provided for text message: {img_url}")
            img_url = None
            
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        
        content_url = create_text_message_url(
            message,
            call.data.get(ATTR_TEXT_COLOR, "black"),
            call.data.get(ATTR_BACKGROUND_COLOR, "white"),
            f"{call.data.get(ATTR_TEXT_SIZE, 28)}px",
            call.data.get(ATTR_TEXT_ALIGN, "center"),
            call.data.get(ATTR_FONT_FAMILY, "Modern"),
            call.data.get(ATTR_FONT_WEIGHT, "normal"),
            call.data.get(ATTR_LAYOUT, "text_only"),
            img_url,
            call.data.get(ATTR_IMAGE_ZOOM, 100),
            0, # image_rotation
            screen_size
        )
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_TEXT, "status": status})

    async def handle_send_weather(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        weather_entity_id = call.data[ATTR_WEATHER_ENTITY]
        layout = call.data[ATTR_LAYOUT]
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, call.data.get(ATTR_SMALL_SCREEN) and "joan6" or "joan6")
        for device_uuid in uuids:
            device_data = coordinator.data.get(device_uuid, {})
            orientation = str(device_data.get("Config", {}).get("DisplayRotation", "0"))
            weather_state = hass.states.get(weather_entity_id)
            if not weather_state: continue
            
            daily_forecast, hourly_forecast = None, None
            try:
                dr = await hass.services.async_call("weather", "get_forecasts", {"entity_id": weather_entity_id, "type": "daily"}, blocking=True, return_response=True)
                if dr: daily_forecast = dr.get(weather_entity_id, {}).get("forecast", [])
            except Exception: pass
            
            try:
                hr = await hass.services.async_call("weather", "get_forecasts", {"entity_id": weather_entity_id, "type": "hourly"}, blocking=True, return_response=True)
                if hr: hourly_forecast = hr.get(weather_entity_id, {}).get("forecast", [])
            except Exception: pass

            content_url = await create_weather_url(hass, weather_state, daily_forecast, hourly_forecast, layout, orientation, lang, screen_size)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_WEATHER, "status": status})

    async def handle_send_energy_panel(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        entity_states = {key: hass.states.get(entity_id) for key, entity_id in call.data.items() if key.endswith("_entity") and entity_id}
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        energy_theme = call.data.get(ATTR_ENERGY_THEME, "classic")
        for device_uuid in uuids:
            orientation = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_energy_panel_url(hass, entity_states, orientation, lang, screen_size, theme=energy_theme)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_ENERGY_PANEL, "status": status})

    async def handle_send_todo_list(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        todo_entity_id, title = call.data[ATTR_TODO_ENTITY], call.data.get(ATTR_TITLE)
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        if not title:
            st = hass.states.get(todo_entity_id)
            title = st.name if st else "To-Do List"
        items = []
        try:
            resp = await hass.services.async_call("todo", "get_items", {"entity_id": todo_entity_id}, blocking=True, return_response=True)
            if resp:
                raw = resp.get(todo_entity_id, {}).get("items", [])
                items = [{'summary': i.get('summary'), 'status': i.get('status'), 'uid': i.get('uid')} for i in raw]
        except Exception: pass
        
        for device_uuid in uuids:
            orientation = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_todo_list_url(hass, title, items, lang, orientation, screen_size)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_TODO_LIST, "status": status})

    async def handle_send_rss_feed(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        feed_url, title, max_items = call.data["feed_url"], call.data.get("title", "News"), call.data.get("max_items", 5)
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        
        def _parse():
            try:
                f = feedparser.parse(feed_url)
                return [{"title": e.title} for e in f.entries[:max_items]]
            except Exception: return []
            
        items = await hass.async_add_executor_job(_parse)
        content_url = await create_rss_feed_url(hass, title, items, lang, screen_size)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_RSS_FEED, "status": status})

    async def handle_send_status_panel(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        title, entity_ids = call.data.get(ATTR_TITLE, "Status Panel"), call.data[ATTR_ENTITIES]
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        
        for device_uuid in uuids:
            orientation = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_status_panel_url(hass, title, entity_ids, lang, orientation, screen_size)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_STATUS_PANEL, "status": status})

    async def handle_set_display_rotation(call: ServiceCall):
        uuids, rotation = await get_uuids_from_call(call), call.data[ATTR_DISPLAY_ROTATION]
        for uuid_val in uuids:
            status = "failure"
            if await api.async_set_display_rotation(uuid_val, rotation) and await api.async_reboot_device(uuid_val):
                status = "success"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SET_DISPLAY_ROTATION, "status": status})
        await coordinator.async_request_refresh()

    async def handle_force_refresh(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        status = "failure"
        if await api.async_restart_sessions_batch(uuids): status = "success"
        for uuid_val in uuids:
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_FORCE_REFRESH, "status": status})

    async def handle_clear_display(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        blank_url = "data:text/html,<html><body style='background-color:white;'></body></html>"
        for uuid_val in uuids:
            status = "success" if await api.async_set_device_url(uuid_val, blank_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_CLEAR_DISPLAY, "status": status})

    async def handle_sleep_device(call: ServiceCall):
        uuids, duration = await get_uuids_from_call(call), call.data[ATTR_DURATION]
        sleep_url = f"data:text/html,<html><script>window.VECT = window.VECT || {{}}; window.VECT.setSleep({duration});</script></html>"
        for uuid_val in uuids:
            status = "success" if await api.async_set_device_url(uuid_val, sleep_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SLEEP_DEVICE, "status": status})

    async def handle_wake_device(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        wake_url = "data:text/html,<html><script>window.VECT = window.VECT || {}; window.VECT.setSleep(0);</script></html>"
        for uuid_val in uuids:
            status = "success" if await api.async_set_device_url(uuid_val, wake_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_WAKE_DEVICE, "status": status})

    async def handle_send_qr_code(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        try:
            content_url = create_qr_code_url(
                qr_data=call.data[ATTR_DATA], message=call.data.get(ATTR_MESSAGE, ""),
                qr_message_text_size=call.data.get(ATTR_QR_MESSAGE_TEXT_SIZE, 24), qr_message_position=call.data.get(ATTR_QR_MESSAGE_POSITION, "below"),
                box_size=call.data.get(ATTR_BOX_SIZE, 10), border=call.data.get(ATTR_BORDER, 4),
                fill_color=call.data.get(ATTR_FILL_COLOR, "black"), back_color=call.data.get(ATTR_BACK_COLOR, "white"),
                screen_size=screen_size
            )
        except Exception: return
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_QR_CODE, "status": status})

    async def handle_send_calendar(call: ServiceCall):
        """Handle send_calendar service with multi-calendar support."""
        uuids = await get_uuids_from_call(call)
        
        # ✅ ZMIANA: Pobierz calendar_entity (może być string lub lista)
        calendar_entity_raw = call.data.get(ATTR_CALENDAR_ENTITY)
        
        # Normalizuj do listy
        if isinstance(calendar_entity_raw, str):
            calendar_entities = [calendar_entity_raw]
        elif isinstance(calendar_entity_raw, list):
            calendar_entities = calendar_entity_raw
        else:
            _LOGGER.error("calendar_entity must be a string or list")
            return
        
        duration_days = call.data.get(ATTR_DURATION_DAYS, 1)
        display_style = call.data.get(ATTR_DISPLAY_STYLE, "modern")
        screen_size = call.data.get(ATTR_SCREEN_SIZE, call.data.get(ATTR_SMALL_SCREEN) and "joan6" or "joan6")
        
        # ✅ ZMIANA: Zbierz eventy z WSZYSTKICH kalendarzy RÓWNOLEGLE dla szybkości
        async def fetch_calendar_events(cal_entity):
            try:
                start = datetime.now(timezone.utc)
                end = start + timedelta(days=duration_days)
                
                events_response = await hass.services.async_call(
                    "calendar", "get_events",
                    {"entity_id": cal_entity, "start_date_time": start.isoformat(), "end_date_time": end.isoformat()},
                    blocking=True, return_response=True,
                )
                
                raw_events = events_response.get(cal_entity, {}).get("events", [])
                
                def normalize_to_aware_dt(val):
                    if val is None: return None
                    dt_out = None
                    if isinstance(val, dict):
                        s = val.get('dateTime') or val.get('date')
                        if s:
                            try: dt_out = dt_util.parse_datetime(s)
                            except: pass
                            if dt_out is None:
                                try: 
                                    d = dt_util.parse_date(s)
                                    if d: dt_out = datetime.combine(d, datetime.min.time())
                                except: pass
                    elif isinstance(val, datetime):
                        dt_out = val
                    elif isinstance(val, date):
                        dt_out = datetime.combine(val, datetime.min.time())
                    elif isinstance(val, str):
                        try: dt_out = dt_util.parse_datetime(val)
                        except: pass
                        if dt_out is None:
                            try: 
                                d = dt_util.parse_date(val)
                                if d: dt_out = datetime.combine(d, datetime.min.time())
                            except: pass
                    if dt_out:
                        if dt_out.tzinfo is None:
                            dt_out = dt_out.replace(tzinfo=timezone.utc)
                        return dt_out
                    return None

                parsed_events = []
                for event in raw_events:
                    if not isinstance(event, dict): continue
                    event['start'] = normalize_to_aware_dt(event.get('start'))
                    event['end'] = normalize_to_aware_dt(event.get('end'))
                    if event['start'] is not None:
                        parsed_events.append(event)
                _LOGGER.debug(f"Fetched {len(parsed_events)} events from {cal_entity}")
                return parsed_events
            except Exception as e:
                _LOGGER.error(f"Failed to fetch events from {cal_entity}: {e}")
                return []

        results = await asyncio.gather(*(fetch_calendar_events(cal) for cal in calendar_entities))
        
        all_events = []
        for event_list in results:
            all_events.extend(event_list)
        
        # ✅ ZMIANA: Sortuj wszystkie eventy po czasie
        def get_event_start(event):
            """Extract start datetime from event for sorting."""
            start_val = event.get("start")
            if isinstance(start_val, datetime):
                # Jeśli datetime nie ma timezone, dodaj UTC
                if start_val.tzinfo is None:
                    return start_val.replace(tzinfo=timezone.utc)
                return start_val
            return datetime.min.replace(tzinfo=timezone.utc)
        
        all_events.sort(key=get_event_start)
        
        # ✅ ZMIANA: Selektywne limity wydarzeń
        # Modern: 6 (default)
        if display_style == "modern":
            all_events = all_events[:6]
        # Minimalist: Wyświetlaj więcej (np. miesięczny widok), limit bezpieczeństwa 50
        elif display_style == "minimalist":
            all_events = all_events[:50]
        # Dla weather_calendar limit ustawiany jest niżej w wywołaniu create_weather_calendar_url (max_events=5)
        # Dla monthly_grid pokazujemy wszystko (bez slice)
        
        _LOGGER.info(f"Total merged events: {len(all_events)} for style {display_style} from {len(calendar_entities)} calendars")
        
        # RESZTA BEZ ZMIAN - generuj URL normalnie
        lang = _get_lang(hass)
        
        daily_forecast = None
        
        if display_style == "monthly_grid":
            today = datetime.now()
            year = today.year
            month = today.month
            
            content_url = create_monthly_calendar_url(
                year, month, all_events, lang=lang, screen_size=screen_size
            )
        elif display_style == "weather_calendar":
            # ✅ NOWA FUNKCJONALNOŚĆ: Kalendarz z pogodą
            weather_entity_id = call.data.get(ATTR_WEATHER_ENTITY)
            if not weather_entity_id:
                _LOGGER.warning("weather_calendar style requires weather_entity parameter, falling back to 'modern'")
                content_url = create_calendar_url(all_events, style="modern", lang=lang, screen_size=screen_size)
            else:
                # Pobierz prognozę pogody przez service call (raz dla wszystkich)
                daily_forecast = []
                try:
                    dr = await hass.services.async_call(
                        "weather", "get_forecasts", 
                        {"entity_id": weather_entity_id, "type": "daily"}, 
                        blocking=True, return_response=True
                    )
                    if dr and weather_entity_id in dr:
                        auths = dr[weather_entity_id].get("forecast", [])
                        daily_forecast = [f for f in auths if f.get("is_daytime", True)][:5]
                    else:
                        _LOGGER.warning(f"No forecast data for {weather_entity_id}")
                except Exception as e:
                    _LOGGER.warning(f"Failed to get weather forecast: {e}")
                
                # Content URL generated dynamically inside loop
                content_url = None 
        else:
            content_url = create_calendar_url(all_events, style=display_style, lang=lang, screen_size=screen_size)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            
            # Dla weather calendar generujemy URL dynamicznie per urządzenie
            current_content_url = content_url
            if display_style == "weather_calendar": 
                if daily_forecast is not None:
                    max_events = 5
                    current_content_url = await create_weather_calendar_url(
                        hass, all_events, weather_entity_id, lang=lang, 
                        screen_size=screen_size, daily_forecast=daily_forecast,
                        add_back_button=add_back, max_events=max_events
                    )
                else: 
                     # Fallback lub brak forecast - używamy content_url który powinien być ustawiony w fallbacku
                     pass
            
            if current_content_url is None:
                 # Safety fallback
                 current_content_url = create_calendar_url(all_events, style="modern", lang=lang, screen_size=screen_size)

            interactive_url = await _add_interactive_layer_to_url(
                hass, current_content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_CALENDAR, "status": status})

    async def handle_send_camera_snapshot(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        camera_entity_id = call.data[ATTR_CAMERA_ENTITY]
        caption_template = call.data.get(ATTR_CAPTION, "")
        image_zoom = call.data.get(ATTR_IMAGE_ZOOM, 100)
        image_rotation = int(call.data.get(ATTR_DISPLAY_ROTATION, "0"))

        if isinstance(caption_template, Template):
            caption_template.hass = hass
            caption = caption_template.async_render(parse_result=False)
        else:
            caption = caption_template

        try:
            image = await async_get_image(hass, camera_entity_id)
        except Exception: return

        www_dir = Path(hass.config.path("www"))
        await hass.async_add_executor_job(lambda: www_dir.mkdir(parents=True, exist_ok=True))
        image_path = www_dir / f"visionect_snapshot_{uuid.uuid4().hex}.jpg"
        await hass.async_add_executor_job(lambda: image_path.write_bytes(image.content))
        await _async_cleanup_media_files(hass)

        try:
            base_url = get_internal_url(hass) if get_internal_url else get_url(hass)
        except Exception: base_url = get_url(hass)
        image_url = create_simple_cache_buster(f"{base_url}/local/{image_path.name}")

        content_url = create_text_message_url(message=caption, layout="image_top", image_url=image_url, text_size="24px", image_zoom=image_zoom, image_rotation=image_rotation)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_CAMERA_SNAPSHOT, "status": status})

    async def handle_send_sensor_graph(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        entity_ids = call.data[ATTR_ENTITIES]
        duration_hours = call.data.get(ATTR_DURATION_HOURS, 24)
        graph_type = call.data.get(ATTR_GRAPH_TYPE, "line")
        show_points = call.data.get(ATTR_SHOW_POINTS, False)
        image_zoom = call.data.get(ATTR_IMAGE_ZOOM, 100)
        image_rotation = int(call.data.get(ATTR_DISPLAY_ROTATION, "0"))
        start_time = dt_util.now() - timedelta(hours=duration_hours)


        history_data = await get_instance(hass).async_add_executor_job(
            partial(
                history.get_significant_states, 
                hass, 
                start_time, 
                entity_ids=entity_ids, 
                significant_changes_only=False, 
                include_start_time_state=True
            )
        )
        
        www_dir = Path(hass.config.path("www"))
        await hass.async_add_executor_job(lambda: www_dir.mkdir(parents=True, exist_ok=True))

        for device_uuid in uuids:
            orientation = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0"))
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            try:
                image_bytes = await hass.async_add_executor_job(_generate_graph_image, hass, history_data, entity_ids, graph_type, show_points, orientation)
            except Exception as e:
                _LOGGER.error(f"Graph generation exception: {e}")
                image_bytes = None

            if not image_bytes:
                # Debugging info
                data_points_count = sum(len(states) for states in history_data.values()) if history_data else 0
                _LOGGER.warning(f"Graph generation returned no data. Entity IDs: {entity_ids}, Data points found: {data_points_count}. Check if entities have numeric states.")
                content_url = f"data:text/html,{urllib.parse.quote('<html><body style=\"display:flex;align-items:center;justify-content:center;height:100vh;font-size:2em;\">No Data (Check Logs)</body></html>')}"
            else:
                image_path = www_dir / f"visionect_graph_{uuid.uuid4().hex}.png"
                await hass.async_add_executor_job(lambda: image_path.write_bytes(image_bytes))
                await _async_cleanup_media_files(hass)
                try: base_url = get_internal_url(hass) if get_internal_url else get_url(hass)
                except Exception: base_url = get_url(hass)
                image_url = create_simple_cache_buster(f"{base_url}/local/{image_path.name}")
                content_url = create_text_message_url(message="", layout="image_only", image_url=image_url, image_zoom=image_zoom, image_rotation=image_rotation)

            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_SENSOR_GRAPH, "status": status})

    async def handle_clear_web_cache(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        restart = bool(call.data.get("restart_session", False))
        status = "failure"
        if await api.async_clear_webkit_cache(uuids):
            status = "success"
            if restart: await api.async_restart_sessions_batch(uuids)
        for uuid_val in uuids:
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_CLEAR_WEB_CACHE, "status": status})

    async def handle_send_image_url(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        image_url = call.data[ATTR_IMAGE_URL]
        image_zoom = call.data.get(ATTR_IMAGE_ZOOM, 100)
        image_rotation = int(call.data.get(ATTR_DISPLAY_ROTATION, "0"))

        if not api.validate_image_url(image_url):
            _LOGGER.error(f"Unsupported image extension: {image_url}")
            return

        content_url = create_text_message_url(message="", layout="image_only", image_url=image_url, image_zoom=image_zoom, image_rotation=image_rotation)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_IMAGE_URL, "status": status})

    async def handle_start_slideshow(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        raw_views = call.data.get("views")
        seconds = int(call.data.get("seconds_per_slide", 30))
        loop = bool(call.data.get("loop", True))

        views_list = []
        if isinstance(raw_views, str):
            for line in raw_views.strip().splitlines():
                if line.strip(): views_list.append(line.strip())
        elif isinstance(raw_views, list):
            views_list = raw_views
        
        def _resolve_views_to_urls(items):
            out = []
            for it in items:
                if it.startswith(("http", "data:")): out.append(it)
                else:
                    resolved = _get_url_from_predefined(it)
                    if resolved: out.append(resolved)
            return out

        resolved_urls = _resolve_views_to_urls(views_list)
        processed_urls = []
        for u in resolved_urls:
            p = await _process_final_url(hass, u)
            processed_urls.append(p)
            
        def _build_slideshow_data_url(urls, sec, lp):
            processed = [create_simple_cache_buster(u) if not u.startswith("data:") else u for u in urls]
            js_urls = json.dumps(processed)
            loop_js = "true" if lp else "false"
            html_doc = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>html,body{{margin:0;height:100%;background:#fff}}#frame{{border:0;width:100%;height:100%;}}</style></head><body><iframe id="frame" referrerpolicy="no-referrer"></iframe><script>(function(){{var urls={js_urls};var idx=0;var loop={loop_js};var sec={int(sec)};function setSrc(){{try{{document.getElementById('frame').src=urls[idx];}}catch(e){{}}}}function next(){{idx++;if(idx>=urls.length){{if(loop)idx=0;else return;}}setSrc();}}setSrc();setInterval(next,Math.max(1,sec)*1000);}})();</script></body></html>"""
            return f"data:text/html,{urllib.parse.quote(html_doc, safe='')}"

        content_url = _build_slideshow_data_url(processed_urls, seconds, loop)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_START_SLIDESHOW, "status": status})

    async def handle_set_session_options(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        encoding = call.data.get("encoding")
        dithering = call.data.get("dithering")
        for uuid_val in uuids:
            status = "success" if await api.async_set_session_options(uuid_val, encoding=encoding, dithering=dithering) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SET_SESSION_OPTIONS, "status": status})

    async def handle_send_keypad(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        title = call.data[ATTR_TITLE]
        webhook_id = call.data[ATTR_ACTION_WEBHOOK_ID]
        
        try: base_url = get_internal_url(hass) if get_internal_url else get_url(hass)
        except Exception: base_url = get_url(hass)
        webhook_url = f"{base_url.rstrip('/')}/api/webhook/{webhook_id}"
        
        content_url = await create_keypad_url(hass, title, webhook_url)
        
        for device_uuid in uuids:
            interactive_url = await _add_interactive_layer_to_url(hass, content_url, None, False, False, False, None, None, call.data.get(ATTR_AUTO_RETURN_SECONDS, 0))
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_KEYPAD, "status": status})

    async def handle_send_crypto(call: ServiceCall):
        """Fetch crypto prices from CryptoCompare API (free, no key) and display on Joan."""
        uuids = await get_uuids_from_call(call)
        coins_input = call.data.get(ATTR_COINS, [])
        vs_currency = str(call.data.get(ATTR_VS_CURRENCY, "usd")).upper().strip()
        history_hours = call.data.get(ATTR_HISTORY_HOURS, 24)
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        show_header = call.data.get(ATTR_SHOW_HEADER, True)

        # Reverse map for CryptoCompare (e.g. "bitcoin" -> "BTC")
        comp_map = {v: k for k, v in CRYPTO_SYMBOL_MAP.items()}
        
        def _to_symbol(s: str) -> str:
            s_clean = s.strip().lower()
            return comp_map.get(s_clean, s.strip().upper())

        symbols = [_to_symbol(c) for c in coins_input]
        session = async_get_clientsession(hass)

        # --- Fetch current prices + 24h change ---
        price_data = {}
        try:
            syms_param = ",".join(symbols)
            price_url = (
                f"https://min-api.cryptocompare.com/data/pricemultifull"
                f"?fsyms={syms_param}&tsyms={vs_currency}"
            )
            async with session.get(price_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data_json = await resp.json()
                    price_data = data_json.get("RAW", {})
                else:
                    _LOGGER.warning("send_crypto: CryptoCompare returned HTTP %s", resp.status)
        except Exception as exc:
            _LOGGER.error("send_crypto: price fetch failed: %s", exc)

        coins_out = []
        for orig_input, sym in zip(coins_input, symbols):
            data = price_data.get(sym, {}).get(vs_currency, {})
            price = data.get("PRICE")
            change = data.get("CHANGEPCT24HOUR")
            high_24h = data.get("HIGHDAY")
            low_24h = data.get("LOWDAY")

            display_name = orig_input.title() if orig_input.lower() == orig_input else orig_input
            if sym in CRYPTO_SYMBOL_MAP:
                display_name = CRYPTO_SYMBOL_MAP[sym].replace("-", " ").title()

            # --- Fetch sparkline history ---
            hist_vals = []
            if history_hours > 0 and price is not None:
                try:
                    limit = max(1, history_hours)
                    hist_url = (
                        f"https://min-api.cryptocompare.com/data/v2/histohour"
                        f"?fsym={sym}&tsym={vs_currency}&limit={limit}"
                    )
                    async with session.get(hist_url, timeout=aiohttp.ClientTimeout(total=15)) as hr:
                        if hr.status == 200:
                            hist_json = await hr.json()
                            raw_data = hist_json.get("Data", {}).get("Data", [])
                            raw = [float(item.get("close")) for item in raw_data if item.get("close") is not None]
                            if len(raw) > 20:
                                step = max(1, len(raw) // 20)
                                raw = raw[::step][:20]
                            hist_vals = raw
                except Exception:
                    pass  # sparkline is optional

            coins_out.append({
                "name": display_name,
                "symbol": sym,
                "price": price,
                "change_pct": change,
                "history": hist_vals,
                "unit": vs_currency.upper(),
                "high_24h": high_24h,
                "low_24h": low_24h,
            })

        if not coins_out:
            _LOGGER.warning("send_crypto: no data from CryptoCompare.")
            return

        history_label = f"{history_hours}h" if history_hours > 0 else ""
        content_url = await create_crypto_panel_url(hass, coins_out, screen_size, lang, show_header, history_label)

        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_CRYPTO, "status": status})



    async def handle_send_button_panel(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        raw_title = call.data.get("title")
        title = raw_title.strip() if isinstance(raw_title, str) else ""
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")

        try: base_url = get_internal_url(hass) if get_internal_url else get_url(hass)
        except Exception: base_url = get_url(hass)
        
        def _get_wh(wid): return f"{base_url.rstrip('/')}/api/webhook/{wid}"

        buttons = []
        for i in range(1, 13):
            wid = call.data.get(f"button_{i}_webhook_id")
            if wid:
                buttons.append({
                    "webhook_url": _get_wh(wid),
                    "name": call.data.get(f"button_{i}_name", ""),
                    "icon": call.data.get(f"button_{i}_icon", ""),
                    "sub_name": ""
                })
        
        if not buttons:
            _LOGGER.error("send_button_panel: No valid buttons.")
            return

        content_url = await create_button_panel_url(hass, title, buttons, screen_size)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_BUTTON_PANEL, "status": status})

    SAFE_TCLV_NAME_ALIASES = {
        ATTR_HEART_BEAT_INTERVAL: [
            "HEARTBEAT",
            "HEART_BEAT",
            "HEART BEAT",
            "HEART BEAT INTERVAL",
        ],
        ATTR_NETWORK_ERROR_RETRY_INTERVAL: [
            "NETWORK_ERROR_RETRY",
            "NET_ERROR_RETRY",
            "NETWORK ERROR RETRY",
            "NETWORK ERROR RETRY INTERVAL",
        ],
        ATTR_SYSTEM_SCREENS: ["SYSTEM_SCREENS", "SYS_SCREENS", "SYSTEM SCREENS"],
        ATTR_TOUCH_MODE: ["TOUCH_MODE", "TOUCH MODE", "SYS_TOUCH_EN", "TOUCH_EN", "SYSTEM_TOUCH"],
        ATTR_POWER_SAVING_MODE: ["POWER_SAVING", "PWR_SAVE", "POWER SAVING", "POWER SAVING MODE"],
    }
    SAFE_DIAG_KEYWORDS = [
        "HEART",
        "RETRY",
        "NETWORK",
        "TOUCH",
        "POWER",
        "SAVING",
        "SCREEN",
        "SYSTEM",
    ]

    def _resolve_safe_tclv_ids(tclv_list: list[dict]) -> dict[str, int]:
        """Resolve safe field names to TCLV IDs using fuzzy alias matching."""
        resolved: dict[str, int] = {}
        normalized_rows: list[tuple[int, str]] = []
        for item in tclv_list or []:
            try:
                tid = int(item.get("ID"))
            except (TypeError, ValueError):
                continue
            name = str(item.get("Name", "")).strip().upper()
            if not name:
                continue
            normalized_rows.append((tid, name))

        for attr_name, aliases in SAFE_TCLV_NAME_ALIASES.items():
            for tid, tname in normalized_rows:
                if any(alias in tname for alias in aliases):
                    resolved[attr_name] = tid
                    break
        return resolved

    def _decode_boolish(value: str, true_label: str = "Enabled", false_label: str = "Disabled") -> str:
        sval = str(value).strip().lower()
        if sval in {"1", "true", "on", "enabled"}:
            return true_label
        if sval in {"0", "false", "off", "disabled"}:
            return false_label
        return str(value)

    def _decode_system_screens(value: str) -> str:
        mapping = {
            "0": "Disabled",
            "1": "Battery",
            "2": "Not connected",
            "3": "Battery+Not connected",
        }
        sval = str(value).strip()
        return mapping.get(sval, sval)

    def _encode_safe_value(attr_name: str, value) -> str:
        if attr_name in (ATTR_HEART_BEAT_INTERVAL, ATTR_NETWORK_ERROR_RETRY_INTERVAL):
            sval = str(value).strip()
            if sval == "":
                return ""
            return str(int(sval))
        if attr_name == ATTR_SYSTEM_SCREENS:
            sval = str(value).strip()
            label_map = {
                "Disabled": "0",
                "Battery": "1",
                "Not connected": "2",
                "Battery+Not connected": "3",
            }
            return label_map.get(sval, sval)
        if attr_name == ATTR_TOUCH_MODE:
            # VSS TCLV 50 expects numeric mode values.
            # Accept legacy labels for backwards compatibility.
            sval = str(value).strip()
            label_map = {"Disabled": "0", "On": "1", "On + Beep": "3"}
            return label_map.get(sval, sval)
        return str(value)

    SAFE_FIELD_LABELS = {
        ATTR_HEART_BEAT_INTERVAL: "Heart beat interval",
        ATTR_NETWORK_ERROR_RETRY_INTERVAL: "Network error retry interval",
        ATTR_SYSTEM_SCREENS: "System screens",
        ATTR_TOUCH_MODE: "Touch mode",
        ATTR_POWER_SAVING_MODE: "Power saving mode",
    }

    _SAFE_FIELD_NTR = {
        ATTR_HEART_BEAT_INTERVAL: "safe_field_heartbeat",
        ATTR_NETWORK_ERROR_RETRY_INTERVAL: "safe_field_network_retry",
        ATTR_SYSTEM_SCREENS: "safe_field_system_screens",
        ATTR_TOUCH_MODE: "safe_field_touch",
        ATTR_POWER_SAVING_MODE: "safe_field_power_save",
    }

    def _safe_field_label(lang: str, attr: str) -> str:
        nk = _SAFE_FIELD_NTR.get(attr)
        return ntr(lang, nk) if nk else attr

    def _format_safe_values(values: dict[str, str], lang: str) -> str:
        if not values:
            return ntr(lang, "safe_values_none")
        lines = []
        for key, val in values.items():
            label = _safe_field_label(lang, key)
            display_val = str(val).strip()
            if display_val == "":
                display_val = ntr(lang, "safe_values_empty")
            lines.append(f"- {label}: `{display_val}`")
        return "\n".join(lines)

    def _format_applied_values(values: dict[str, str], lang: str) -> str:
        if not values:
            return "- " + ntr(lang, "safe_no_applied_fields")

        system_screens_map = {
            "0": "Disabled",
            "1": "Battery",
            "2": "Not connected",
            "3": "Battery+Not connected",
        }
        touch_mode_map = {
            "0": "Off",
            "1": "On",
            "3": "On + Beep",
        }

        lines: list[str] = []
        for key, raw in values.items():
            val = str(raw).strip()
            label = _safe_field_label(lang, key)
            if key == ATTR_HEART_BEAT_INTERVAL and val != "":
                lines.append(f"- {label}: {ntr(lang, 'safe_set_minutes', val=val)}")
            elif key == ATTR_SYSTEM_SCREENS and val != "":
                pretty = system_screens_map.get(val, val)
                lines.append(f"- {label}: {ntr(lang, 'safe_set_value', val=pretty)}")
            elif key == ATTR_TOUCH_MODE and val != "":
                pretty = touch_mode_map.get(val, val)
                lines.append(f"- {label}: {ntr(lang, 'safe_set_value', val=pretty)}")
            else:
                lines.append(f"- {label}: {ntr(lang, 'safe_set_value', val=val)}")
        return "\n".join(lines)

    def _has_any_read_value(values: dict[str, str]) -> bool:
        for val in values.values():
            if str(val).strip() != "":
                return True
        return False

    def _format_safe_ids(ids: dict[str, int], lang: str) -> str:
        if not ids:
            return "- (no safe TCLV IDs mapped)"
        lines = []
        for key, tid in ids.items():
            label = _safe_field_label(lang, key)
            lines.append(f"- {label}: `{tid}`")
        return "\n".join(lines)

    def _format_diag_rows(rows: list[dict], lang: str) -> str:
        if not rows:
            return "- (no additional readable TCLV candidates detected)"
        lines = []
        for row in rows:
            name = row.get("name", "?")
            tid = row.get("id", "?")
            val = str(row.get("value", "")).strip() or ntr(lang, "safe_values_empty")
            lines.append(f"- {name} (ID `{tid}`): `{val}`")
        return "\n".join(lines)

    async def _read_safe_config_for_uuid(device_uuid: str) -> dict:
        tclv_list = await api.async_get_tclv_list(device_uuid) or []
        safe_ids = _resolve_safe_tclv_ids(tclv_list)
        values = await api.async_get_tclv_values(device_uuid, list(safe_ids.values()))
        decoded: dict[str, str] = {}
        for attr_name, tid in safe_ids.items():
            raw_val = values.get(tid, "")
            if attr_name == ATTR_SYSTEM_SCREENS:
                decoded[attr_name] = _decode_system_screens(raw_val)
            else:
                decoded[attr_name] = str(raw_val)

        # Diagnostic expansion: show additional readable candidates (Touch/Power/etc.)
        diag_candidates: list[dict] = []
        diag_ids: list[int] = []
        seen_ids: set[int] = set()
        for item in tclv_list:
            try:
                tid = int(item.get("ID"))
            except (TypeError, ValueError):
                continue
            tname = str(item.get("Name", "")).strip()
            tname_upper = tname.upper()
            if not tname:
                continue
            if any(k in tname_upper for k in SAFE_DIAG_KEYWORDS):
                if tid not in seen_ids:
                    seen_ids.add(tid)
                    diag_ids.append(tid)
                    diag_candidates.append({"id": tid, "name": tname})

        diag_values = await api.async_get_tclv_values(device_uuid, diag_ids)
        for row in diag_candidates:
            row["value"] = str(diag_values.get(int(row["id"]), ""))

        return {"ids": safe_ids, "values": decoded, "diag_candidates": diag_candidates}

    async def handle_read_safe_device_config(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        state = hass.data[DOMAIN][entry.entry_id]["safe_config_state"]
        nlang = _tablet_notify_lang(hass)
        for device_uuid in uuids:
            read_data = await _read_safe_config_for_uuid(device_uuid)
            state["last_read"][device_uuid] = read_data
            has_readback = _has_any_read_value(read_data.get("values", {}))
            note = (
                ntr(nlang, "safe_read_note_firmware")
                if has_readback
                else ntr(nlang, "safe_read_note_noreadback")
            )
            notif_body = ntr(
                nlang,
                "safe_read_step1",
                device=device_uuid,
                values=_format_safe_values(read_data.get("values", {}), nlang),
                note=note,
            )
            async_create_persistent_notification(
                hass,
                notif_body,
                title=ntr(nlang, "safe_read_title"),
                notification_id=f"visionect_safe_read_{device_uuid}",
            )
            hass.bus.async_fire(
                EVENT_COMMAND_RESULT,
                {"uuid": device_uuid, "service": SERVICE_READ_SAFE_DEVICE_CONFIG, "status": "success", "params": read_data.get("values", {})},
            )

    async def handle_apply_safe_device_config(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        state = hass.data[DOMAIN][entry.entry_id]["safe_config_state"]
        incoming = {
            ATTR_HEART_BEAT_INTERVAL: call.data.get(ATTR_HEART_BEAT_INTERVAL),
            ATTR_SYSTEM_SCREENS: call.data.get(ATTR_SYSTEM_SCREENS),
            ATTR_TOUCH_MODE: call.data.get(ATTR_TOUCH_MODE),
        }
        incoming = {k: v for k, v in incoming.items() if v is not None}
        if not incoming:
            return

        for device_uuid in uuids:
            current = await _read_safe_config_for_uuid(device_uuid)
            safe_ids = current.get("ids", {})
            current_values = current.get("values", {})

            backup_values = {k: current_values.get(k, "") for k in incoming.keys() if k in current_values}
            state["last_backup"][device_uuid] = backup_values

            values_to_write: dict[int, str] = {}
            written_keys: list[str] = []
            for attr_name, new_val in incoming.items():
                tid = safe_ids.get(attr_name)
                if tid is None:
                    continue
                values_to_write[tid] = _encode_safe_value(attr_name, new_val)
                written_keys.append(attr_name)

            if not values_to_write:
                nlang = _tablet_notify_lang(hass)
                async_create_persistent_notification(
                    hass,
                    ntr(nlang, "safe_no_mapping", device=device_uuid),
                    title=ntr(nlang, "safe_no_mapping_title"),
                    notification_id=f"visionect_safe_apply_{device_uuid}",
                )
                hass.bus.async_fire(
                    EVENT_COMMAND_RESULT,
                    {"uuid": device_uuid, "service": SERVICE_APPLY_SAFE_DEVICE_CONFIG, "status": "failure"},
                )
                continue

            success = await api.async_set_tclv_values(device_uuid, values_to_write)
            nlang = _tablet_notify_lang(hass)
            changed_view = ", ".join(_safe_field_label(nlang, k) for k in written_keys)
            if success:
                verified = await _read_safe_config_for_uuid(device_uuid)
                state["last_read"][device_uuid] = verified
                requested_values = {k: _encode_safe_value(k, v) for k, v in incoming.items()}
                async_create_persistent_notification(
                    hass,
                    ntr(
                        nlang,
                        "safe_applied",
                        device=device_uuid,
                        fields=changed_view or "-",
                        applied=_format_applied_values(requested_values, nlang),
                    ),
                    title=ntr(nlang, "safe_applied_title"),
                    notification_id=f"visionect_safe_apply_{device_uuid}",
                )
            else:
                async_create_persistent_notification(
                    hass,
                    ntr(nlang, "safe_apply_failed", device=device_uuid),
                    title=ntr(nlang, "safe_apply_failed_title"),
                    notification_id=f"visionect_safe_apply_{device_uuid}",
                )
            hass.bus.async_fire(
                EVENT_COMMAND_RESULT,
                {"uuid": device_uuid, "service": SERVICE_APPLY_SAFE_DEVICE_CONFIG, "status": "success" if success else "failure"},
            )

    async def handle_restore_safe_device_config(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        state = hass.data[DOMAIN][entry.entry_id]["safe_config_state"]
        nlang = _tablet_notify_lang(hass)
        for device_uuid in uuids:
            backup = state.get("last_backup", {}).get(device_uuid, {})
            if not backup:
                async_create_persistent_notification(
                    hass,
                    ntr(nlang, "safe_no_backup", device=device_uuid),
                    title=ntr(nlang, "safe_no_backup_title"),
                    notification_id=f"visionect_safe_restore_{device_uuid}",
                )
                hass.bus.async_fire(
                    EVENT_COMMAND_RESULT,
                    {"uuid": device_uuid, "service": SERVICE_RESTORE_SAFE_DEVICE_CONFIG, "status": "failure"},
                )
                continue

            current = await _read_safe_config_for_uuid(device_uuid)
            safe_ids = current.get("ids", {})
            values_to_write: dict[int, str] = {}
            for attr_name, old_val in backup.items():
                tid = safe_ids.get(attr_name)
                if tid is None:
                    continue
                encoded_val = _encode_safe_value(attr_name, old_val)
                # Skip empty backup values for strict numeric fields.
                # Some firmware does not return readable values for TCLV reads.
                if encoded_val == "":
                    continue
                values_to_write[tid] = encoded_val

            success = await api.async_set_tclv_values(device_uuid, values_to_write)
            if success:
                state["last_read"][device_uuid] = await _read_safe_config_for_uuid(device_uuid)
                async_create_persistent_notification(
                    hass,
                    ntr(
                        nlang,
                        "safe_restored",
                        device=device_uuid,
                        values=_format_safe_values(backup, nlang),
                    ),
                    title=ntr(nlang, "safe_restored_title"),
                    notification_id=f"visionect_safe_restore_{device_uuid}",
                )
            else:
                async_create_persistent_notification(
                    hass,
                    ntr(nlang, "safe_restore_failed", device=device_uuid),
                    title=ntr(nlang, "safe_restore_failed_title"),
                    notification_id=f"visionect_safe_restore_{device_uuid}",
                )
            hass.bus.async_fire(
                EVENT_COMMAND_RESULT,
                {"uuid": device_uuid, "service": SERVICE_RESTORE_SAFE_DEVICE_CONFIG, "status": "success" if success else "failure"},
            )

    # Register services
    hass.services.async_register(DOMAIN, SERVICE_SET_URL, handle_set_url, schema=SERVICE_SET_URL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_TEXT, handle_send_text, schema=SERVICE_SEND_TEXT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_DISPLAY_ROTATION, handle_set_display_rotation, schema=SERVICE_SET_DISPLAY_ROTATION_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_FORCE_REFRESH, handle_force_refresh, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_DISPLAY, handle_clear_display, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SLEEP_DEVICE, handle_sleep_device, schema=SERVICE_SLEEP_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_WAKE_DEVICE, handle_wake_device, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_QR_CODE, handle_send_qr_code, schema=SERVICE_SEND_QR_CODE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_CALENDAR, handle_send_calendar, schema=SERVICE_SEND_CALENDAR_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_WEATHER, handle_send_weather, schema=SERVICE_SEND_WEATHER_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_ENERGY_PANEL, handle_send_energy_panel, schema=SERVICE_SEND_ENERGY_PANEL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_TODO_LIST, handle_send_todo_list, schema=SERVICE_SEND_TODO_LIST_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_CAMERA_SNAPSHOT, handle_send_camera_snapshot, schema=SERVICE_SEND_CAMERA_SNAPSHOT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_STATUS_PANEL, handle_send_status_panel, schema=SERVICE_SEND_STATUS_PANEL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_SENSOR_GRAPH, handle_send_sensor_graph, schema=SERVICE_SEND_SENSOR_GRAPH_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_RSS_FEED, handle_send_rss_feed, schema=SERVICE_SEND_RSS_FEED_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_KEYPAD, handle_send_keypad, schema=SERVICE_SEND_KEYPAD_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_WEB_CACHE, handle_clear_web_cache, schema=SERVICE_CLEAR_WEB_CACHE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_START_SLIDESHOW, handle_start_slideshow, schema=SERVICE_START_SLIDESHOW_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_IMAGE_URL, handle_send_image_url, schema=SERVICE_SEND_IMAGE_URL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_SESSION_OPTIONS, handle_set_session_options, schema=SERVICE_SET_SESSION_OPTIONS_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_BUTTON_PANEL, handle_send_button_panel, schema=SERVICE_SEND_BUTTON_PANEL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_CRYPTO, handle_send_crypto, schema=SERVICE_SEND_CRYPTO_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_APPLY_SAFE_DEVICE_CONFIG, handle_apply_safe_device_config, schema=SERVICE_APPLY_SAFE_DEVICE_CONFIG_SCHEMA)


    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Visionect Joan config entry successfully initialized.")



    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Unloading Visionect Joan integration.")
    services_to_remove = [
        SERVICE_SET_URL, SERVICE_SEND_TEXT, SERVICE_SET_DISPLAY_ROTATION, SERVICE_FORCE_REFRESH,
        SERVICE_CLEAR_DISPLAY, SERVICE_SLEEP_DEVICE, SERVICE_WAKE_DEVICE, SERVICE_SEND_QR_CODE,
        SERVICE_SEND_CALENDAR, SERVICE_SEND_WEATHER, SERVICE_SEND_ENERGY_PANEL, SERVICE_SEND_TODO_LIST,
        SERVICE_SEND_CAMERA_SNAPSHOT, SERVICE_SEND_STATUS_PANEL, SERVICE_SEND_SENSOR_GRAPH,
        SERVICE_SEND_RSS_FEED, SERVICE_CLEAR_WEB_CACHE, SERVICE_START_SLIDESHOW, SERVICE_SEND_IMAGE_URL,
        SERVICE_SET_SESSION_OPTIONS, SERVICE_SEND_KEYPAD, SERVICE_SEND_BUTTON_PANEL,
        SERVICE_SEND_CRYPTO, SERVICE_APPLY_SAFE_DEVICE_CONFIG,
    ]
    for service in services_to_remove:
        hass.services.async_remove(DOMAIN, service)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Visionect Joan integration successfully unloaded.")
    else:
        _LOGGER.error("Error while unloading Visionect Joan integration.")

    return unload_ok

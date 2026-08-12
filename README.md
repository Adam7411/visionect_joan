***
- [Visionect Server v3 (All‑in‑One) installation in Home Assistant](https://github.com/Adam7411/visionect-v3-allinone)
- [Visionect Software Suite - Installation in Proxmox](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant_EN)
- [Joan 6 / 13PRO: AppDaemon Dashboard Generator add-on](https://github.com/Adam7411/joan_generator/blob/main/README_EN.md)
- [Developer knowledge base](./docs/INTEGRATION_KNOWLEDGE.md)
***

<div align="right">
<a href="README_pl.md">Polski</a> | <strong>English</strong>
</div>

# Version E‑Ink Home Assistant — Visionect Joan for Home Assistant

The visionect_joan integration connects energy‑efficient e‑ink Joan 6 / 13 PRO tablets with Home Assistant through the Visionect Software Suite (VSS). It provides per‑URL battery protection, ready‑made e‑ink screens, AppDaemon dashboard support and interactive webhooks.


## Recommended AppDaemon configuration (brief)

Most users run a single AppDaemon dashboard generated with the Joan Dashboard Generator add‑on (joan_generator). The typical setup:

- joan_generator (GUI) → .dash files in AppDaemon → http://<HA>:5050/Dashboard?widget=…
- Tablet session URL → the same AppDaemon dashboard URL (set once)
- visionect_joan integration → manages device operations: battery, recovery, temporary overlays

Set once in integration Options:

- Main menu URL: AppDaemon dashboard URL
- Recovery probe URL: same AppDaemon address (used to check availability during recovery)

AppDaemon keeps widgets refreshed from HA entities — avoid repeatedly calling set_url. Use built‑in services (send_text, camera snapshot, weather, …) as temporary overlays with auto_return_seconds to return to the dashboard.


## Table of contents

- Recommended configuration (AppDaemon)
- Purpose & overview
- Key features
- Installation
- VSS & integration setup
- Sync profiles and battery guard
- Entities
- Services — summary
- Interactive layer & recovery
- Automation examples
- Performance & battery
- Troubleshooting
- FAQ
- Development & knowledge base
- License


## Purpose & overview

The integration is a bridge between Home Assistant and VSS. It enables:

- Managing and enforcing the tablet session URL (AppDaemon, /local/, Lovelace, images).
- Rendering e‑ink optimized overlay screens (energy, weather, calendar, buttons, PIN, RSS, etc.).
- Exposing sensors, diagnostics, repairs and controls for sync/power management.
- Session recovery after HA/VSS restarts with minimal tablet wakeups (Eco mode).


## Key features (summary)

- Any URL, predefined views, AppDaemon dashboards, local /local/ files, inline data:text/html.
- Built‑in views: weather (3 layouts), calendar, todo/shopping list (webhook toggle), energy panel, status panel, sensor graphs, RSS, QR, camera snapshot, crypto panel.
- Interactive overlay: bottom bar (← Back / ✔ / → Action) or full‑screen tap; webhooks trigger HA automations.
- Slideshow support (use long intervals in Eco).
- Per‑tablet sync profile (Eco / Normal / Alert) and battery guard (avoid unnecessary PUTs to VSS).
- Recovery probe and optional safe restore flows; WebKit cache management; sleep/wake and rotation.
- Live preview camera entity (PNG snapshot of current screen).


## Installation

### Via HACS (recommended)
1. Install HACS.
2. HACS → Integrations → ⋮ → Custom repositories → add https://github.com/Adam7411/visionect_joan
3. Install Visionect Joan and restart Home Assistant.

### Manual
1. Copy the folder custom_components/visionect_joan/ to /config/custom_components/.
2. Restart Home Assistant.

Requirements: running VSS (visionect-v3-allinone) and tablet registered in VSS.


## VSS & integration setup

Settings → Devices & Services → Add integration → Visionect Joan

Connection: VSS host IP:8081, login/password or API key + secret (create in VSS → Users → Add API key).

Integration options include:
- Views (named URLs)
- Main menu URL (default Back target / AppDaemon dashboard)
- Recovery probe URL (HTTP probe used before session restart)
- Recovery page token (fallback)
- Notification toggles (battery, offline, error codes, VSS health)
- Per‑device session URL and options


## Sync profiles & battery guard

Select entity: refresh_profile_select

Profiles:
- Eco — for a stable AppDaemon dashboard. PUTs are skipped if URL unchanged; minimal polling.
- Normal — occasional overlays allowed; guard enabled with medium cache.
- Alert — used for urgent alerts/cameras; may force wake and faster refresh.

wake_tablet flag in services forces a session write even when Eco would skip it. After HA restart in Eco, if probe shows AppDaemon OK and URL matches expected Main menu/view, the integration avoids unnecessary session restarts to save battery.


## Entities (examples)

- sensor.* — state, battery, RSSI, temperature, configured_url, last_seen, error_code
- binary_sensor.* — online, orphan/health, is_charging, dashboard_ok
- select — sync profile, view, back target, sleep schedule, encoding, dithering
- number — ReloadTimeout (session refresh seconds)
- text — device name (writes to VSS)
- button — force_refresh, reboot, clear_web_cache (some hidden by default)
- camera — live preview PNG of the current screen


## Services — summary

Key services are: set_url, send_text, send_image_url, send_camera_snapshot, send_status_panel, send_energy_panel, send_weather, send_calendar, send_todo_list, send_sensor_graph, send_rss_feed, send_qr_code, start_slideshow, send_keypad, send_button_panel, set_session_options, clear_web_cache, force_refresh, sleep_device, wake_device, set_display_rotation, read_safe_device_config, apply_safe_device_config, restore_safe_device_config, diagnose_vss_session, health_check_vss_url.

Full field documentation is in Developer Tools → Services and ./services.yaml.


## Interactive layer & recovery

Back priority: call back_button_url in service → per‑device Back target select → global Main menu URL.

Overlays: when sending HTML/data: the integration remembers the previous AppDaemon URL and restores it after Back / auto_return_seconds.

Recovery HTTP: if tablet cannot reach HA, set the VSS Default URL to the generated recovery page (Integration Options → Recovery page). Offline alerts and hourly checks are available (v3.9.13+ persists state across restarts).


## Automation examples (short)

Set a permanent AppDaemon dashboard (once):

service: visionect_joan.set_url
target:
  device_id: <joan_device_id>
data:
  url: "http://192.168.100.80:5050/Dashboard?skin=default&widget=joan_salon&count=1"
  wake_tablet: true

Temporary alert overlay:

service: visionect_joan.send_text
target:
  device_id: <joan_device_id>
data:
  message: "Front door opened!"
  text_size: 36
  add_back_button: true
  auto_return_seconds: 120

Listen for push results:

trigger:
  - platform: event
    event_type: visionect_joan_command_result
action:
  - service: logbook.log
    data:
      message: "Joan {{ trigger.event.data.push_result }} skipped={{ trigger.event.data.skipped_wake }}"


## Performance & battery (high level)

- Use AppDaemon dashboard + Eco profile for everyday usage.
- Use overlays with auto_return_seconds; do not leave overlays permanently.
- Slideshow in Eco: long intervals (≥300 s recommended).
- ReloadTimeout: 60–300 s for dynamic pages; higher for static AppDaemon.
- Configure Recovery probe URL to point at AppDaemon.


## Troubleshooting (short)

- Connection refused after HA restart: check Recovery probe URL and AppDaemon status.
- Wrong screen: check sensor.*_configured_url and binary_sensor.*_dashboard_ok and set_url.
- Webhook not firing: verify webhook_id in automation and Developer Tools → Events.
- Offline alert with wrong time: reload integration (v3.9.13+ persists guard to disk).
- Old images/styles: force_refresh or adjust ReloadTimeout.
- VSS orphan sessions: use Integration Options → Repairs.

Enable debug logs:

logger:
  logs:
    custom_components.visionect_joan: debug


## FAQ (short)

Q: Best setup for single dashboard?
A: joan_generator + AppDaemon + one set_url + Eco profile.

Q: Do button panels reflect entity states?
A: No — buttons trigger one‑way webhooks. Use AppDaemon or send_status_panel for live states.

Q: Other Joan models supported?
A: Tested on Joan 6 / 13 PRO.


## Development & knowledge base

- Knowledge base: ./docs/INTEGRATION_KNOWLEDGE.md
- Unit tests: tests/ (e.g. python -m pytest tests/test_url_push.py)
- Issues: GitHub Issues


## License

MIT — not an official Visionect or Home Assistant product. Tested on Joan 6 / 13 PRO. Development assisted by AI.

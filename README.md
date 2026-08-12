***
- [Visionect Server v3 (All‑in‑One) installation in Home Assistant](https://github.com/Adam7411/visionect-v3-allinone)
- [Visionect Software Suite - Installation in Proxmox](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant_EN)
- [Joan 6 / 13PRO: AppDaemon Dashboard Generator add-on](https://github.com/Adam7411/joan_generator/blob/main/README_EN.md)
- [Developer knowledge base](./docs/INTEGRATION_KNOWLEDGE.md)
***

<div align="right">
<strong>English</strong> | <a href="README_pl.md">Polski</a>
</div>

# Version E‑Ink Home Assistant — Visionect Joan for Home Assistant

The visionect_joan integration connects energy‑efficient e‑ink Joan 6/13PRO tablets with Home Assistant through the Visionect Software Suite (VSS). It provides per‑URL battery protection, ready‑made e‑ink screens, AppDaemon dashboard support and interactive webhooks.

<img width="1280" height="800" alt="Joan 6 home screen" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

<p align="center">
⬇️ Hardware: Joan 6/13PRO ⬇️  
<br>
<img width="421" height="328" alt="Joan 6 e-ink tablet" src="https://github.com/user-attachments/assets/6fd88078-283a-4363-a801-71250b8211f4" />
<img width="1484" height="1278" alt="Joan large" src="https://github.com/user-attachments/assets/99fb87e0-3d8c-4ecc-b411-ad81f203665d" />

</p>

---

## Table of Contents
- Purpose & overview
- Key features
- Screenshots
- Installation
- Visionect Software Suite (VSS) Setup
- Predefined Views
- Entities
- Services – Summary
- Service Details
- Interactive Layer & Back Priority
- Automation Examples
- Performance & Battery
- Security & Webhooks
- Troubleshooting
- FAQ
- Development & Knowledge Base
- License


## Purpose & Overview

The integration acts as a bridge between Home Assistant and the Visionect Software Suite (VSS). It renders dynamic, e‑ink‑optimized screens on the Joan 6/13PRO tablet triggered by context (events, zones, time, sensors). Instead of a static dashboard you can push fully rendered view overlays: energy panel, to‑do list with webhook toggles, sensor graphs, weather with chart, PIN keypad or a 12‑button action panel.


## Key Features

- Full screen content control: any URL, local pages (AppDaemon, `/local/`, embedded Lovelace), images, inline `data:text/html`.
- Built‑in e‑ink optimized views: weather (3 layouts), calendar, to‑do/shopping list (interactive toggle), energy panel, status panel, sensor history graphs, RSS, QR, camera snapshot, crypto panel.
- Interactive overlay: bottom bar (← Back / ✔ Center / → Action) or full‑screen tap‑to‑action/back; webhooks trigger HA automations.
- Slideshow support (use long intervals in Eco mode).
- Per‑device sync profiles (Eco / Normal / Alert) and battery guard to avoid unnecessary session updates.
- Recovery probe and safe restore flows; WebKit cache management; sleep/wake and rotation utilities.
- Live preview camera entity (PNG snapshot of current screen).


## Screenshots

<details>
  <summary>Expand screenshot gallery</summary>
  <img width="425" height="574" alt="Start panel" src="https://github.com/user-attachments/assets/fea6f969-3785-4efd-961a-58e9086becfd" />
  <img width="758" height="1024" alt="Home dashboard" src="https://github.com/user-attachments/assets/fd78c164-6691-477e-84e1-e47a1f70a8cc" />
  <img width="758" height="1024" alt="RSS feed view" src="https://github.com/user-attachments/assets/f5a1f528-8201-47a0-9f7a-15b435f9152c" />
  <img width="758" height="1024" alt="Detailed weather" src="https://github.com/user-attachments/assets/2aca216e-e0d2-454e-b089-ee1eb04e947b" />
  <img width="758" height="1024" alt="PIN keypad" src="https://github.com/user-attachments/assets/c765b34f-ed4e-48d7-a59d-ff8ecd67aa7c" />
  <img width="758" height="1024" alt="Monthly calendar" src="https://github.com/user-attachments/assets/a5f3b53e-1b33-414b-8173-3fac794cbd46" />
  <img width="758" height="1024" alt="Camera snapshot" src="https://github.com/user-attachments/assets/a73e16a8-af85-47a0-9088-f21b932f9231" />
  <img width="758" height="1024" alt="Sensor graph" src="https://github.com/user-attachments/assets/7819468a-c33b-409f-9845-2256def6a134" />
  <img width="758" height="1024" alt="Energy panel" src="https://github.com/user-attachments/assets/acb78d0e-ca38-451e-8fc2-f64f479d1c78" />
  <img width="758" height="1024" alt="Live preview camera" src="https://github.com/user-attachments/assets/3bd6d185-33ae-4407-98c5-9b70821c27b9" />
</details>


## Installation

### Via HACS (recommended)
1. Install [HACS](https://hacs.xyz/) if not already.
2. HACS → Integrations → ⋮ → Custom repositories → add `https://github.com/Adam7411/visionect_joan`.
3. Search “Visionect Joan” → Install.
4. Restart Home Assistant.

### Manual
1. Copy `custom_components/visionect_joan/` to `/config/custom_components/`.
2. Restart Home Assistant.

Requirements: running VSS (visionect-v3-allinone) and tablet registered in VSS.


## Visionect Software Suite (VSS) Setup

Settings → Devices & Services → Add integration → Visionect Joan

Provide connection details: VSS host `IP:8081`, or API key + secret (create in VSS → Users → Add API key).

Integration options include views, Main menu URL, Recovery probe URL, notification toggles (battery/offline/error), per‑device session URL and more.


## Predefined Views

Configure in integration Options: add named view entries (Name + URL). Names are selectable via the “Choose view” select entity or referenced in services (`url` / `predefined_url`). Legacy “Name: URL” lines are auto‑parsed.


## Entities

- `camera` — live screen preview (PNG)
- `sensor.*` — online state, battery, temperature, RSSI, uptime, configured_url, last_seen, error_code
- `binary_sensor.*` — online, orphan/health, is_charging, dashboard_ok
- `select` — view, back target, sync profile, encoding/dithering
- `number` — ReloadTimeout (session refresh interval)
- `text` — device name
- `button` — force_refresh, reboot, clear_web_cache (some hidden)


## Services — Summary

See full list in Developer Tools → Services and ./services.yaml. Key services include set_url, send_text, send_image_url, send_camera_snapshot, send_status_panel, send_energy_panel, send_weather, send_calendar, send_todo_list, send_sensor_graph, send_rss_feed, send_qr_code, start_slideshow, send_keypad, send_button_panel, set_session_options, clear_web_cache, force_refresh, sleep_device, wake_device, set_display_rotation, and safe_device_config operations.


## Interactive Layer & Recovery

Back priority: service call `back_button_url` → per‑device Back target select → global Main menu URL. Overlays restore previous AppDaemon URL after Back / auto_return_seconds. Recovery uses HTTP probe (AppDaemon) and can fall back to a generated recovery page served by HA; offline alerts and hourly checks available (v3.9.13+).


## Automation Examples

(See services in Developer Tools for full fields.) Examples: set a one‑time dashboard URL with wake_tablet, show temporary alert overlays with auto_return_seconds, send keypad and validate via webhook, show energy panel on zone enter, start slideshow, etc.


## Performance & Battery

Recommendations: use AppDaemon dashboard + Eco profile for daily use; overlays with auto_return_seconds; slideshow intervals long in Eco (≥300s); ReloadTimeout 60–300s for dynamic pages; scale large images to device resolution; use sleep_device overnight.


## Troubleshooting

Common checks: Recovery probe URL and AppDaemon status for connection refused; sensor.*_configured_url and binary_sensor.*_dashboard_ok for incorrect screen; webhook_id and Developer Tools → Events for webhooks; force_refresh for stale images; Integration Options → Repairs for orphan sessions.

Enable debug logs:

```yaml
logger:
  logs:
    custom_components.visionect_joan: debug
```


## FAQ

- Best setup for a single dashboard? joan_generator + AppDaemon + single set_url + Eco profile.
- Do button panels show live states? No — use AppDaemon or send_status_panel.
- Other Joan models? Tested on Joan 6/13PRO.


## Development & Knowledge Base

- Knowledge base: ./docs/INTEGRATION_KNOWLEDGE.md
- Tests: tests/ (e.g. python -m pytest tests/test_url_push.py)
- Issues: GitHub Issues


## License

MIT — not an official Visionect or Home Assistant product. Tested on Joan 6/13PRO. Development assisted by AI.

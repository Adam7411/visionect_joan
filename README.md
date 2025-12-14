***
- [Visionect Server v3 (All‑in‑One) installation in Home Assistant](https://github.com/Adam7411/visionect-v3-allinone)
- [Visionect Software Suite - Installation in Proxmox](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant_EN)
- [Visionect Joan for Home Assistant add-on](https://github.com/Adam7411/visionect_joan)
- [Joan 6: AppDaemon Dashboard Generator add-on](https://github.com/Adam7411/joan_generator/blob/main/README_EN.md)
***

<div align="right">
<strong>English</strong> | <a href="README_pl.md">Polski</a>
</div>

<!-- Badges -->
<p align="center">
  <a href="https://github.com/Adam7411/visionect_joan/releases"><img alt="Release" src="https://img.shields.io/github/v/release/Adam7411/visionect_joan?style=for-the-badge"></a>
  <a href="https://github.com/Adam7411/visionect_joan"><img alt="License" src="https://img.shields.io/github/license/Adam7411/visionect_joan?style=for-the-badge"></a>
  <a href="https://hacs.xyz/"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-orange?style=for-the-badge"></a>
  <a href="https://github.com/Adam7411/visionect_joan/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/Adam7411/visionect_joan?style=for-the-badge"></a>
</p>

# Visionect Joan for Home Assistant <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Otwórz swoją instancję Home Assistant i przejdź do repozytorium w HACS." /></a>

> The `visionect_joan` integration turns the energy‑efficient e‑ink **Joan 6** tablet into a customizable information & control hub for Home Assistant: energy panel, calendar views, shopping / to‑do lists, sensor graphs, multi‑layout weather, RSS feed, camera snapshot, PIN keypad, slideshows, and interactive buttons / webhooks.

<img width="1280" height="800" alt="Joan 6 home screen" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

<p align="center">
⬇️ Hardware: Joan 6 ⬇️  
<br>
<img width="421" height="328" alt="Joan 6 e-ink tablet" src="https://github.com/user-attachments/assets/6fd88078-283a-4363-a801-71250b8211f4" />
</p>

---

## Table of Contents
1. [Purpose & Overview](#purpose--overview)  
2. [Key Features](#key-features)  
3. [Screenshots](#screenshots)  
4. [Installation](#installation)  
5. [Visionect Software Suite (VSS) Setup](#visionect-software-suite-vss-setup)  
6. [Predefined Views](#predefined-views)  
7. [Entities](#entities)  
8. [Services – Summary](#services--summary)  
9. [Service Details](#service-details)  
10. [Interactive Layer & Back Priority](#interactive-layer--back-priority)  
11. [Automation Examples](#automation-examples)  
12. [Performance & Battery](#performance--battery)  
13. [Security & Webhooks](#security--webhooks)  
14. [Troubleshooting](#troubleshooting)  
15. [FAQ](#faq)  
16. [License](#license)  

---

## Purpose & Overview

The integration acts as a bridge between Home Assistant and the Visionect Software Suite (VSS). It renders dynamic, e‑ink‑optimized screens on the Joan 6 tablet triggered by context (events, zones, sensor changes, time). Instead of loading a generic dashboard, you generate a complete, static or semi‑static “screen” (energy panel, interactive to‑do list, weather with graph, keypad PIN, 12‑button action panel, etc.).

---

## Key Features

- Full screen content control: any URL, local pages (AppDaemon, `/local/`, embedded Lovelace), images, inline `data:text/html`.
- Optimized built‑in views:
  - Weather: detailed summary, daily forecast list, 24h temperature graph panel.
  - Calendar: multi‑day list, minimalist list, monthly grid + daily overlay.
  - To‑Do / Shopping list with interactive toggling via webhook.
  - Energy panel (current usage + production/import/export/consumption daily metrics).
  - Entity status panel (icons + names + values + translated states).
  - Sensor history graph (line/bar; multi entity; orientation aware).
  - Paginated RSS / Atom feed.
  - QR code (guest Wi‑Fi, device pairing).
  - PIN keypad (webhook → HA automation validates code).
  - Up to 12 action buttons (stateless webhooks).
- Interactive overlay: bottom bar (← Back / ✔ Center / → Action) or full-screen tap-to-back / tap-to-action.
- Live preview (`camera` entity) – current rendered screen as a still image.
- UI configuration (no YAML): predefined views + global Main Menu URL.
- Management utilities: display rotation, clear WebKit cache, force refresh, sleep/wake.
- Rendering controls: encoding (bit depth), dithering method.
- Automatic cleanup of temporary media (snapshots / graphs) in `www/`.

<details>
  <summary>Screenshot: bottom action bar</summary>
  <img width="561" height="705" alt="Bottom action bar" src="https://github.com/user-attachments/assets/dd217c23-d402-43a8-acb3-1bf0ea841c74" />
</details>

<details>
  <summary>Predefined view options</summary>
  <img width="838" height="566" alt="Integration options" src="https://github.com/user-attachments/assets/ef9ef69b-413d-4ca4-86d9-373d3117880a" />
</details>

---

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
  <img width="758" height="1024" alt="QR code view" src="https://github.com/user-attachments/assets/f3c19b37-0dad-4bd9-89ac-271c016d4211" />
  <img width="758" height="1024" alt="Sensor graph" src="https://github.com/user-attachments/assets/7819468a-c33b-409f-9845-2256def6a134" />
  <img width="758" height="1024" alt="Text message layout" src="https://github.com/user-attachments/assets/0d735375-caf9-4e8c-a4c8-6b5008a88f9b" />
  <img width="758" height="1024" alt="Weather alternate layout" src="https://github.com/user-attachments/assets/6267ae6c-0263-4fb0-8189-c638cc5d685d" />
  <img width="758" height="1024" alt="Entity status panel" src="https://github.com/user-attachments/assets/8e35f996-26a3-4e4f-9951-1938530a9028" />
  <img width="758" height="1024" alt="Energy panel" src="https://github.com/user-attachments/assets/acb78d0e-ca38-451e-8fc2-f64f479d1c78" />
  <img width="758" height="1024" alt="Live preview camera" src="https://github.com/user-attachments/assets/3bd6d185-33ae-4407-98c5-9b70821c27b9" />
  <img width="758" height="1024" alt="Diagnostics & battery" src="https://github.com/user-attachments/assets/fe7eb843-a6f1-4ef7-a3a4-e006b93c528f" />
</details>

---

## Installation

### Via HACS (recommended)
1. Install [HACS](https://hacs.xyz/) if not already.
2. In HACS → Integrations → ⋮ → Custom repositories.
3. Add `Adam7411/visionect_joan` as “Integration”.
4. Search “Visionect Joan” → Install.
5. Restart Home Assistant.

### Manual
1. Download the latest release archive.
2. Extract to: `/config/custom_components/visionect_joan/`.
3. Restart Home Assistant.

---

## Visionect Software Suite (VSS) Setup

1. Go to Home Assistant: Settings → Devices & Services.
2. Click “+ Add Integration”.
3. Search “Visionect Joan”.
4. Provide connection details (see VSS install guide: [Visionect Software Suite Installation](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant_EN)):
   - Server host: `IP:8081` (default Visionect Management API port 8081).
   - Username (e.g. `admin`) & Password OR API Key & Secret.
   - Create API key/secret in VSS → Users → Add new API key.

<img width="1567" height="425" alt="Integration step 1" src="https://github.com/user-attachments/assets/37bbcdb7-e820-4275-b7ed-efc9248048e5" />
<img width="575" height="615" alt="Integration step 2" src="https://github.com/user-attachments/assets/a70ccc87-bbff-4fa4-aec5-f4e602709f19" />

---

## Predefined Views

Configure in integration Options:
1. Settings → Devices & Services → Visionect Joan → Configure.
2. “Add view” → Name + URL.
3. Names are selectable via the “Choose view” select entity or referenced in services (`url` / `predefined_url`).

Legacy “Name: URL” line format is auto‑parsed.

---

## Entities

| Entity Type | Purpose | Notes |
|-------------|---------|-------|
| `camera` | Live screen preview | Encodes current display as PNG |
| `sensor` | Online state, battery, temperature, RSSI, uptime, voltage, storage, URL, diagnostics | Some disabled by default |
| `binary_sensor` | Charging status | `is_charging` |
| `text` | Device name | Writes directly to device via API |
| `number` | `ReloadTimeout` (session refresh interval) | 0–86400 s |
| `select` | View switch / Back target / dithering / bit depth | Session options (encoding/dithering) |
| `button` | Force Refresh / Reboot / Clear Web Cache | Reboot & Clear disabled by default |
| (internal) | Views options flow | Options UI only |

<details>
  <summary>Show entity screenshot</summary>
  <img width="658" height="1002" alt="Entity list" src="https://github.com/user-attachments/assets/67de6efe-ffd5-4757-8a82-71e46f039943" />
</details>

---

## Services – Summary

| Service | Category | Interactive Overlay | Short Description |
|---------|----------|---------------------|-------------------|
| `visionect_joan.set_url` | Navigation | Optional | Set URL or predefined view |
| `visionect_joan.send_text` | Content | Yes | Text + optional image layout (Jinja2) |
| `visionect_joan.send_image_url` | Content | Yes | Single image (PNG/JPG/SVG/WebP) |
| `visionect_joan.send_camera_snapshot` | Content | Yes | Snapshot from HA camera entity |
| `visionect_joan.send_status_panel` | Status | Yes | Icons + state values |
| `visionect_joan.send_energy_panel` | Energy | Yes | Current usage + daily metrics |
| `visionect_joan.send_weather` | Weather | Yes | 3 layouts (detail/list/graph) |
| `visionect_joan.send_calendar` | Calendar | Yes | List / minimalist / monthly grid |
| `visionect_joan.send_todo_list` | Lists | Yes | To‑Do / Shopping (interactive toggle) |
| `visionect_joan.send_sensor_graph` | History | Yes | Line/bar graph multi entity |
| `visionect_joan.send_rss_feed` | RSS | Yes | Paginated feed items |
| `visionect_joan.send_qr_code` | QR | Yes | QR + caption |
| `visionect_joan.start_slideshow` | Navigation | Yes | Rotate views / URLs |
| `visionect_joan.send_keypad` | Input | Yes (no Back by default) | PIN keypad → webhook |
| `visionect_joan.send_button_panel` | Actions | Yes | Up to 12 stateless webhook buttons |
| `visionect_joan.set_session_options` | Render | N/A | Bit depth / dithering |
| `visionect_joan.clear_web_cache` | Maintenance | N/A | Clear WebKit cache (optional restart) |
| `visionect_joan.force_refresh` | Maintenance | N/A | Restart session |
| `visionect_joan.set_display_rotation` | Maintenance | N/A | Rotate & reboot |
| `visionect_joan.clear_display` | Maintenance | N/A | Blank screen |
| `visionect_joan.sleep_device` / `wake_device` | Power | N/A | Sleep / wake tablet |

---

## Service Details

Expandable sections with screenshots (full field documentation lives in `services.yaml` & HA UI).

### Content Display

- `visionect_joan.send_button_panel`  
  - Grid of up to 12 configurable buttons. Each has a label, icon (from `svg_button`), and individual `webhook_id`.  
  - Tip: Each webhook must have a corresponding automation (Webhook trigger) to act.  
  - ⚠ Stateless: The button panel does not reflect live entity states (use status panels / dashboards for state feedback).
  <details>
    <summary>Show screenshot</summary>
    <img width="1214" height="3814" alt="Button panel service form" src="https://github.com/user-attachments/assets/fdbb51ba-0f4b-4db4-98bd-e5d01b34ce77" />
  </details>

***

- `visionect_joan.set_url`  
  - Sets any URL or predefined view name. Case‑insensitive matching for view names.  
  - Edit predefined views: Settings → Devices & Services → Visionect Joan → Configure.
  <details>
    <summary>Show screenshot</summary>
    <img width="1220" height="595" alt="Set URL service form" src="https://github.com/user-attachments/assets/bfdf8101-1b45-45e0-ab1a-46c7ab79d96b" />
  </details>

***

- `visionect_joan.send_text`  
  - Render styled text (Jinja2 supported), optional image, multiple layouts (text_only, image_top, left/right etc.).
  <details>
    <summary>Show screenshot</summary>
    <img width="1225" height="2066" alt="Send text service form" src="https://github.com/user-attachments/assets/9912da53-becf-4932-ab7e-7f0a17a681d7" />
  </details>

***

- `visionect_joan.send_image_url`  
  - Display an image from URL (supported: png, jpg, jpeg, gif, svg, webp). For local files use `http://<HA_IP>:8123/local/...`.
  <details>
    <summary>Show screenshot</summary>
    <img width="1234" height="1448" alt="Send image URL form" src="https://github.com/user-attachments/assets/9da6769f-668a-4adb-9edf-b5fdc5851d55" />
  </details>

***

- `visionect_joan.send_camera_snapshot`  
  - Captures a snapshot from a HA camera entity, renders with caption & optional rotation.
  <details>
    <summary>Show screenshot</summary>
    <img width="1223" height="1472" alt="Camera snapshot form" src="https://github.com/user-attachments/assets/6cec8748-a586-46c2-8f2b-2bcf-25237e08" />
  </details>

***

- `visionect_joan.send_status_panel`  
  - Custom entity status panel with friendly names, icons, translated states.
  <details>
    <summary>Show screenshot</summary>
    <img width="1230" height="1416" alt="Status panel form" src="https://github.com/user-attachments/assets/bb21ddb7-77bf-4db1-bc57-9ecf2c2d5021" />
  </details>

***

- `visionect_joan.send_energy_panel`  
  - Energy summary: current usage + daily production/import/export/consumption. Portrait recommended.
  <details>
    <summary>Show screenshot</summary>
    <img width="1230" height="1423" alt="Energy panel form" src="https://github.com/user-attachments/assets/66b3f26d-f5c3-4276-b837-de6b85cf9fcf" />
  </details>

***

- `visionect_joan.send_weather`  
  - Layouts: detailed summary, daily forecast list, temperature graph panel (24h).
  <details>
    <summary>Show screenshot</summary>
    <img width="1225" height="1237" alt="Weather form" src="https://github.com/user-attachments/assets/588660d8-e0ff-48b3-b7a5-6d9432cd2329" />
  </details>

***

- `visionect_joan.send_calendar`  
  - Renders list (1–31 days) or monthly grid with daily drill‑down.
  <details>
    <summary>Show screenshot</summary>
    <img width="1207" height="801" alt="Monthly calendar form" src="https://github.com/user-attachments/assets/83f5d345-69ef-42af-84d3-f7f4f3c3b1a0" />
  </details>

***

- `visionect_joan.send_todo_list`  
  - To‑Do / Shopping List items with optional interactive checkbox toggling via webhook.
  <details>
    <summary>Show screenshot</summary>
    <img width="1216" height="1201" alt="To-do list form" src="https://github.com/user-attachments/assets/6735340b-bec9-47a6-a72e-07d16da20943" />
  </details>

***

- `visionect_joan.send_sensor_graph`  
  - Historical graph (line/bar) for selected sensors. Auto adjusts orientation spacing.
  <details>
    <summary>Show screenshot</summary>
    <img width="1219" height="1895" alt="Sensor graph form" src="https://github.com/user-attachments/assets/c5507b3b-28e6-47a1-a88a-11d936f2f35b" />
  </details>

***

- `visionect_joan.send_rss_feed`  
  - Fetches and paginates RSS/Atom feed items (title list).
  <details>
    <summary>Show screenshot</summary>
    <img width="1225" height="1255" alt="RSS feed form" src="https://github.com/user-attachments/assets/56316ce1-8350-49d5-a624-2f7a880b8a4e" />
  </details>

***

### Interactivity & Navigation

- `visionect_joan.send_qr_code`  
  - QR generation with caption (above/below).
  <details>
    <summary>Show screenshot</summary>
    <img width="1223" height="1765" alt="QR code form" src="https://github.com/user-attachments/assets/a55360c9-9f17-4b81-baf9-b990692bc2a0" />
  </details>

***

- `visionect_joan.start_slideshow`  
  - Loops through view names or local URLs.  
  - Note: Many external sites block iframe embedding (X-Frame-Options / CSP).
  <details>
    <summary>Show screenshot</summary>
    <img width="606" height="729" alt="Slideshow form" src="https://github.com/user-attachments/assets/91d25761-2709-417b-9a2c-edf2104c5869" />
  </details>

***

- `visionect_joan.send_keypad`  
  - Full-screen numeric keypad sending JSON `{"pin": "1234"}` to webhook.
  <details>
    <summary>Show screenshot</summary>
    <img width="1220" height="632" alt="Keypad form" src="https://github.com/user-attachments/assets/5df2b9d9-ae6e-4a60-9f9f-c787f7658135" />
  </details>

***

### Rendering & Management

- `visionect_joan.set_session_options` – Set session rendering parameters (`encoding`, `dithering`).  
- `visionect_joan.clear_web_cache` – Clear WebKit cache (optional restart).  
- `visionect_joan.force_refresh` – Restart current session (force reload).  
- `visionect_joan.set_display_rotation` – Persist orientation (reboot required).  
- `visionect_joan.clear_display` – Blank white screen.  
- `visionect_joan.sleep_device` / `wake_device` – Power management.

---

## Interactive Layer & Back Priority

Back target resolution priority:
1. `back_button_url` provided in the service call
2. Per‑device select entity `Back button target`
3. Global `Main menu URL` (integration options)

Hiding buttons:
- `click_anywhere_to_action: true` → full screen triggers Action webhook.
- `click_anywhere_to_return: true` → full screen navigates back.
When either is enabled, the bottom bar is hidden.

---

## Automation Examples

Annotated with inline comments (`#`).

### 1. Simple text message
```yaml
service: visionect_joan.send_text                  # Send a styled text screen
target:
  device_id: 00000000000000000000000000000000       # Replace with your device_id
data:
  message: "Hello!\n{{ now().strftime('%H:%M') }}"  # Jinja2 template for current time
  text_size: 42                                     # Font size (px)
```

### 2. Toggle a light with right button (→)

Automation reacting to the webhook:
```yaml
alias: "Joan: living room light"            # Friendly name
trigger:
  - platform: webhook
    webhook_id: joan_light_on               # Must match action_webhook_id below
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room          # Light entity to control
```

Display the screen with actionable button:
```yaml
service: visionect_joan.send_text
target:
  device_id: 00000000000000000000000000000000  # Joan device
data:
  message: "Living room light"              # On-screen label
  action_webhook_id: joan_light_on          # Triggers the automation above
  add_back_button: true                     # Show ← Back
  back_button_url: MainMenu                 # View name or full URL
```

### 3. PIN keypad with success navigation

Initial keypad display:
```yaml
service: visionect_joan.send_keypad
target:
  device_id: 266a72218733bb9a056aff49bf6f8e2d  # Joan device
data:
  title: "PIN"
  action_webhook_id: joan_pin                  # Webhook receiving PIN JSON
```

Automation validating PIN:
```yaml
alias: "PIN → access"
mode: single
trigger:
  - platform: webhook
    webhook_id: joan_pin                       # Must match keypad webhook
variables:
  correct_pin: "321"                           # Consider storing this securely
action:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ trigger.json.pin == correct_pin }}"  # Compare PIN
        sequence:
          - service: visionect_joan.set_url
            target:
              device_id: 266a72218733bb9a056aff49bf6f8e2d
            data:
              url: HomePanel                   # Predefined view name
    default:
      - service: visionect_joan.send_text
        target:
          device_id: 266a72218733bb9a056aff49bf6f8e2d
        data:
          message: "Wrong PIN!"
          text_size: 48
          add_back_button: true
          back_button_url: MainMenu
      - delay: "00:00:03"                      # Short pause
      - service: visionect_joan.send_keypad    # Redisplay keypad
        target:
          device_id: 266a72218733bb9a056aff49bf6f8e2d
        data:
          title: "PIN"
          action_webhook_id: joan_pin
```

### 4. Energy panel on zone entry
```yaml
alias: "Arrive home → Energy panel"          # Trigger when person enters home zone
trigger:
  - platform: zone
    entity_id: person.alex                   # Person entity
    zone: zone.home
    event: enter
action:
  - service: visionect_joan.send_energy_panel
    target:
      device_id: 00000000000000000000000000000000
    data:
      power_usage_entity: sensor.house_power            # Current power (W/kW)
      daily_consumption_entity: sensor.energy_daily_consumption
      add_back_button: true
      back_button_url: MainMenu
```

### 5. Slideshow rotating information
```yaml
service: visionect_joan.start_slideshow
target:
  device_id: 00000000000000000000000000000000
data:
  views: |                                      # Each line: view name OR local URL
    MainMenu
    WeatherPanel
    http://192.168.1.10:8123/local/announcements.png
  seconds_per_slide: 45                         # Slide duration (sec) – shorter = more battery drain
  loop: true                                    # Return to first slide after last
  add_back_button: true
```

### 6. Camera snapshot on motion
```yaml
alias: "Motion → Snapshot"
trigger:
  - platform: state
    entity_id: binary_sensor.hall_motion        # Motion sensor
    to: "on"
action:
  - service: visionect_joan.send_camera_snapshot
    target:
      device_id: 00000000000000000000000000000000
    data:
      camera_entity: camera.hallway             # Camera entity
      caption: "Motion: {{ now().strftime('%H:%M:%S') }}"
      add_back_button: true
      back_button_url: MainMenu
```

---

## Performance & Battery

| Aspect | Recommendation |
|--------|---------------|
| `ReloadTimeout` | 60–300 s for info panels; use 0 only for static display (manual change) |
| Slideshow interval | ≥ 30 s per slide; avoid rapid cycling |
| Encoding | `1` for text/status; `4` only when grayscale detail needed |
| Dithering | `none` for clarity; `floyd-steinberg` for photographic/grayscale content |
| Large images | Pre-scale server side to device resolution |
| Night usage | Reduce refreshes via time or presence automations |
| Sleep mode | Use `sleep_device` during long inactivity (overnight) |

---

## Security & Webhooks

- HA webhooks (`/api/webhook/<id>`) are unauthenticated by default – treat them as local triggers.
- Do not expose port 8123 publicly without reverse proxy + authentication.
- Use long, non‑guessable `webhook_id` strings for sensitive actions.
- Do not log raw PIN values; compare via templates or store hashed.
- If VSS runs on a separate host, ensure `internal_url` in HA is correct so webhook URLs resolve properly.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Button press ignored | Incorrect `webhook_id` or missing automation | Check Developer Tools → Events → webhook |
| Screen not updating | Stale session | Use `force_refresh` or adjust `ReloadTimeout` |
| Old styles/images persist | WebKit cache | `clear_web_cache` (optionally restart session) |
| Empty graph | Recorder/history disabled | Enable history recording for sensors |
| Wrong orientation after change | Session not rebuilt | Use `set_display_rotation` → reboot completes automatically |
| PIN always fails | Automation not parsing JSON | Inspect `trigger.json` in Template Editor |
| RSS feed empty | Feed unreachable or blocked | Open URL in browser, check logs |

Enable debug logging:
```yaml
logger:
  logs:
    custom_components.visionect_joan: debug
```

---

## FAQ

**Do button panels show live entity states?**  
No—panels are stateless (one‑way). Use `send_status_panel` or a custom dashboard for real‑time states.

**Is e‑ink “ghosting” normal?**  
Frequent high‑contrast refreshes cause artifacts; reduce update frequency and prefer encoding=1 for crisp text.

**Other Joan models supported?**  
Tested on Joan 6; other models may partially work but are not verified yet.

**External site not visible in slideshow?**  
Likely blocked by X‑Frame-Options / CSP. Use local HA/AppDaemon URLs or predefined views.

**Can I send arbitrary HTML?**  
Yes – `data:text/html,<html>...</html>` via `set_url` or generate using existing services.

---

## License

MIT

---

- The project is not an official integration of Visionect or Home Assistant.
- Tested on **Joan 6**; other models were not verified.
- AI was used for faster development.
- [Visionect Software Suite - installation](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant)
- [Joan 6 dashboard Generator](https://github.com/Adam7411/joan_generator/blob/main/README.md)


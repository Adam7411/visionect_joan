<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
</div>

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and go to the repository in HACS." /></a>

# Visionect Joan for Home Assistant

<img width="1280" height="800" alt="Sample home screen on a Joan 6 tablet" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

<p align="center">

<br>

⬇️ Visionect Joan 6 ⬇️
 
<img width="421" height="328" alt="Joan 6 hardware" src="https://github.com/user-attachments/assets/6fd88078-283a-4363-a801-71250b8211f4" />

***
👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇
<details>
  <summary>Show screenshots</summary> 
  
  <img width="758" height="1024" alt="Home panel" src="https://github.com/user-attachments/assets/fd78c164-6691-477e-84e1-e47a1f70a8cc" />
  <img width="758" height="1024" alt="RSS view" src="https://github.com/user-attachments/assets/f5a1f528-8201-47a0-9f7a-15b435f9152c" />
  <img width="758" height="1024" alt="Weather" src="https://github.com/user-attachments/assets/2aca216e-e0d2-454e-b089-ee1eb04e947b" />
  <img width="758" height="1024" alt="PIN keypad" src="https://github.com/user-attachments/assets/c765b34f-ed4e-48d7-a59d-ff8ecd67aa7c" />
  <img width="758" height="1024" alt="Calendar" src="https://github.com/user-attachments/assets/a5f3b53e-1b33-414b-8173-3fac794cbd46" />
  <img width="758" height="1024" alt="Camera snapshot" src="https://github.com/user-attachments/assets/9c087661-69b0-463b-937e-19b2567cab6b" />
  <img width="758" height="1024" alt="QR code" src="https://github.com/user-attachments/assets/f3c19b37-0dad-4bd9-89ac-271c016d4211" />
  <img width="758" height="1024" alt="Sensor graph" src="https://github.com/user-attachments/assets/7819468a-c33b-409f-9845-2256def6a134" />
  <img width="758" height="1024" alt="Text message" src="https://github.com/user-attachments/assets/0d735375-caf9-4e8c-a4c8-6b5008a88f9b" />
  <img width="758" height="1024" alt="Weather layout 2" src="https://github.com/user-attachments/assets/6267ae5-0263-4fb0-8189-c638cc5d685d" />
  <img width="758" height="1024" alt="Status panel" src="https://github.com/user-attachments/assets/8e35f996-26a3-4e4f-9951-1938530a9028" />
  <img width="758" height="1024" alt="Energy panel" src="https://github.com/user-attachments/assets/acb78d0e-ca38-451e-8fc2-f64f479d1c78" />
  <img width="758" height="1024" alt="Live preview" src="https://github.com/user-attachments/assets/3bd6d185-33ae-4407-98c5-9b70821c27b9" />
  <img width="758" height="1024" alt="Battery/diagnostics" src="https://github.com/user-attachments/assets/fe7eb843-a6f1-4ef7-a3a4-e006b93c528f" />
  
  
</details>

***

</p>

The `visionect_joan` integration turns the energy‑efficient e‑ink tablet **Joan 6** into a powerful, fully customizable information hub for your smart home.

Thanks to rich services, you can build advanced automations: show the energy panel when you get home, display your shopping list when you enter the kitchen, send a camera snapshot when motion is detected, and automatically return to the main screen.

***

## Key features

- Full screen control: send any web URL, local dashboards (e.g., AppDaemon), or single images.
- Dynamic e‑ink‑optimized views: weather, calendar (including monthly grid), tasks (To‑Do/Shopping List), energy panel, entity status panel, sensor history graphs.
- Interactivity: a bottom bar with a “Back” button (←) and two action buttons (✔ and →), or optionally “tap anywhere” to run an action or go back.

<details>
  <summary>Show screenshot</summary>

  <img width="561" height="705" alt="Bottom action bar with back/action buttons" src="https://github.com/user-attachments/assets/dd217c23-d402-43a8-acb3-1bf0ea841c74" />

</details>

- Two webhooks (actions): separate IDs for the right (→) and center (✔) buttons.
- Power management: sleep/wake device, and set the session refresh interval.
- Live preview: the `camera` entity returns the device’s current screen image.
- UI configuration: set predefined views and the main menu URL in integration options (no YAML).

<details>
  <summary>Show screenshot</summary>

  <img width="838" height="566" alt="Integration options with predefined views" src="https://github.com/user-attachments/assets/ef9ef69b-413d-4ca4-86d9-373d3117880a" />


</details>


***

## Available entities

- `camera` – Live screen preview.
- `sensor`
  - Online/offline, battery, temperature, RSSI, uptime, battery voltage, storage (free/total/used), “configured URL”, last seen.
  - Diagnostics: last connect reason, last error code.
  - Display orientation (descriptive value).
- `binary_sensor`
  - Charging status (is the charger connected).
- `text`
  - Device name (change directly from HA).
- `number`
  - Screen refresh (`ReloadTimeout`) – how often the session refreshes (s).
- `select`
  - Choose view – select a predefined view for the device.
  - Back button target – default “Back” destination.
  - Dithering Method – dithering algorithm (e.g., none/bayer/floyd‑steinberg).
  - Bit Depth – grayscale depth (normally 1 or 4).
- `button`
  - Force Refresh – immediately restart the renderer session.
  - Reboot Device – reboot device.
  - Clear Web Cache – clear web browser cache.

<details>
  <summary>Show screenshot</summary>

  <img width="658" height="1002" alt="Screenshot" src="https://github.com/user-attachments/assets/67de6efe-ffd5-4757-8a82-71e46f039943" />
</details>



---

## Services

Below is the full list of services available in the integration (many can be combined with the interactive overlay: buttons, webhooks, click‑anywhere):

### Content display

- `visionect_joan.set_url`
  - Sets any URL or the name of a predefined view.
  - Tip: view names are matched case‑insensitively. Add/edit views in: Settings → Devices & Services → Visionect Joan → Configure.

<details>
  <summary>Show screenshot</summary>

  <img width="1220" height="595" alt="Service: set_url" src="https://github.com/user-attachments/assets/bfdf8101-1b45-45e0-ab1a-46c7ab79d96b" />
</details>

***

- `visionect_joan.send_text`
  - Sends formatted text (supports Jinja2), optionally with an image and various layouts (text only, text + image).
  - Tips: use fonts that read well on e‑ink; for images, adjust `image_zoom` and `image_rotation`.
 
<details>
  <summary>Show screenshot</summary>

  <img width="1225" height="2066" alt="Service: send_text" src="https://github.com/user-attachments/assets/9912da53-becf-4932-ab7e-7f0a17a681d7" />

</details>

***

- `visionect_joan.send_image_url` ➊
  - Displays an image from a URL (PNG/JPG/SVG/WebP supported).
  - Tips: for local images, use `http://<HA_IP>:8123/local/...`.
 
<details>
  <summary>Show screenshot</summary>

  <img width="1234" height="1448" alt="Service: send_image_url" src="https://github.com/user-attachments/assets/9da6769f-668a-4adb-9edf-b5fdc5851d55" />


</details>

***

- `visionect_joan.send_camera_snapshot`
  - Captures a snapshot from a `camera` entity and displays it on the screen (with caption and image rotation).
 
<details>
  <summary>Show screenshot</summary>

  <img width="1223" height="1472" alt="Service: send_camera_snapshot" src="https://github.com/user-attachments/assets/6cec8748-a586-46c2-8f2b-2bcf-25237e08" />

</details>

***

- `visionect_joan.send_status_panel`
  - Status panel for any entities: icons + names + values (with translations for on/off/open/…).
 
<details>
  <summary>Show screenshot</summary>

  <img width="1230" height="1416" alt="Service: send_status_panel" src="https://github.com/user-attachments/assets/bb21ddb7-77bf-4db1-bc57-9ecf2c2d5021" />

</details>

***

- `visionect_joan.send_energy_panel`
  - Large energy panel (current power + cards: production/import/export/daily consumption). Looks great in portrait.

<details>
  <summary>Show screenshot</summary>

  <img width="1230" height="1423" alt="Service: send_energy_panel" src="https://github.com/user-attachments/assets/66b3f26d-f5c3-4276-b837-de6b85cf9fcf" />

</details>

***

- `visionect_joan.send_weather`
  - 3 layouts: detailed summary, daily forecast list, panel with a 24 h graph (auto day/night icons).

<details>
  <summary>Show screenshot</summary>

  <img width="1225" height="1237" alt="Service: send_weather" src="https://github.com/user-attachments/assets/588660d8-e0ff-48b3-b7a5-6d9432cd2329" />

</details>

***

- `visionect_joan.send_calendar`
  - Event list (1–31 days) or a monthly grid with a per‑day view.

<details>
  <summary>Show screenshot</summary>

  <img width="1920" height="2252" alt="Service: send_calendar" src="https://github.com/user-attachments/assets/b6431600-0556-4052-abdf-53eacf79397e" />

</details>

***

- `visionect_joan.send_todo_list`
  - To‑Do list (including Shopping List). Large, readable items; supports interactive toggling via webhook (see below).

<details>
  <summary>Show screenshot</summary>

  <img width="1216" height="1201" alt="Service: send_todo_list" src="https://github.com/user-attachments/assets/6735340b-bec9-47a6-a72e-07d16da20943" />

</details>

***

- `visionect_joan.send_sensor_graph`
  - History graph for selected sensors (line or bar), automatically adapted to the screen orientation.

<details>
  <summary>Show screenshot</summary>

  <img width="1219" height="1895" alt="Service: send_sensor_graph" src="https://github.com/user-attachments/assets/c5507b3b-28e6-47a1-a88a-11d936f2f35b" />

</details>

***

- `visionect_joan.send_rss_feed` ➋
  - Fetches and displays the latest items from an RSS/Atom feed (pagination, header, icons). Provide `feed_url`, `max_items`, and optionally a custom title.

<details>
  <summary>Show screenshot</summary>

  <img width="1225" height="1255" alt="Service: send_rss_feed" src="https://github.com/user-attachments/assets/56316ce1-8350-49d5-a624-2f7a880b8a4e" />

</details>

***
### Interactivity and navigation

- `visionect_joan.send_qr_code`
  - Generates a QR code (e.g., guest Wi‑Fi) with an optional caption (above/below).
    
<details>
  <summary>Show screenshot</summary>

  <img width="1223" height="1765" alt="Service: send_qr_code" src="https://github.com/user-attachments/assets/a55360c9-9f17-4b81-baf9-b990692bc2a0" />

</details>

***

- `visionect_joan.start_slideshow` ➌
  - Plays a list of views (predefined names or full URLs) in a loop with a per‑slide display time.
  - Tip: shorter intervals = more frequent e‑ink refreshes and higher battery use. Recommended ≥ 30 s.
 
<details>
  <summary>Show screenshot</summary>

  <img width="1228" height="1457" alt="Service: start_slideshow" src="https://github.com/user-attachments/assets/106d5ae9-8d8a-4b3f-8f5e-206aab76e0c8" />

</details>

***

- `visionect_joan.send_keypad` ➍
  - Full‑screen numeric keypad. The entered PIN is POSTed to a Home Assistant webhook (`trigger.json.pin`).
  - Tip: you need an automation to validate the code.
  
 <details>
  
  <summary><strong>Example: PIN automation (webhook + keypad) for Visionect Joan</strong></summary>

This example shows how to use `visionect_joan.send_keypad` to enter a PIN on the Joan screen and validate it in an automation triggered by a webhook. If the PIN is correct — the device navigates to a target view; if it’s wrong — a message appears and the keypad returns after a short delay.

— Requirements:
- The Visionect Joan integration is installed and the device (Joan 6) is added.
- You know your tablet’s `device_id` (Settings → Devices & Services → your device → three dots → Copy device ID).
- A view is defined in the integration options (or you can use a full URL).

— How to show the keypad for the first time:
- Call `visionect_joan.send_keypad` once with:
  - device_id: your tablet
  - title: e.g., “Enter PIN”
  - action_webhook_id: e.g., “joan_pin” (must match the webhook in the automation)

— Automation YAML (paste into HA’s automation YAML editor and replace values in comments):

```
alias: PIN code automation for Visionect Joan
mode: single

trigger:
  - platform: webhook
    # SET YOUR WEBHOOK ID (must match visionect_joan.send_keypad → action_webhook_id):
    webhook_id: joan_pin

action:
  - choose:
      # Condition: correct PIN?
      - conditions:
          - condition: template
            # SET YOUR PIN:
            value_template: "{{ trigger.json.pin == '321' }}"
        sequence:
          # SUCCESS: navigate to a view (predefined view name or full URL)
          - action: visionect_joan.set_url
            target:
              # SET YOUR DEVICE_ID:
              device_id: 266a72218733bb9a056aff49bf6f8e2d
            data:
              # Change to a view name (e.g., KuchniaGóra) or provide a full URL
              url: KuchniaGóra
    default:
      # WRONG PIN: show a message
      - action: visionect_joan.send_text
        target:
          device_id: 266a72218733bb9a056aff49bf6f8e2d
        data:
          message: "Wrong code!"
          text_size: 48
          # (optional) you can add an overlay with Back/action buttons:
          # add_back_button: true
          # back_button_url: "ViewNameOrURL"
      # short pause
      - delay: "00:00:03"
      # Show the keypad again (same webhook_id as in the trigger)
      - action: visionect_joan.send_keypad
        target:
          device_id: 266a72218733bb9a056aff49bf6f8e2d
        data:
          title: "Try again"
          action_webhook_id: joan_pin
```

— Tips and security:
- Webhooks don’t require a token — best used on a local network or behind a reverse proxy/ACL.
- You can store the PIN more safely (e.g., `input_text` helper or secrets) and compare via a template.
- Instead of a view name in `data.url`, you may use a full URL (e.g., an AppDaemon dashboard).

</details>
 

<details>
  <summary>Show screenshot</summary>

  <img width="1220" height="632" alt="Service: send_keypad call" src="https://github.com/user-attachments/assets/5df2b9d9-ae6e-4a60-9f9f-c787f7658135" />

</details>

***

### Rendering parameters and management

- `visionect_joan.set_session_options` ➎
  - Sets session parameters: `encoding` (bit depth, usually “1” or “4”) and `dithering` (none/bayer/floyd‑steinberg).
  - Tip: 1‑bit = highest contrast and speed; 4‑bit = 16 grayscale levels (better graphics).

- `visionect_joan.clear_web_cache`
  - Clears the WebKit cache for selected devices; optionally set `restart_session: true`.
  - Tip: useful when “stale” images or styles get stuck.

- `visionect_joan.force_refresh`
  - Immediately restarts the session (refreshes the current view).

- `visionect_joan.set_display_rotation`
  - Permanently changes device screen orientation (requires a short device reboot).

- `visionect_joan.clear_display`
  - Clears the screen to a blank background (white).

- `visionect_joan.sleep_device` / `visionect_joan.wake_device`
  - Sleep/wake device (save battery; set sleep duration in seconds).

➊ `send_image_url` – accepted extensions: png, jpg, jpeg, gif, svg, webp (format support also depends on the Visionect renderer version).

➋ `send_rss_feed` – the integration parses the feed (Feedparser), builds lists and pagination; great for quick “news boards”.

➌ `start_slideshow` – accepts view names (from “Views & options”) and/or full URLs (one per line).

➍ `send_keypad` – the HA automation must use a Webhook trigger; in conditions: `{{ trigger.json.pin == '1234' }}`.

➎ `set_session_options` – leaving a parameter empty keeps the current value unchanged.

---

## Interactive overlay (buttons, click‑anywhere, webhooks)

Every content service can add an “overlay” with buttons:
- “Back” (←) — return to a URL determined by:
  1) `back_button_url` in the service call,
  2) the `Back button target` selector entity (per device),
  3) the global “Main menu URL” set in the integration options.
- “Action” (→) — triggers the `action_webhook_id` webhook.
- “Center” (✔) — triggers the `action_webhook_2_id` webhook.
- “Click anywhere” — can trigger an action (webhook) or serve as a quick “return”.

<details>
 
  <summary><strong>Example: action button (webhook) → turn on a light</strong></summary>

This example shows how to use `action_webhook_id` in a view sent to Joan so that pressing the right button (→) turns on a light in Home Assistant.

Works with most display services (send_text, send_status_panel, send_weather, send_image_url, send_todo_list, send_calendar, send_energy_panel, send_sensor_graph, start_slideshow). Below we use `send_text`.

— Step 1. Automation: listen for the webhook and turn on the light

Copy into the automation YAML editor (change WEBHOOK_ID and the light entity):

```
alias: "Joan: turn on light via button"
mode: single

trigger:
  - platform: webhook
    # SET YOUR WEBHOOK ID (must match action_webhook_id in step 2):
    webhook_id: joan_light_on

action:
  - service: light.turn_on
    target:
      entity_id: light.your_light  # e.g., light.kitchen_ceiling
    data:
      brightness_pct: 100  # optional
```

— Step 2. Send a view to Joan with an action button (→)

Call the `visionect_joan.send_text` service (Developer Tools → Services) with `action_webhook_id: joan_light_on`. This adds the bottom bar; the right button (→) will POST a webhook to HA.

```
service: visionect_joan.send_text
data:
  message: "Turn on the light"
  add_back_button: true                # optionally show 'Back' (←)
  back_button_url: "Main"              # predefined view name or full URL (optional)
  action_webhook_id: joan_light_on     # MUST match 'webhook_id' in the automation
target:
  device_id: 00000000000000000000000000000000  # <- your Joan device_id
```

Variant: make the entire screen a button
- If you prefer a full‑screen “tap to act” instead of visible buttons at the bottom, use:

```yaml
service: visionect_joan.send_text
data:
  message: "Tap to turn on the light"
  click_anywhere_to_action: true       # hides the button bar and makes the whole screen a 'tap to act'
  action_webhook_id: joan_light_on
target:
  device_id: 00000000000000000000000000000000
```

Tips:
- The right button (→) uses `action_webhook_id`. The center (✔) uses `action_webhook_2_id`.
- You can add “Back” (←) with `add_back_button: true`. The “Back” destination priority:
  1) `back_button_url` in the service call,
  2) device’s “Back button target” selector entity,
  3) global “Main menu URL” in integration options.
- Webhooks work most reliably when the Visionect Server runs as a HA add‑on on the same host (the integration will use the correct internal URL). If the server is on a different host, ensure it can reach HA over HTTP/HTTPS.
- The same approach works with other display services (e.g., `send_status_panel`, `send_image_url`) — just add `action_webhook_id`.

Troubleshooting:
- Pressing the button does nothing? Check the Events viewer to see if the webhook arrives and whether `trigger.json` is present in the automation.
- If you use HTTPS and separate hosts, verify the internal URL in Settings → System → Network.
  
</details>


Tips:
- Webhooks are most reliable when the Visionect Server runs as a HA add‑on (same host) — the integration automatically uses the correct internal HA address for webhooks.
- If Visionect runs on another host, ensure HTTP connectivity to HA and a valid certificate (if using https).

---

## Installation

### Via HACS (recommended)
1. Install [HACS](https://hacs.xyz/) in Home Assistant.
2. HACS → Integrations → menu (⋮) → Custom repositories.
3. Add this repo as an Integration and click Add.
4. Find “Visionect Joan” and click Install.
5. Restart Home Assistant.

### Manual
1. Download the latest release (`visionect-joan.zip` or `Source code (zip)`).
2. Extract to `/config/custom_components/visionect_joan/`.
3. Restart Home Assistant.

---

## Configuration


1. Go to `Settings → Devices & Services`.
2. Click “+ Add integration”.
3. Search for “Visionect Joan” and start configuration.
4. Enter your Visionect Software Suite details: [Visionect Software Suite installation](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant_EN)
   - Server address (e.g., `192.168.x.x:8081`) (Home Assistant address)
   - Username (`admin`)
   - Password (`set your own`)
   - API Key and API Secret (create in Visionect Software Suite → Users → Add new API key)

<img width="1567" height="425" alt="Config screen" src="https://github.com/user-attachments/assets/37bbcdb7-e820-4275-b7ed-efc9248048e5" />

<img width="575" height="615" alt="Add API key in VSS" src="https://github.com/user-attachments/assets/a70ccc87-bbff-4fa4-aec5-f4e602709f19" />


---

## Examples

Screens you can display on a Joan 6 tablet:

<details>
  <summary>Click to see more screenshots</summary>
  <img width="381" height="570" alt="View 1" src="https://github.com/user-attachments/assets/e1f32a48-0277-42ce-9018-837aeba1b6a8" />
  <img width="510" height="739" alt="View 2" src="https://github.com/user-attachments/assets/8f8c673d-8447-42ec-9d13-0bd4e9683437" />
  <img width="948" height="791" alt="View 3" src="https://github.com/user-attachments/assets/4a3c054a-e239-49c1-ab9d-037584cd7989" />
  <img width="607" height="893" alt="View 4" src="https://github.com/user-attachments/assets/1321cfe8-905d-44ef-b1b9-29d999559a04" />
  <img width="770" height="641" alt="View 5" src="https://github.com/user-attachments/assets/31e9bca1-d7c6-4245-b32f-4c909251bf2c" />
  <img width="290" height="407" alt="View 6" src="https://github.com/user-attachments/assets/ad0d3f54-fe5a-466a-8da6-a5d93a052944" />
  <img width="433" height="290" alt="View 7" src="https://github.com/user-attachments/assets/871617fa-b4cb-4d4e-af4b-eae5120b684a" />
  <img width="307" height="457" alt="View 8" src="https://github.com/user-attachments/assets/d7d76fdd-52b7-4c95-8f77-a369e672ab4b" />
  <img width="306" height="456" alt="View 9" src="https://github.com/user-attachments/assets/e3f248bb-f2c8-4e32-b41d-09cbf24a02bf" />
  <img width="569" height="808" alt="View 10" src="https://github.com/user-attachments/assets/f746301e-d0fa-4993-aa7f-b7b4d5c2e15d" />
  <img width="758" height="1024" alt="Home panel" src="https://github.com/user-attachments/assets/fd78c164-6691-477e-84e1-e47a1f70a8cc" />
  
</details>

---


## Notes

- This is not an official Visionect or Home Assistant integration.
- Tested with **Joan 6**; other models have not been verified.
- AI was used for faster development.
- [Want to buy a new Joan 6?](https://allegrolokalnie.pl/oferta/joan-6-nowy-home-assistant-energooszczedny-dotykowy-tablet-eink)
- [Guide: Visionect Software Suite - Installation](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant)

---

## License

MIT

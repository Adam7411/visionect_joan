<!-- README.md -->
<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
</div>


<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open this repository in HACS." /></a>

# Visionect Joan for Home Assistant

<img width="1280" height="800" alt="Example main screen on a Joan 6 tablet" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

<p align="center">
<img width="24%" alt="Weather view" src="https://github.com/user-attachments/assets/993bbcaf-5ee9-47d8-80b4-b886ef897b69" />
<img width="24%" alt="Wi‑Fi QR code" src="https://github.com/user-attachments/assets/d165cd67-79cf-402a-b595-905e3c5cb809" />
<img width="24%" alt="Status panel" src="https://github.com/user-attachments/assets/1594ae1f-0a95-44cb-8edc-cad3b0879c88" />
<img width="24%" alt="Energy panel" src="https://github.com/user-attachments/assets/5ad26dae-dc77-408f-bf55-0a33ce2601ba" />
<br>
<img width="35%" alt="Temperature graph" src="https://github.com/user-attachments/assets/27b23199-e4c1-4f69-8c45-2e06cd290f3a" />
</p>

The `visionect_joan` integration turns your energy‑efficient **Joan 6** e‑ink tablet into a powerful, fully customizable information hub for your smart home.

With the extensive service set, you can build advanced automations—show the energy panel when you arrive home, display the shopping list when you walk into the kitchen, or send a camera snapshot and automatically return to the main dashboard after motion is detected.

## Key features

- Full screen control: send any URL, local dashboards (e.g., from AppDaemon), or single images.
- Dynamically generated views: e‑ink‑optimized panels for weather, calendar, to‑do lists, energy, and entity statuses.
- Interactivity: add a “Back” button to temporary views or make the entire screen clickable to return to the main menu.
- Two action buttons (webhooks): right (→) and center (✔) can trigger different Home Assistant automations.
- Button bar moved to the bottom of the screen: easier access to Back (←), Action (→) and the center button (✔).
- Power management: sleep and wake services help extend battery life.
- Live preview: a built‑in `camera` entity shows what is currently on the tablet.
- Easier view and option configuration: everything is configured in the Home Assistant UI. Configuration via `configuration.yaml` is no longer used.
<img width="838" height="566" alt="Button bar at the bottom" src="https://github.com/user-attachments/assets/3d86ce11-44b9-4a65-aa2d-9c4379b77fd3" />

### Available entities and services

**Entities and sensors:**
- Screen preview (`camera`): current image displayed on the tablet.
- Battery (`sensor`): charge level.
- Charging status (`binary_sensor`): whether the device is plugged in.
- Device status (`sensor`): whether the tablet is online.
- Device name (`text`): change the name directly from HA.
- Refresh interval (`number`): how often the tablet refreshes content.
- Bit depth: number of grayscale levels (1‑bit = black/white; 4‑bit = 16 shades — better quality).
- Dithering method: improves perceived image quality by smoothing gradients.
- Clear cache: removes stored page data (e.g., images) if outdated content persists.
- And more: temperature, Wi‑Fi signal strength, battery voltage, uptime, storage used, configured URL, last seen, etc.

<img width="663" height="987" alt="Example entities" src="https://github.com/user-attachments/assets/03f7ec1a-784d-4400-93e1-add56af0bc49" />

**Services:**
- `visionect_joan.set_url`: display any URL or the name of a saved (predefined) view.
- `visionect_joan.send_text`: formatted text with an optional image.
- `visionect_joan.send_camera_snapshot`: snapshot from any HA camera.
- `visionect_joan.send_weather`: clean weather panel (multiple layouts).
- `visionect_joan.send_calendar`: event list or monthly grid with a day view.
- `visionect_joan.send_energy_panel`: summary of energy consumption/production.
- `visionect_joan.send_status_panel`: panel with the states of selected entities.
- `visionect_joan.send_sensor_graph`: history graph for sensors, adapted to screen orientation.
- `visionect_joan.send_todo_list`: to‑do list (e.g., groceries).
- `visionect_joan.send_qr_code`: QR code (e.g., guest Wi‑Fi).
- `visionect_joan.sleep_device` and `wake_device`: put the device to sleep/wake it up.
- `visionect_joan.clear_display`, `force_refresh`, `set_display_rotation`: screen management tools.

The integration supports Jinja2 templates. You can dynamically build content in:
- `message` (service `send_text`)
- `caption` (service `send_camera_snapshot`)

### Back button and action buttons (webhook)

- Action buttons (webhooks) — add interactive “Action” (→) and a second button (✔). Pressing a button sends a POST request to a Home Assistant webhook, letting you trigger automations (e.g., turn on lights, change scenes) directly from the e‑ink screen.
- The button bar is positioned at the bottom of the screen for easier operation.
- “Back” button — return to your main panel (e.g., AppDaemon). Set the main menu in the integration options (Configure).

<img width="1237" height="639" alt="Interactive overlay" src="https://github.com/user-attachments/assets/c1246088-77e0-4be7-8a51-ac49b9d8cd46" />

<img width="561" height="705" alt="Back button option" src="https://github.com/user-attachments/assets/c7d2f579-759e-48dd-8046-5b0606f5de9e" />

---

## Installation

You can install the integration via **HACS** (recommended) or **manually**.

### Install via HACS (recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant.
2. Go to `HACS → Integrations`.
3. Click the three‑dot menu (top‑right) and choose **Custom repositories**.
4. Paste this repository URL, select the **Integration** category, and click **Add**.
5. Find **Visionect Joan** and click **Install**.
6. Restart Home Assistant.

### Manual installation

1. Download the latest release (`visionect-joan.zip` or `Source code (zip)`).
2. Extract the archive into `/config/custom_components/`.
3. Restart Home Assistant.

---

## Configuration

After installing and restarting Home Assistant:

1. Go to `Settings → Devices & Services`.
2. Click **“+ Add Integration”**.
3. Search for **“Visionect Joan”** and start the setup.
4. Enter your Visionect Software Suite details: [Visionect Software Suite installation](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant_EN)
   - Server address (e.g., `192.168.x.x:8081`) (your Home Assistant address)
   - Username (e.g., `admin`)
   - Password (set your own)
   - API Key and API Secret (create in Visionect Software Suite → Users → Add new API key)

<img width="1567" height="425" alt="Integration configuration" src="https://github.com/user-attachments/assets/356a55f2-342d-43f4-bf64-3ef1c6522d4e" />
<img width="575" height="615" alt="Adding an API key in Visionect Software Suite" src="https://github.com/user-attachments/assets/c467a686-6e58-4b6a-9286-033fc45ddbcd" />

---

## Views and options — configure in the UI

- All settings (including views and the main menu address) are configured in the UI:
  - `Settings → Devices & Services → Visionect Joan → Configure`
- There you can:
  - add/edit/delete views (name + URL),
  - set the global “Main menu URL”.
- In services (e.g., `visionect_joan.set_url`) you can provide a view name instead of the full URL — the integration will resolve it (name matching is case‑insensitive).
- Configuration via `configuration.yaml` is no longer used.

---

## Examples

Screens you can display on a Joan 6 tablet managed by Visionect:

<img width="1920" height="848" alt="AppDaemon dashboard on Joan 6" src="https://github.com/user-attachments/assets/9dce230b-c149-49df-b1be-2802cf761cbe" />
<img width="1920" height="1578" alt="AppDaemon — dark theme" src="https://github.com/user-attachments/assets/c3e7cbff-4e94-4172-93e8-c688ca70a7d3" />

**More examples:**

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
</details>

---

## Notes

- This is not an official Visionect or Home Assistant integration.
- Confirmed to work with **Joan 6**; other models have not been tested.
- AI was used to accelerate development.

- [Step‑by‑step guide to using a Joan 6 tablet as a Home Assistant control panel](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant).

## License

This project is released under the MIT License.

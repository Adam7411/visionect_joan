<!-- README.md -->
<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
</div>


<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." /></a>

# Visionect Joan for Home Assistant

<img width="1280" height="800" alt="Example main screen on a Joan 6 tablet" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

<p align="center">
<img width="24%" alt="Weather View" src="https://github.com/user-attachments/assets/993bbcaf-5ee9-47d8-80b4-b886ef897b69" />
<img width="24%" alt="Wi-Fi QR Code" src="https://github.com/user-attachments/assets/d165cd67-79cf-402a-b595-905e3c5cb809" />
<img width="24%" alt="Status Panel" src="https://github.com/user-attachments/assets/1594ae1f-0a95-44cb-8edc-cad3b0879c88" />
<img width="24%" alt="Energy Panel" src="https://github.com/user-attachments/assets/5ad26dae-dc77-408f-bf55-0a33ce2601ba" />
<br>
<img width="35%" alt="Temperature Graph" src="https://github.com/user-attachments/assets/27b23199-e4c1-4f69-8c45-2e06cd290f3a" />
</p>

The `visionect_joan` integration transforms your energy-efficient **Joan 6** e-ink tablet into a powerful, fully customizable information hub for your smart home. Instead of a static calendar, you get a dynamic, touch-enabled screen where you can display any data from Home Assistant—from control panels and weather forecasts to camera snapshots.

With extensive services, you can create advanced automations, such as displaying an energy panel upon returning home, showing a shopping list when you enter the kitchen, or sending a notification with a camera image, followed by an automatic return to your main dashboard.

## Key Features

- **Full Screen Control:** Send any website, local dashboards (e.g., from AppDaemon), or single images.
- **Dynamically Generated Views:** The integration can create e-ink optimized panels for weather forecasts, calendars, to-do lists, energy summaries, or entity statuses.
- **Interactivity:** Add a "back" button to temporary views or make the entire screen clickable for an easy return to your main menu.
- **Power Management:** Maximize battery life with services to put the device to sleep and wake it up as part of your automations.
- **Live View:** A built-in `camera` entity allows you to see what’s currently displayed on the tablet directly from the Home Assistant interface.

### Available Entities and Services

**Sensors and Entities:**
- **Live View (`camera`):** See the current image on the tablet's screen.
- **Battery (`sensor`):** Monitor the charge level.
- **Charging Status (`binary_sensor`):** Check if the device is plugged in.
- **Device Status (`sensor`):** Verify if the tablet is online.
- **Device Name (`text`):** Change the tablet's name directly from HA.
- **Refresh Interval (`number`):** Adjust how often the tablet refreshes its content.
- And many more: temperature, Wi-Fi signal strength, battery voltage, uptime, storage used, configured URL, and last seen time.
<img width="921" height="812" alt="joan" src="https://github.com/user-attachments/assets/1ca6ecb8-499b-46bc-ab2c-8e2987211f42" />


**Services:**
- `visionect_joan.set_url`: Display any URL.
- `visionect_joan.send_text`: Send a formatted text message with an optional image.
- `visionect_joan.send_camera_snapshot`: Send a snapshot from any camera in Home Assistant.
- `visionect_joan.send_weather`: Show a clean and readable weather panel.
- `visionect_joan.send_calendar`: Display calendar events as a list or a monthly grid.
- `visionect_joan.send_energy_panel`: Show a summary of your energy consumption and production.
- `visionect_joan.send_status_panel`: Display a panel with the current state of selected entities.
- `visionect_joan.send_sensor_graph`: Generate a history graph for sensors, adapted to the screen's orientation.
- `visionect_joan.send_todo_list`: Display a to-do list (e.g., your shopping list).
- `visionect_joan.send_qr_code`: Show a QR code (e.g., for guest Wi-Fi).
- `visionect_joan.sleep_device` & `wake_device`: Put the device to sleep and wake it up.
- `visionect_joan.clear_display`, `force_refresh`, `set_display_rotation`: Screen management tools.

### Back Button and Interactivity

Many services (like `send_weather`, `send_calendar`, or `send_sensor_graph`) allow you to temporarily display information with an easy way to return to your main screen. To use this feature, define your main dashboard URL in `configuration.yaml`:

```yaml
visionect_joan:
  main_menu_url: "http://<YOUR_HA_IP>:5050/dashboard_name" #Example of the Appdaemon Menu panel
```
Then, when calling a service, you can use the option `add_back_button: true` to display a visible back button, or `click_anywhere_to_return: true` to make the entire screen clickable, leading back to your main menu.

<img width="309" height="467" alt="Bez tytułu" src="https://github.com/user-attachments/assets/8d13bc78-2aa6-45de-819b-53b1ba0f8619" />


---

## Installation

The integration can be installed in two ways: via **HACS** (recommended) or **manually**.

### Installation via HACS (Recommended)

1.  Ensure you have [HACS](https://hacs.xyz/) installed in your Home Assistant.
2.  Go to `HACS -> Integrations`.
3.  Click the three-dot menu in the top right corner and select **"Custom repositories"**.
4.  Paste the URL of this repository, select the category **"Integration"**, and click **"Add"**.
5.  Find the **"Visionect Joan"** integration in the list and click **"Install"**.
6.  Restart Home Assistant to apply the changes.

### Manual Installation

1.  Download the latest release by clicking on `visionect-joan.zip` (or `Source code (zip)`).
2.  Unpack the downloaded archive into your `/config/custom_components/` directory.
3.  Restart Home Assistant.

---

## Configuration

After a successful installation and restart of Home Assistant:

1.  Go to `Settings > Devices & Services`.
2.  Click **"+ Add Integration"** in the bottom right corner.
3.  Search for **"Visionect Joan"** and click it to start the configuration.
4.  Enter your Visionect Software Suite credentials: [Installation Software Suite credentials ]([https://hacs.xyz/](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant_EN))
    -   Server Address (e.g., `192.168.x.x:8081`)
    -   Username (e.g., `admin`)
    -   Password
    -   API Key and API Secret (you can generate these in the Visionect Software Suite under the "Users" tab by clicking "Add new API key").

<img width="1567" height="425" alt="Integration Configuration" src="https://github.com/user-attachments/assets/356a55f2-342d-43f4-bf64-3ef1c6522d4e" />
<img width="575" height="615" alt="Adding an API key in the Visionect Software Suite" src="https://github.com/user-attachments/assets/c467a686-6e58-4b6a-9286-033fc45ddbcd" />

---

## Usage Examples

Example screens that can be displayed on the Joan 6 tablet using the Visionect server:


<img width="1920" height="848" alt="AppDaemon Dashboard on a Joan 6 screen" src="https://github.com/user-attachments/assets/9dce230b-c149-49df-b1be-2802cf761cbe" />
<img width="1920" height="1578" alt="AppDaemon Dashboard - dark theme" src="https://github.com/user-attachments/assets/c3e7cbff-4e94-4172-93e8-c688ca70a7d3" />

**More examples:**

<details>
  <summary>Click to see more screenshots</summary>
  <img width="381" height="570" alt="Untitled" src="https://github.com/user-attachments/assets/e1f32a48-0277-42ce-9018-837aeba1b6a8" />
  <img width="510" height="739" alt="3" src="https://github.com/user-attachments/assets/8f8c673d-8447-42ec-9d13-0bd4e9683437" />
  <img width="948" height="791" alt="2" src="https://github.com/user-attachments/assets/4a3c054a-e239-49c1-ab9d-037584cd7989" />
  <img width="607" height="893" alt="1" src="https://github.com/user-attachments/assets/1321cfe8-905d-44ef-b1b9-29d999559a04" />
  <img width="770" height="641" alt="4" src="https://github.com/user-attachments/assets/31e9bca1-d7c6-4245-b32f-4c909251bf2c" />
  <img width="290" height="407" alt="smie" src="https://github.com/user-attachments/assets/ad0d3f54-fe5a-466a-8da6-a5d93a052944" />
  <img width="433" height="290" alt="vvvvu" src="https://github.com/user-attachments/assets/871617fa-b4cb-4d4e-af4b-eae5120b684a" />
  <img width="307" height="457" alt="bater tytułu" src="https://github.com/user-attachments/assets/d7d76fdd-52b7-4c95-8f77-a369e672ab4b" />
  <img width="306" height="456" alt="Bez tytułu" src="https://github.com/user-attachments/assets/e3f248bb-f2c8-4e32-b41d-09cbf24a02bf" />
  <img width="569" height="808" alt="Bez tytułuss" src="https://github.com/user-attachments/assets/f746301e-d0fa-4993-aa7f-b7b4d5c2e15d" />
</details>

---

## Notes

-   This project is not an official Visionect or Home Assistant integration.
-   It is confirmed to work with the **Joan 6** device; other models have not been tested.
-   AI was used to expedite the development of this integration.

-   [Step-by-step guide on using the Joan 6 tablet as a Home Assistant control panel (Polish)](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant).

## License

This project is licensed under the MIT License.

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." /></a>

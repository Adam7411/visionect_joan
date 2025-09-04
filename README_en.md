<!-- README.md -->
<div align="right">
<a href="README.md">English</a> | <a href="README_PL.md">Polski</a>
</div>

<img width="447" height="355" alt="image" src="https://github.com/user-attachments/assets/27b23199-e4c1-4f69-8c45-2e06cd290f3a" />

# Visionect Joan for Home Assistant

A custom integration that displays essential information from the **Joan 6** e-ink tablet by Visionect in Home Assistant. It also allows you to send custom URLs, text, and images directly from HA.

This enables powerful automations, such as sending low battery notifications, displaying sensor states on the tablet, or pushing images for alerts before returning to your Appdaemon dashboard.

---

## ✨ What's New in v1.8.0

This is a significant feature update! You can now send messages with images, have more direct control over the device, and monitor its status in greater detail.

*   **🖼️ Rich Text Messages:** The `send_text` service now supports adding an image with layout options (top, left, right).
*   **⚪ New `clear_display` Service:** A dedicated service to easily clear the device screen to a blank white page.
*   **🔄 New `force_refresh` Service:** Instantly force the device to reload its currently configured URL on demand.
*   **📊 New Entities:**
    *   **Screen Refresh Control:** A new number entity to set the device's refresh interval.
    *   **Charging Status:** A binary sensor to see if the device is currently charging.
    *   **Configured URL Sensor:** Shows the current URL displayed on the device.
    *   **Last Seen Sensor:** A timestamp for when the device was last active.
*   **🔧 Other:** Minor bug fixes and performance improvements.

---

## Features

This integration provides the following entities and services:

**Sensors:**
- Battery Level
- Total & Used Storage
- Uptime
- Charging Status (Binary Sensor)
- Screen Refresh Interval (Number)
- Battery Voltage
- Device Status (Online/Offline)
- Wi-Fi Signal Strength
- Temperature
- Configured URL
- Last Seen Timestamp

**Services:**
- `visionect_joan.send_text`: Send text messages, now with image support and layout options. Supports Jinja2 templates for dynamic content.
- `visionect_joan.set_url`: Display a custom URL (e.g., a website like `https://www.wikipedia.org/` or a local image like `http://<your_ha_ip>:8123/local/test_image.png`).
- `visionect_joan.clear_display`: Wipes the screen.
- `visionect_joan.force_refresh`: Immediately reloads the content from the configured URL.

<img width="1470" height="678" alt="Screenshot" src="https://github.com/user-attachments/assets/18474371-8779-48aa-8a46-a2270dc120fa" />

---

## Installation

You can install this integration via **HACS** (recommended) or **manually**.

### Installation via HACS (Recommended)

1.  Ensure you have [HACS](https://hacs.xyz/) installed in your Home Assistant.
2.  Go to `HACS -> Integrations`.
3.  Click the three-dots menu in the top right corner and select **"Custom repositories"**.
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
4.  Enter your Visionect Software Suite credentials:
    -   Server Address (e.g., `192.168.x.x:8081`)
    -   Username (e.g., `admin`)
    -   Password
    -   API Key and API Secret (You can generate these in the Visionect Software Suite under the "Users" tab by clicking "Add new API key").

<img width="1567" height="425" alt="5" src="https://github.com/user-attachments/assets/356a55f2-342d-43f4-bf64-3ef1c6522d4e" />
<img width="575" height="615" alt="6" src="https://github.com/user-attachments/assets/c467a686-6e58-4b6a-9286-033fc45ddbcd" />

---

## Showcase

Here are some examples of what can be displayed on the Joan 6 tablet using the Visionect server:

<img width="636" height="399" alt="vision" src="https://github.com/user-attachments/assets/6e30517f-c34a-443e-9e8f-5e02f59c80c7" />
<img width="1920" height="848" alt="ada" src="https://github.com/user-attachments/assets/9dce230b-c149-49df-b1be-2802cf761cbe" />
<img width="1920" height="1578" alt="aaaa" src="https://github.com/user-attachments/assets/c3e7cbff-4e94-4172-93e8-c688ca70a7d3" />

**More Examples:**

<details>
  <summary>Click to see more screenshots</summary>
  <img width="510" height="739" alt="3" src="https://github.com/user-attachments/assets/8f8c673d-8447-42ec-9d13-0bd4e9683437" />
  <img width="948" height="791" alt="2" src="https://github.com/user-attachments/assets/4a3c054a-e239-49c1-ab9d-037584cd7989" />
  <img width="607" height="893" alt="1" src="https://github.com/user-attachments/assets/1321cfe8-905d-44ef-b1b9-29d999559a04" />
  <img width="770" height="641" alt="4" src="https://github.com/user-attachments/assets/31e9bca1-d7c6-4245-b32f-4c909251bf2c" />
  <img width="290" height="407" alt="smie" src="https://github.com/user-attachments/assets/ad0d3f54-fe5a-466a-8da6-a5d93a052944" />
  <img width="433" height="290" alt="vvvvu" src="https://github.com/user-attachments/assets/871617fa-b4cb-4d4e-af4b-eae5120b684a" />
  <img width="306" height="456" alt="Bez tytułu" src="https://github.com/user-attachments/assets/e3f248bb-f2c8-4e32-b41d-09cbf24a02bf" />
  <img width="569" height="808" alt="Bez tytułuss" src="https://github.com/user-attachments/assets/f746301e-d0fa-4993-aa7f-b7b4d5c2e15d" />
</details>

---

## Notes

-   This project is not an official Visionect or Home Assistant integration.
-   It is confirmed to work with the **Joan 6** device; other models have not been tested.
-   This integration was rapidly developed with the assistance of AI.
-   [Interested in buying a new Joan 6? (Polish offer)](https://allegrolokalnie.pl/oferta/joan-6-nowy-home-assistant-energooszczedny-dotykowy-tablet-eink).
-   [Step-by-step guide to using the Joan 6 tablet as a Home Assistant control panel (Polish)](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant).

## License

This project is licensed under the MIT License.

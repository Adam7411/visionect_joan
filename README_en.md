# Visionect Joan

A custom Home Assistant integration that displays basic information about **Joan 6** tablets and allows sending URLs from Home Assistant.
This enables creating automations like low battery notifications or displaying battery level entities on the tablet, as well as sending images to various notifications.

## Displayed Information:

- Battery
- Total memory
- Uptime
- Refresh interval
- Battery voltage
- Status
- WiFi signal
- Temperature
- Sending your text (notifications from Home Assistant)
- Sending URL addresses (e.g., https://www.wikipedia.org/) or images (example: http://HAaddress:8123/local/test_image.png) (place test_image.png file in the directory \\192.168.xxx.xxx\config\www\)

<img width="1470" height="678" alt="Screenshot" src="https://github.com/user-attachments/assets/18474371-8779-48aa-8a46-a2270dc120fa" />

---

## Integration Installation

The integration can be installed in two ways: through **HACS** (recommended) or **manually**.

### Installation via HACS (recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant.
2. Go to `HACS -> Integrations`.
3. Click the three-dot menu in the top right corner and select **"Custom repositories"**.
4. Paste this repository's URL, select **"Integration"** category and click **"Add"**.
5. Search for **"Visionect Joan"** integration in the list and click **"Install"**.
6. Restart Home Assistant to apply changes.

### Manual Installation

1. Download the latest release by clicking on `visionect-joan.zip` (or `Source code (zip)`).
2. Extract the downloaded archive to /config/custom_components/
3. Restart Home Assistant.

---

## Configuration

After successful installation and Home Assistant restart:

1. Go to `Settings > Devices & Services`.
2. Click **"+ Add Integration"** in the bottom right corner.
3. Search for **"Visionect Joan"** and click to start configuration.
4. Enter login credentials for Visionect Software Suite:
   - URL address (192.168.x.x:8081)
   - Visionect Software Suite username
   - Visionect Software Suite password
   - API Key and API Secret (create these in Visionect Software Suite under Users tab with "Add new API key" button)

<img width="1567" height="425" alt="5" src="https://github.com/user-attachments/assets/356a55f2-342d-43f4-bf64-3ef1c6522d4e" />
<img width="575" height="615" alt="6" src="https://github.com/user-attachments/assets/c467a686-6e58-4b6a-9286-033fc45ddbcd" />

### Example Screenshots

<img width="510" height="739" alt="3" src="https://github.com/user-attachments/assets/8f8c673d-8447-42ec-9d13-0bd4e9683437" />
<img width="948" height="791" alt="2" src="https://github.com/user-attachments/assets/4a3c054a-e239-49c1-ab9d-037584cd7989" />
<img width="607" height="893" alt="1" src="https://github.com/user-attachments/assets/1321cfe8-905d-44ef-b1b9-29d999559a04" />
<img width="770" height="641" alt="4" src="https://github.com/user-attachments/assets/31e9bca1-d7c6-4245-b32f-4c909251bf2c" />

---

## Notes

- This project is not an official Visionect or Home Assistant integration.
- It works with **Joan 6** devices, other models have not been tested.
- I used AI to quickly write this integration.
- [Step-by-step guide for using Joan 6 tablet as Home Assistant control panel](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant).

## License

This project is released under the MIT License.

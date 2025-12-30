from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD

from .const import DOMAIN, CONF_API_KEY, CONF_API_SECRET

TO_REDACT = {
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_API_KEY,
    CONF_API_SECRET,
}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
):
    data = async_redact_data(dict(entry.data), TO_REDACT)
    options = dict(entry.options)

    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get("coordinator")
    devices = {}
    if coordinator and coordinator.data:
        # Uproszczony widok urządzeń (bez binariów), zredagowany
        for uuid, dev in coordinator.data.items():
            devices[uuid] = {
                "State": dev.get("State"),
                "Config": {
                    "Name": dev.get("Config", {}).get("Name"),
                    "Url": dev.get("Config", {}).get("Url"),
                    "DisplayRotation": dev.get("Config", {}).get("DisplayRotation"),
                    "ReloadTimeout": dev.get("Config", {}).get("ReloadTimeout"),
                },
                "Status": {
                    "Battery": dev.get("Status", {}).get("Battery"),
                    "RSSI": dev.get("Status", {}).get("RSSI"),
                    "Temperature": dev.get("Status", {}).get("Temperature"),
                    "ApplicationVersion": dev.get("Status", {}).get("ApplicationVersion"),
                    "ConnectReason": dev.get("Status", {}).get("ConnectReason"),
                    "ErrorCode": dev.get("Status", {}).get("ErrorCode"),
                },
                "LastUpdated": str(dev.get("LastUpdated")),
            }

    return {
        "config": data,
        "options": options,
        "device_count": len(devices),
        "devices": devices,
    }
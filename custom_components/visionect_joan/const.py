# custom_components/visionect_joan/const.py

from datetime import timedelta

DOMAIN = "visionect_joan"
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"

# Common phrases to treat as 'unknown' or 'None' in data
UNKNOWN_STRINGS = {"unknown", "nieznany", "none", "", "n/a", "na", "unknown_value"}

# Joan screen rotations
DISPLAY_ROTATIONS = {
    "0": "Landscape",
    "1": "Portrait, 90°",
    "2": "Landscape, 180°",
    "3": "Portrait, 270°"
}

# Statuses
IP_UNKNOWN = "unknown"
STATE_ONLINE = "online"
STATE_OFFLINE = "offline"

# Device constants
MODEL_JOAN6 = "Joan 6"

# Refresh constants
SCAN_INTERVAL = timedelta(minutes=5)

# Battery constants
BATTERY_VOLTAGE_DIVIDER = 1000  # Convert mV to V

# API Endpoints
API_PING = "/api/ping"
API_DEVICES = "/api/device"
API_DEVICE_DETAIL = "/api/device/{uuid}"
API_SESSION = "/api/session"
API_REBOOT = "/api/device/{uuid}/reboot"
API_RESTART_SESSION = "/api/session/{uuid}/restart"

# Service names
SERVICE_FORCE_REFRESH = "force_refresh"
SERVICE_CLEAR_DISPLAY = "clear_display"
SERVICE_SLEEP_DEVICE = "sleep_device"
SERVICE_WAKE_DEVICE = "wake_device"
SERVICE_SEND_QR_CODE = "send_qr_code"
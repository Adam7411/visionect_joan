from datetime import timedelta

DOMAIN = "visionect_joan"

# Credentials / API keys
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"

# Opcje (Options Flow / UI configuration)
CONF_VIEWS = "views"
CONF_VIEW_NAME = "view_name"
CONF_VIEW_URL = "view_url"
CONF_MAIN_MENU_URL = "main_menu_url"
CONF_CLEANUP_MAX_AGE = "cleanup_max_age_hours"
CONF_CLEANUP_INTERVAL = "cleanup_interval_hours"
CONF_TABLET_LANGUAGE = "tablet_language"

# Limit długości Data URI dla HTML
URL_LENGTH_LIMIT = 4096
CACHE_DIR_NAME = "visionect_cache"

# Nazwa eventu dla wyników komend usług
EVENT_COMMAND_RESULT = f"{DOMAIN}_command_result"

UNKNOWN_STRINGS = {
    "unknown", "nieznany", "none", "", "n/a", "na", "unknown_value", "unavailable"
}

DISPLAY_ROTATIONS = {
    "0": "Portrait",
    "1": "Landscape, 90°",
    "2": "Portrait, 180°",
    "3": "Landscape, 270°",
}

DITHERING_OPTIONS = ["none", "bayer", "floyd-steinberg"]
ENCODING_OPTIONS = ["1", "4"]

ROTATION_OPTIONS = ["Portrait", "Landscape, 90°", "Portrait, 180°", "Landscape, 270°"]
ROTATION_TO_API = {
    "Portrait": "0",
    "Landscape, 90°": "1",
    "Portrait, 180°": "2",
    "Landscape, 270°": "3",
}

SLEEP_PERIODIC_OPTIONS = ["Periodic", "Disabled"]
SLEEP_PERIODIC_TO_API = {
    "Periodic": "true",
    "Disabled": "false",
}

PUSH_MODE_OPTIONS = ["Enabled", "Disabled"]
PUSH_MODE_TO_API = {
    "Enabled": "true",
    "Disabled": "false",
}

ATTR_PREDEFINED_URL = "predefined_url"

# Statusy
IP_UNKNOWN = "unknown"
STATE_ONLINE = "online"
STATE_OFFLINE = "offline"
STATE_SLEEPING = "sleeping"

MODEL_JOAN6 = "Joan 6"

SCAN_INTERVAL = timedelta(minutes=5)
BATTERY_VOLTAGE_DIVIDER = 1000

# Endpointy API Visionect (Z UKOŚNIKAMI NA KOŃCU, WYMAGANE PRZEZ VSS API)
API_PING = "/api/user/"
API_DEVICES = "/api/device/"
API_DEVICE_DETAIL = "/api/device/{uuid}"
API_SESSION = "/api/session/"
API_SESSION_DETAIL = "/api/session/{uuid}"
API_REBOOT = "/api/device/{uuid}/reboot"
API_RESTART_SESSION = "/api/session/{uuid}/restart"
API_CLEAR_WEB_CACHE = "/api/session/webkit-clear-cache"
API_REBOOT_BATCH = "/api/device/reboot"
API_RESTART_SESSION_BATCH = "/api/session/restart"
API_ORPHANS = "/api/orphans"
API_TCLV_LIST = "/api/devicetclv/{uuid}"
API_TCLV_PARAM = "/api/cmd/Param/{uuid}"
API_SCREENSHOT = "/api/live/device/{uuid}/cached.png"
TCLV_SLEEP_MODE_ID = 52

# Usługi
SERVICE_FORCE_REFRESH = "force_refresh"
SERVICE_CLEAR_DISPLAY = "clear_display"
SERVICE_SLEEP_DEVICE = "sleep_device"
SERVICE_WAKE_DEVICE = "wake_device"
SERVICE_SEND_QR_CODE = "send_qr_code"
SERVICE_SEND_KEYPAD = "send_keypad"
SERVICE_SEND_MEDIA_PLAYER = "send_media_player"
SERVICE_SEND_BUTTON_PANEL = "send_button_panel"

SUPPORTED_IMAGE_FORMATS = ["png", "jpg", "jpeg", "gif", "svg", "webp"]

NETWORK_RETRY_DELAY = 60
MAX_RETRY_ATTEMPTS = 3

ATTR_CALENDAR_ENTITY = "calendar_entity"
ATTR_DURATION_DAYS = "duration_days"
ATTR_DISPLAY_STYLE = "display_style"
ATTR_SCREEN_SIZE = "screen_size"
SCREEN_SIZE_OPTIONS = ["joan6", "joan13"]
# Plik: custom_components/visionect_joan/const.py
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

# Limit długości Data URI dla HTML (powyżej zapis do pliku w /www/visionect_cache/<hash>.html)
# Zbyt długie adresy mogą powodować problemy z odświeżaniem lub limitami urządzenia
URL_LENGTH_LIMIT = 4096
CACHE_DIR_NAME = "visionect_cache"

# Nazwa eventu dla wyników komend usług
EVENT_COMMAND_RESULT = f"{DOMAIN}_command_result"

# Zestaw wartości traktowanych jako 'unknown' / brak danych
UNKNOWN_STRINGS = {
    "unknown", "nieznany", "none", "", "n/a", "na", "unknown_value", "unavailable"
}

# Rotacje ekranu – zgodnie z VSS Management Interface (NIE raw API docs, które są odwrócone)
# VSS UI: 0=Landscape, 1=Portrait 90°, 2=Landscape 180°, 3=Portrait 270°
DISPLAY_ROTATIONS = {
    "0": "Landscape",
    "1": "Portrait, 90°",
    "2": "Landscape, 180°",
    "3": "Portrait, 270°",
}

# Opcje dla dithering / enkodowania (bit depth)
DITHERING_OPTIONS = ["none", "bayer", "floyd-steinberg"]
ENCODING_OPTIONS = ["1", "4"]

# Opcje rotacji ekranu dla Select entity – zgodne z VSS Management Interface
ROTATION_OPTIONS = ["Landscape", "Portrait, 90°", "Landscape, 180°", "Portrait, 270°"]
# Mapowanie opis → numer Rotation wysyłany do API (0=Landscape to domyślne dla Joan 6)
ROTATION_TO_API = {
    "Landscape": "0",
    "Portrait, 90°": "1",
    "Landscape, 180°": "2",
    "Portrait, 270°": "3",
}

# Opcje trybu Sleep (PeriodicSleep)
SLEEP_PERIODIC_OPTIONS = ["periodic", "at_time", "disabled"]

# Atrybut dla usług z wyborem wstępnie zdefiniowanego widoku
ATTR_PREDEFINED_URL = "predefined_url"

# Statusy
IP_UNKNOWN = "unknown"
STATE_ONLINE = "online"
STATE_OFFLINE = "offline"

# Model (na razie jeden – można rozszerzyć w przyszłości)
MODEL_JOAN6 = "Joan 6"

# Interwał odświeżania koordynatora
SCAN_INTERVAL = timedelta(minutes=5)

# Konwersja mV -> V dla napięcia baterii
BATTERY_VOLTAGE_DIVIDER = 1000

# Endpointy API Visionect
API_PING = "/api/ping"
API_DEVICES = "/api/device"
API_DEVICE_DETAIL = "/api/device/{uuid}"
API_SESSION = "/api/session"
API_SESSION_DETAIL = "/api/session/{uuid}"
API_REBOOT = "/api/device/{uuid}/reboot"
API_RESTART_SESSION = "/api/session/{uuid}/restart"
API_CLEAR_WEB_CACHE = "/api/session/webkit-clear-cache"
API_REBOOT_BATCH = "/api/device/reboot"
API_RESTART_SESSION_BATCH = "/api/session/restart"
API_ORPHANS = "/api/orphans"
API_TCLV_LIST = "/api/devicetclv/{uuid}"
API_TCLV_PARAM = "/api/cmd/Param/{uuid}"

# Nazwy usług (część podstawowa + nowe)
SERVICE_FORCE_REFRESH = "force_refresh"
SERVICE_CLEAR_DISPLAY = "clear_display"
SERVICE_SLEEP_DEVICE = "sleep_device"
SERVICE_WAKE_DEVICE = "wake_device"
SERVICE_SEND_QR_CODE = "send_qr_code"
SERVICE_SEND_KEYPAD = "send_keypad"
SERVICE_SEND_MEDIA_PLAYER = "send_media_player"
SERVICE_SEND_BUTTON_PANEL = "send_button_panel" # Nowa usługa

# Obsługiwane rozszerzenia obrazów dla walidacji URL
SUPPORTED_IMAGE_FORMATS = ["png", "jpg", "jpeg", "gif", "svg", "webp"]

# Konfiguracja retry sieci
NETWORK_RETRY_DELAY = 60  # sekundy pomiędzy próbami (bazowa)
MAX_RETRY_ATTEMPTS = 3

# Atrybuty kalendarza
ATTR_CALENDAR_ENTITY = "calendar_entity"
ATTR_DURATION_DAYS = "duration_days"
ATTR_DISPLAY_STYLE = "display_style"

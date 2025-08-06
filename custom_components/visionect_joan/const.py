# custom_components/visionect_joan/const.py

from datetime import timedelta

DOMAIN = "visionect_joan"
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"

# Common phrases to treat as 'unknown' or 'None' in data
UNKNOWN_STRINGS = {"unknown", "nieznany", "none", "", "n/a", "na", "unknown_value"}

# Statusy
IP_UNKNOWN = "unknown" # Used internally by API, but sensor converts to None if it matches UNKNOWN_STRINGS
STATE_ONLINE = "online"
STATE_OFFLINE = "offline"
STATE_CHARGING = "charging"
STATE_DISCHARGING = "discharging"
STATE_SLEEPING = "sleeping"
STATE_ERROR = "error"

# Stałe urządzenia
MODEL_JOAN6 = "Joan 6"
MODEL_JOAN6_PRO = "Joan 6 Pro"
MODEL_JOAN13 = "Joan 13"
MODEL_JOAN32 = "Joan 32"

DEFAULT_REFRESH_INTERVAL = 3600  # 1 godzina w sekundach
MIN_REFRESH_INTERVAL = 30  # Minimum 30 sekund
MAX_REFRESH_INTERVAL = 86400  # Maximum 24 godziny

BATTERY_VOLTAGE_DIVIDER = 1000  # Konwersja mV na V
BATTERY_LOW_THRESHOLD = 20  # Próg niskiej baterii w %
BATTERY_CRITICAL_THRESHOLD = 10  # Próg krytycznej baterii w %

# Stałe odświeżania
SCAN_INTERVAL = timedelta(minutes=5)
FAST_SCAN_INTERVAL = timedelta(minutes=1)  # Dla urządzeń z problemami
SLOW_SCAN_INTERVAL = timedelta(minutes=15)  # Dla urządzeń offline

# Tryby uśpienia
SLEEP_MODE_MANUAL = "manual"
SLEEP_MODE_AUTO = "auto"
SLEEP_MODE_DISABLED = "disabled"

# Orientacje ekranu
ORIENTATION_PORTRAIT = "portrait"
ORIENTATION_LANDSCAPE = "landscape"
ORIENTATION_PORTRAIT_FLIPPED = "portrait_flipped"
ORIENTATION_LANDSCAPE_FLIPPED = "landscape_flipped"

# Typy sieci
NETWORK_TYPE_WIFI = "wifi"
NETWORK_TYPE_ETHERNET = "ethernet"
NETWORK_TYPE_CELLULAR = "cellular"

# Endpointy API
API_PING = "/api/ping"
API_DEVICES = "/api/device"
API_DEVICE_DETAIL = "/api/device/{uuid}"
API_SESSION = "/api/session/{uuid}"
API_RESTART_SESSION = "/api/session/{uuid}/restart"
API_LOGS = "/api/device/{uuid}/logs"
API_SCREENSHOT = "/api/device/{uuid}/screenshot"
API_STATISTICS = "/api/device/{uuid}/statistics"
API_HISTORY = "/api/device/{uuid}/history"
API_SERVER_INFO = "/api/server"

# Limity API
API_TIMEOUT = 10  # Timeout dla większości operacji
API_UPLOAD_TIMEOUT = 30  # Timeout dla upload operacji
API_RETRY_COUNT = 3  # Liczba prób ponowienia
API_RETRY_DELAY = 1  # Opóźnienie między próbami w sekundach

# Stałe jakości obrazu
IMAGE_QUALITY_LOW = "low"
IMAGE_QUALITY_MEDIUM = "medium"
IMAGE_QUALITY_HIGH = "high"

# Stałe rozdzielczości
RESOLUTION_6INCH = "1024x758"
RESOLUTION_13INCH = "1600x1200"
RESOLUTION_32INCH = "2560x1440"

# Stałe temperatury
TEMP_MIN_OPERATING = -10  # Minimalna temperatura pracy w °C
TEMP_MAX_OPERATING = 50   # Maksymalna temperatura pracy w °C
TEMP_WARNING_THRESHOLD = 45  # Próg ostrzeżenia o temperaturze w °C

# Stałe pamięci
MEMORY_WARNING_THRESHOLD = 80  # Próg ostrzeżenia o pamięci w %
STORAGE_WARNING_THRESHOLD = 90  # Próg ostrzeżenia o miejscu na dysku w %

# Kody błędów
ERROR_CODE_NETWORK = "network_error"
ERROR_CODE_AUTHENTICATION = "authentication_error"
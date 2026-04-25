DOMAIN = "brother_ads2400n"
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 60  # seconds

CONF_HOST = "host"
CONF_PASSWORD = "password"

# Status page path
PATH_STATUS = "/general/status.html"
PATH_INFO = "/general/information.html?kind=item"

# Known device status values from the scanner HTML
STATUS_MAP = {
    "sleep": "Sleep",
    "ready": "Ready",
    "scanning": "Scanning",
    "warming up": "Warming Up",
    "error": "Error",
    "busy": "Busy",
    "cooling down": "Cooling Down",
    "cancel": "Cancelling",
}

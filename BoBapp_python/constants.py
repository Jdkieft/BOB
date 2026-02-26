"""
Constants en Configuratie

Dit bestand bevat alle constanten en vaste waarden die door de applicatie
worden gebruikt. Door deze centraal te definiëren is het gemakkelijk om
instellingen aan te passen zonder door meerdere bestanden te zoeken.
"""

# ============================================================================
# APPARAAT CONFIGURATIE
# ============================================================================

# Standaard aantal modes bij eerste start
DEFAULT_MODES = 4

# Maximum aantal modes dat de gebruiker kan aanmaken
MAX_MODES_LIMIT = 10

# Minimum aantal modes (kan niet minder dan 1)
MIN_MODES = 1

# Aantal knoppen per mode (3x3 grid)
BUTTONS_PER_MODE = 9

# Aantal fysieke sliders
NUM_SLIDERS = 4  # 3 voor apps + 1 voor master volume

# Standaard baudrate voor seriële communicatie
SERIAL_BAUDRATE = 9600


# ============================================================================
# KLEUREN (Light mode, Dark mode)
# ============================================================================

# Achtergrond kleuren
COLOR_BACKGROUND_LIGHT = "gray90"
COLOR_BACKGROUND_DARK = "gray15"

# Button kleuren
COLOR_BUTTON_NORMAL_LIGHT = "gray80"
COLOR_BUTTON_NORMAL_DARK = "gray25"

COLOR_BUTTON_HOVER_LIGHT = "gray70"
COLOR_BUTTON_HOVER_DARK = "gray35"

# Mooie blauwe accent kleuren (geïnspireerd door moderne UI)
COLOR_ACCENT = "#3B82F6"           # Moderne blauwe accent
COLOR_ACCENT_HOVER = "#2563EB"     # Donkerder voor hover
COLOR_ACCENT_ACTIVE = "#60A5FA"    # Lichter voor active/selected

COLOR_BUTTON_ACTIVE = COLOR_ACCENT_ACTIVE   # Voor geconfigureerde buttons
COLOR_BUTTON_FOCUS = COLOR_ACCENT           # Voor hover/focus

# Status kleuren
COLOR_SUCCESS = "green"
COLOR_ERROR = "red"
COLOR_WARNING = "orange"


# ============================================================================
# FONTS
# ============================================================================

FONT_TITLE = ("Inter", 28, "bold")
FONT_HEADER = ("Roboto", 20, "bold")
FONT_SUBHEADER = ("Roboto", 18, "bold")
FONT_NORMAL = ("Roboto", 14)
FONT_SMALL = ("Roboto", 11)
FONT_TINY = ("Roboto", 9)
FONT_ICON = ("Segoe UI Emoji", 45)
FONT_MONOSPACE = ("Courier", 12)


# ============================================================================
# AFMETINGEN
# ============================================================================

# Window grootte
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 900

# Header hoogte
HEADER_HEIGHT = 80

# Button grid afmetingen
BUTTON_SIZE = 160
BUTTON_SPACING = 10
BUTTON_CORNER_RADIUS = 15
BUTTON_BORDER_WIDTH = 3


# ============================================================================
# QUICK ACTIONS
# ============================================================================

# Voorgedefinieerde acties die gebruikers snel kunnen toewijzen
QUICK_ACTIONS = [
    {
        "name": "Discord Mute",
        "icon": "🎤",
        "hotkey": "ctrl+shift+m",
        "description": "Toggle Discord microphone mute"
    },
    {
        "name": "Discord Deafen",
        "icon": "🔇",
        "hotkey": "ctrl+shift+d",
        "description": "Toggle Discord deafen (mute input & output)"
    },
    {
        "name": "OBS Start/Stop Recording",
        "icon": "⏺️",
        "hotkey": "ctrl+shift+r",
        "description": "Start or stop OBS recording"
    },
    {
        "name": "OBS Switch Scene",
        "icon": "🎬",
        "hotkey": "ctrl+shift+s",
        "description": "Switch to next OBS scene"
    },
    {
        "name": "Spotify Play/Pause",
        "icon": "⏯️",
        "hotkey": "ctrl+shift+p",
        "description": "Toggle Spotify playback"
    },
    {
        "name": "Volume Up",
        "icon": "🔊",
        "hotkey": "volumeup",
        "description": "Increase system volume"
    },
    {
        "name": "Volume Down",
        "icon": "🔉",
        "hotkey": "volumedown",
        "description": "Decrease system volume"
    },
    {
        "name": "Mute Audio",
        "icon": "🔇",
        "hotkey": "volumemute",
        "description": "Toggle system audio mute"
    },
    {
        "name": "Screenshot",
        "icon": "📸",
        "hotkey": "win+shift+s",
        "description": "Take a screenshot (Windows Snipping Tool)"
    },
    {
        "name": "Task Manager",
        "icon": "⚙️",
        "hotkey": "ctrl+shift+esc",
        "description": "Open Windows Task Manager"
    },
]


# ============================================================================
# HOTKEY DOCUMENTATIE
# ============================================================================

HOTKEY_INFO_TEXT = """Available keys:
• Letters: a-z
• Digits: 0-9  
• Function: f1-f24
• Media: volumeup, volumedown, volumemute, playpause
• Special: space, enter, tab, esc, backspace
• Arrows: up, down, left, right"""


# ============================================================================
# MESSAGES
# ============================================================================

MSG_NO_DEVICES = "❌ Geen devices gevonden\n\nSluit je Arduino/Pico aan"
MSG_CONNECTED = "✅ Connected"
MSG_DISCONNECTED = "❌ Not Connected"
MSG_SYNC_COMPLETE = "✅ Sync complete!"
MSG_CONFIG_SAVED = "💾 Config saved"
MSG_EMPTY_HOTKEY = "❌ Main key mag niet leeg zijn!"

MSG_INFO_DEFAULT = """Click een knop om te configureren

Of kies een Quick Action en
click dan een knop"""

MSG_INFO_QUICK_ACTION = """Selected:
{icon} {name}

Hotkey: {hotkey}

Click een knop (#1-9) om
deze actie toe te wijzen"""
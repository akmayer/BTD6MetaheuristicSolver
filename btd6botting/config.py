import ctypes

ctypes.windll.user32.SetProcessDPIAware()

TOWER_PLACEMENT_KEYS = "qwertyzxcvnasdfgjklpoh"
INTERVAL_BETWEEN_ACTIONS = 0.05

TOWER_X_MIN = 60
TOWER_X_MAX = 1550
TOWER_Y_MIN = 150
TOWER_Y_MAX = 950

DISCORD_WEBHOOK = (
    # Fill in
)

# Disable notebook-style popup visuals in script mode by default.
ENABLE_DEBUG_VISUALS = False

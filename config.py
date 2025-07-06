"""
OSRS Flip Assistant Configuration
Centralized configuration management
"""

# Trading Configuration
MIN_MARGIN = 500
MIN_VOLUME = 500
MIN_UTILITY = 10000

# Excluded items that cause issues
EXCLUDED_ITEMS = [
    "Zulrah's scales",
    "Rune arrow",
    "Coal"
]

# API Configuration
HEADERS = {
    'User-Agent': 'OSRS_Flip_Assistant/1.0 - Real-time GE flipping tool - melon4free on Discord'
}

# Category definitions for item classification
CATEGORY_KEYWORDS = {
    'Raw Materials': ['ore', 'log', 'fish', 'bar', 'gem'],
    'Consumables': ['potion', 'food', 'scroll', 'seed'],
    'Runes & Ammo': ['rune', 'arrow', 'bolt'],
    'Gear & Weapons': ['sword', 'shield', 'helm', 'plate', 'bow', 'staff'],
}

# Google Sheets Integration
SHEET_NAME = 'OSRS Flipping Profits'
SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

# UI Configuration
DEFAULT_PAGE = 'opportunities'
ITEMS_PER_PAGE = 50

# Performance Settings
CACHE_TTL_SECONDS = 300  # 5 minutes
MAX_CACHE_SIZE = 1000

# Trading Strategy Presets
STRATEGY_PRESETS = {
    "Low-Risk": {
        "margin": 200,
        "volume": 1000,
        "utility": 2000,
        "description": "Conservative trading with stable items"
    },
    "High-ROI": {
        "margin": 1000,
        "volume": 500,
        "utility": 5000,
        "description": "Higher returns with increased risk"
    },
    "Passive Overnight": {
        "margin": 300,
        "volume": 200,
        "utility": 1000,
        "description": "Set-and-forget overnight flips"
    },
    "High Volume": {
        "margin": 100,
        "volume": 1000,
        "utility": 1000,
        "description": "Focus on liquid, high-volume items"
    }
}
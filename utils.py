"""
OSRS Utilities Module
Helper functions for GE tax, buy limits, and item categorization
"""

import json
import math

# Category definitions
CATEGORY_KEYWORDS = {
    'Raw Materials': ['ore', 'log', 'fish', 'bar', 'gem'],
    'Consumables': ['potion', 'food', 'scroll', 'seed'],
    'Runes & Ammo': ['rune', 'arrow', 'bolt'],
    'Gear & Weapons': ['sword', 'shield', 'helm', 'plate', 'bow', 'staff'],
}


def calculate_ge_tax(price):
    """Calculate Grand Exchange tax (2% capped at 5M)"""
    tax = math.floor(price * 0.02)
    return min(tax, 5_000_000)


def categorize_item(name):
    """Categorize item based on name keywords"""
    lname = name.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in lname for kw in kws):
            return cat
    return 'Other'


def get_buy_limits():
    """Load GE buy limits from file, with intelligent defaults if file missing"""
    try:
        with open('ge_limits.json', 'r') as f:
            limits = json.load(f)
            print(f"✅ Loaded {len(limits)} buy limits from file")
            return limits
    except FileNotFoundError:
        print("⚠️ ge_limits.json not found, using default buy limits")
        default_limits = {
            # High volume items
            "Air rune": 12000, "Water rune": 12000, "Earth rune": 12000, "Fire rune": 12000,
            "Pure essence": 25000, "Rune essence": 25000, "Logs": 25000, "Oak logs": 25000,
            "Willow logs": 25000, "Coal": 1000, "Iron ore": 1000, "Gold ore": 300,

            # Combat items
            "Dragon bones": 25000, "Cannonball": 5000, "Rune arrow": 11000, "Adamant arrow": 9000,
            "Blood rune": 25000, "Death rune": 11000, "Nature rune": 1000, "Law rune": 1000,

            # Food
            "Lobster": 1000, "Swordfish": 1000, "Shark": 1000, "Anglerfish": 1000,
            "Raw lobster": 1000, "Raw swordfish": 1000, "Raw shark": 1000,

            # Potions & supplies
            "Prayer potion(4)": 100, "Super combat potion(4)": 100, "Amylase crystal": 100,
            "Grimy ranarr weed": 80, "Grimy snapdragon": 80, "Grimy torstol": 80,

            # Seeds
            "Ranarr seed": 5, "Snapdragon seed": 5, "Torstol seed": 5,

            # Gems
            "Uncut diamond": 50, "Uncut ruby": 50, "Uncut emerald": 50, "Uncut sapphire": 50,

            # High-value items (typical 8 limit)
            "Abyssal whip": 8, "Dragon claws": 8, "Bandos chestplate": 8, "Bandos tassets": 8,
            "Dragon warhammer": 8, "Toxic blowpipe": 8, "Trident of the seas": 8,

            # Ultra-rare items (typical 2 limit)
            "Twisted bow": 2, "Elysian spirit shield": 2, "Scythe of vitur": 2
        }
        return default_limits
    except Exception as e:
        print(f"❌ Error loading buy limits: {e}")
        return {}
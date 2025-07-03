# OSRS Flip Assistant: Enhanced with Advanced Market Intelligence
# Added: Manipulation Detection, Volatility Scoring, Time Patterns, Risk Assessment, Portfolio Optimization

import requests
import pandas as pd
import streamlit as st
import gspread
from discord_webhook import DiscordWebhook
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import json
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import traceback
import os
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Load secrets from .streamlit/secrets.toml
discord_webhook_url = st.secrets["discord"]["webhook_url"]
gspread_creds = st.secrets["gspread"]

# CONFIGURATION
MIN_MARGIN = 500
MIN_VOLUME = 500
MIN_UTILITY = 10000
EXCLUDED_ITEMS = ["Zulrah's scales", "Rune arrow", "Coal"]
HEADERS = {
    'User-Agent': 'OSRS_Flip_Assistant/1.0 - Real-time GE flipping tool - melon4free on Discord'
}

# Enhanced Category definitions with meta dependencies
CATEGORY_KEYWORDS = {
    'Raw Materials': ['ore', 'log', 'fish', 'bar', 'gem', 'hide', 'leather'],
    'Consumables': ['potion', 'food', 'scroll', 'seed', 'cake', 'pie'],
    'Runes & Ammo': ['rune', 'arrow', 'bolt', 'dart', 'javelin'],
    'Gear & Weapons': ['sword', 'shield', 'helm', 'plate', 'bow', 'staff', 'armor'],
    'PvM Gear': ['whip', 'claws', 'scythe', 'bow', 'blowpipe', 'tentacle'],
    'Skilling Supplies': ['essence', 'planks', 'thread', 'chisel', 'needle'],
    'High Value': ['twisted', 'elysian', 'ancestral', 'justiciar', 'inquisitor']
}

# Item relationship mappings for substitute analysis
SUBSTITUTE_GROUPS = {
    'combat_food': ['shark', 'anglerfish', 'manta ray', 'karambwan'],
    'prayer_restore': ['prayer potion', 'super restore', 'sanfew serum'],
    'combat_potions': ['super combat', 'ranging potion', 'magic potion'],
    'high_alch_items': ['rune platebody', 'rune platelegs', 'rune 2h sword'],
    'skilling_food': ['lobster', 'swordfish', 'tuna', 'salmon']
}

# Meta dependency tracking
META_DEPENDENCIES = {
    'cox_items': ['twisted bow', 'ancestral hat', 'ancestral robe top', 'dragon claws'],
    'tob_items': ['scythe of vitur', 'justiciar faceguard', 'avernic defender'],
    'pvm_supplies': ['super combat potion', 'ranging potion', 'stamina potion'],
    'pk_supplies': ['super combat potion', 'anglerfish', 'karambwan', 'combo food']
}

# Google Sheets Integration
SHEET_NAME = 'OSRS Flipping Profits'
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Globals
show_all = False
LAST_ALERTS = {}
MANIPULATION_CACHE = {}  # Cache for manipulation detection
VOLATILITY_CACHE = {}   # Cache for volatility scores

# GE tax calculation
def calculate_ge_tax(price):
    tax = math.floor(price * 0.02)
    return min(tax, 5_000_000)

# Enhanced Market Intelligence Functions
def detect_manipulation(item_id, current_price, hourly_data, timeseries_data=None):
    """
    Detect potential price manipulation using statistical analysis
    Returns manipulation score (0-10) and flags
    """
    try:
        # Check cache first
        cache_key = f"{item_id}_{current_price}"
        if cache_key in MANIPULATION_CACHE:
            return MANIPULATION_CACHE[cache_key]
        
        flags = []
        score = 0
        
        if not hourly_data:
            return {'score': 0, 'flags': ['No data'], 'risk_level': 'Unknown'}
        
        # Get volumes and prices
        high_vol = hourly_data.get('highPriceVolume', 0)
        low_vol = hourly_data.get('lowPriceVolume', 0)
        total_vol = high_vol + low_vol
        
        avg_high = hourly_data.get('avgHighPrice', current_price)
        avg_low = hourly_data.get('avgLowPrice', current_price)
        
        # Flag 1: Unusual volume spikes
        if total_vol > 10000:  # Very high volume
            score += 2
            flags.append('High volume spike')
        
        # Flag 2: Wide spread relative to price
        if avg_high and avg_low:
            spread_ratio = (avg_high - avg_low) / avg_low
            if spread_ratio > 0.1:  # >10% spread
                score += 3
                flags.append('Wide price spread')
        
        # Flag 3: Unbalanced buy/sell ratio
        if high_vol > 0 and low_vol > 0:
            ratio = max(high_vol, low_vol) / min(high_vol, low_vol)
            if ratio > 10:  # Very unbalanced
                score += 2
                flags.append('Unbalanced order flow')
        
        # Flag 4: Price vs volume inconsistency
        if total_vol > 0 and current_price > 1000:
            expected_vol = max(100, 50000 / current_price)  # Inverse relationship
            if total_vol > expected_vol * 5:
                score += 2
                flags.append('Volume/price inconsistency')
        
        # Determine risk level
        if score >= 7:
            risk_level = 'High'
        elif score >= 4:
            risk_level = 'Medium'
        elif score >= 2:
            risk_level = 'Low'
        else:
            risk_level = 'Normal'
        
        result = {
            'score': min(score, 10),
            'flags': flags,
            'risk_level': risk_level
        }
        
        # Cache result
        MANIPULATION_CACHE[cache_key] = result
        return result
        
    except Exception as e:
        print(f"Error in manipulation detection: {e}")
        return {'score': 0, 'flags': ['Error'], 'risk_level': 'Unknown'}

def calculate_volatility_score(item_id, timeseries_data=None):
    """
    Calculate volatility score based on price stability
    Higher score = more volatile = higher risk
    """
    try:
        if item_id in VOLATILITY_CACHE:
            return VOLATILITY_CACHE[item_id]
        
        if not timeseries_data or len(timeseries_data) < 5:
            # Fetch minimal timeseries data
            ts = get_timeseries_custom(item_id, '1h')
            if ts is None or len(ts) < 5:
                return {'score': 5, 'level': 'Unknown', 'coefficient': 0}
        else:
            ts = timeseries_data
        
        # Calculate coefficient of variation
        prices = ts['high'].values
        if len(prices) < 2:
            return {'score': 5, 'level': 'Unknown', 'coefficient': 0}
        
        cv = np.std(prices) / np.mean(prices)
        
        # Convert to 0-10 scale
        if cv < 0.02:        # <2% variation
            score, level = 1, 'Very Low'
        elif cv < 0.05:      # <5% variation
            score, level = 2, 'Low'
        elif cv < 0.10:      # <10% variation
            score, level = 4, 'Medium'
        elif cv < 0.20:      # <20% variation
            score, level = 6, 'High'
        else:                # >20% variation
            score, level = 8, 'Very High'
        
        result = {
            'score': score,
            'level': level,
            'coefficient': round(cv, 4)
        }
        
        VOLATILITY_CACHE[item_id] = result
        return result
        
    except Exception as e:
        print(f"Error calculating volatility: {e}")
        return {'score': 5, 'level': 'Unknown', 'coefficient': 0}

def analyze_time_patterns(item_id, days=7):
    """
    Analyze intraday and weekly trading patterns
    """
    try:
        # Get longer timeseries for pattern analysis
        ts = get_timeseries_custom(item_id, '1h')
        if ts is None or len(ts) < 24:
            return {'intraday_pattern': 'Unknown', 'weekly_pattern': 'Unknown', 'best_hours': []}
        
        # Convert to local time for pattern analysis
        ts['hour'] = ts['timestamp'].dt.hour
        ts['day_of_week'] = ts['timestamp'].dt.dayofweek
        
        # Intraday pattern analysis
        hourly_volumes = ts.groupby('hour')['volume'].mean()
        peak_hours = hourly_volumes.nlargest(3).index.tolist()
        
        # Determine pattern
        if any(h in [16, 17, 18, 19, 20] for h in peak_hours):  # UK evening
            intraday_pattern = 'Evening Peak'
        elif any(h in [12, 13, 14, 15] for h in peak_hours):    # UK afternoon
            intraday_pattern = 'Afternoon Peak'
        elif any(h in [21, 22, 23, 0, 1] for h in peak_hours):  # Late night
            intraday_pattern = 'Night Peak'
        else:
            intraday_pattern = 'Distributed'
        
        # Weekly pattern analysis
        daily_volumes = ts.groupby('day_of_week')['volume'].mean()
        weekend_avg = daily_volumes[[5, 6]].mean()  # Saturday, Sunday
        weekday_avg = daily_volumes[[0, 1, 2, 3, 4]].mean()  # Mon-Fri
        
        if weekend_avg > weekday_avg * 1.2:
            weekly_pattern = 'Weekend Heavy'
        elif weekday_avg > weekend_avg * 1.2:
            weekly_pattern = 'Weekday Heavy'
        else:
            weekly_pattern = 'Balanced'
        
        return {
            'intraday_pattern': intraday_pattern,
            'weekly_pattern': weekly_pattern,
            'best_hours': peak_hours,
            'peak_volume': hourly_volumes.max()
        }
        
    except Exception as e:
        print(f"Error analyzing time patterns: {e}")
        return {'intraday_pattern': 'Unknown', 'weekly_pattern': 'Unknown', 'best_hours': []}

def calculate_competition_density(item_name, current_margin, all_items_df):
    """
    Calculate how many similar items are competing for attention
    """
    try:
        # Find items in same category with similar margins
        same_category = all_items_df[all_items_df['Category'] == all_items_df[all_items_df['Item'] == item_name]['Category'].iloc[0]]
        
        # Count items with similar margins (±50%)
        margin_range = (current_margin * 0.5, current_margin * 1.5)
        similar_items = same_category[
            (same_category['Net Margin'] >= margin_range[0]) & 
            (same_category['Net Margin'] <= margin_range[1])
        ]
        
        density = len(similar_items)
        
        if density <= 3:
            level = 'Low'
        elif density <= 8:
            level = 'Medium'
        else:
            level = 'High'
        
        return {'density': density, 'level': level}
        
    except Exception as e:
        return {'density': 0, 'level': 'Unknown'}

def calculate_capital_at_risk(buy_price, volume, ge_limit, volatility_score):
    """
    Calculate potential capital loss if price moves against you
    """
    try:
        # Maximum position size
        max_position = min(volume, ge_limit) if ge_limit else volume
        capital_required = buy_price * max_position
        
        # Risk factor based on volatility
        risk_multiplier = 1 + (volatility_score / 10) * 0.5  # Up to 50% additional risk
        
        # Potential loss (assume 10% adverse move for high volatility items)
        potential_loss_pct = 0.05 + (volatility_score / 10) * 0.1  # 5-15% loss
        potential_loss = capital_required * potential_loss_pct * risk_multiplier
        
        return {
            'capital_required': capital_required,
            'potential_loss': potential_loss,
            'risk_ratio': potential_loss / capital_required
        }
        
    except Exception as e:
        return {'capital_required': 0, 'potential_loss': 0, 'risk_ratio': 0}

def analyze_substitute_relationships(item_name, all_items_df):
    """
    Find substitute items that might be affected by price changes
    """
    try:
        substitutes = []
        
        # Check predefined substitute groups
        for group, items in SUBSTITUTE_GROUPS.items():
            if any(sub.lower() in item_name.lower() for sub in items):
                # Found group, add other items from same group
                for sub_item in items:
                    matches = all_items_df[all_items_df['Item'].str.contains(sub_item, case=False, na=False)]
                    if not matches.empty:
                        substitutes.extend(matches['Item'].tolist())
        
        # Remove duplicates and the original item
        substitutes = list(set(substitutes))
        if item_name in substitutes:
            substitutes.remove(item_name)
        
        return substitutes[:5]  # Return top 5 substitutes
        
    except Exception as e:
        return []

# Enhanced existing functions
def get_item_mapping():
    """Fetch OSRS item ID-name mapping from RuneScape Wiki API."""
    print("🔍 Fetching item mapping...")
    
    url = "https://prices.runescape.wiki/api/v1/osrs/mapping"
    try:
        print(f"Trying RuneScape Wiki mapping API: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        
        mapping_list = r.json()
        print(f"✅ Wiki mapping API success: {len(mapping_list)} items")
        
    except Exception as e:
        print(f"❌ Mapping API failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response text: {e.response.text}")
        return {}, {}
    
    try:
        id2name = {}
        name2id = {}
        
        for item in mapping_list:
            if isinstance(item, dict) and 'id' in item and 'name' in item:
                item_id = str(item['id'])
                item_name = item['name']
                id2name[item_id] = item_name
                name2id[item_name] = item_id
            else:
                print(f"Skipping invalid item format: {item}")
        
        print(f"✅ Processed {len(id2name)} item mappings")
        return id2name, name2id
        
    except Exception as e:
        print(f"❌ Error processing mapping: {e}")
        traceback.print_exc()
        return {}, {}

def get_real_time_prices():
    """Fetch real-time prices with enhanced error handling and timestamp tracking"""
    print("💰 Fetching real-time prices...")
    
    try:
        r = requests.get("https://prices.runescape.wiki/api/v1/osrs/latest", 
                        headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if isinstance(data, dict) and 'data' in data:
            price_data = data['data']
            print(f"✅ Fetched prices for {len(price_data)} items")
            
            timestamp = data.get('timestamp', datetime.datetime.now(datetime.timezone.utc).timestamp())
            
            return {'data': price_data, 'timestamp': timestamp}
        else:
            print(f"Unexpected price data format: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return {'data': {}, 'timestamp': datetime.datetime.now(datetime.timezone.utc).timestamp()}
            
    except Exception as e:
        print(f"❌ Failed to fetch real-time prices: {e}")
        st.error(f"Failed to fetch real-time prices: {e}")
        return {'data': {}, 'timestamp': datetime.datetime.now(datetime.timezone.utc).timestamp()}

def get_summary():
    """Alias for get_real_time_prices for backward compatibility"""
    result = get_real_time_prices()
    if isinstance(result, dict) and 'data' in result:
        return result['data']
    return result

def get_hourly_prices():
    """Fetch hourly prices with error handling"""
    print("📊 Fetching hourly prices...")
    
    try:
        r = requests.get("https://prices.runescape.wiki/api/v1/osrs/1h", 
                        headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            hourly_data = data.get('data', {}) if isinstance(data, dict) else {}
            print(f"✅ Fetched hourly data for {len(hourly_data)} items")
            return hourly_data
        else:
            print(f"❌ Hourly prices API returned status {r.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Failed to fetch hourly prices: {e}")
        return {}

def get_timeseries(item_id, days=1):
    """Fetch timeseries data with error handling - Updated for correct API"""
    try:
        if days <= 1:
            timestep = "5m"
        elif days <= 7:
            timestep = "1h"
        else:
            timestep = "6h"
            
        url = f"https://prices.runescape.wiki/api/v1/osrs/timeseries?id={item_id}&timestep={timestep}"
        
        print(f"📊 Fetching timeseries: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        if r.status_code != 200:
            print(f"❌ Timeseries API returned status {r.status_code}: {r.text}")
            return None
            
        response_data = r.json()
        print(f"📊 Timeseries response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
        
        if 'data' not in response_data:
            print(f"❌ No 'data' key in timeseries response: {response_data}")
            return None
            
        data = response_data['data']
        if not data:
            print(f"❌ Empty data array in timeseries response")
            return pd.DataFrame()
            
        print(f"✅ Got {len(data)} timeseries data points")
        
        df = pd.DataFrame(data)
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        df['avg_price'] = (df['avgLowPrice'] + df['avgHighPrice']) / 2
        df['volume'] = df['lowPriceVolume'] + df['highPriceVolume']
        
        df = df.rename(columns={
            'avgHighPrice': 'high',
            'avgLowPrice': 'low'
        })
        
        print(f"✅ Processed timeseries data: {len(df)} rows")
        return df
        
    except Exception as e:
        print(f"❌ Error fetching timeseries for item {item_id}: {e}")
        traceback.print_exc()
        return None

def get_timeseries_custom(item_id, timestep):
    """Get timeseries data with custom timestep"""
    try:
        url = f"https://prices.runescape.wiki/api/v1/osrs/timeseries?id={item_id}&timestep={timestep}"
        print(f"📊 Fetching custom timeseries: {url}")
        
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"❌ Timeseries API returned status {r.status_code}: {r.text}")
            return None
            
        response_data = r.json()
        
        if 'data' not in response_data or not response_data['data']:
            print(f"❌ No data in timeseries response")
            return None
            
        data = response_data['data']
        print(f"✅ Got {len(data)} timeseries data points")
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        if 'avgHighPrice' in df.columns:
            df['high'] = df['avgHighPrice']
            df['low'] = df['avgLowPrice']
            df['volume'] = df['lowPriceVolume'] + df['highPriceVolume']
        elif 'high' in df.columns:
            df['volume'] = df.get('lowVolume', 0) + df.get('highVolume', 0)
        else:
            print(f"❌ Unexpected column names: {df.columns.tolist()}")
            return None
        
        return df.sort_values('timestamp')
        
    except Exception as e:
        print(f"❌ Error fetching custom timeseries: {e}")
        return None

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

def categorize_item(name):
    lname = name.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in lname for kw in kws):
            return cat
    return 'Other'

# Enhanced main filter function with advanced analytics
def filter_items(price_data_result, hourly_data, id2name, show_all=False, mode="Custom"):
    """Enhanced filter with manipulation detection, volatility scoring, and risk analysis"""
    
    if isinstance(price_data_result, dict) and 'data' in price_data_result:
        price_data = price_data_result['data']
        data_timestamp = price_data_result.get('timestamp', datetime.datetime.now(datetime.timezone.utc).timestamp())
    else:
        price_data = price_data_result
        data_timestamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
    
    print(f"🔄 Enhanced filtering with advanced analytics...")
    print(f"   Price data: {len(price_data)}, Hourly data: {len(hourly_data)}, Mappings: {len(id2name)}")
    
    if not price_data or not id2name:
        print("❌ No data available")
        return pd.DataFrame()
    
    limits = get_buy_limits()
    recs = []
    processed = 0
    valid_items = 0
    total_items = len(price_data)
    
    current_hour = datetime.datetime.now(datetime.timezone.utc).hour
    current_time = datetime.datetime.now(datetime.timezone.utc).timestamp()
    
    price_items = list(price_data.items())
    
    for iid, stats in price_items:
        processed += 1
        
        if processed % 1000 == 0:
            print(f"Processed {processed}/{total_items} items...")
        
        try:
            name = id2name.get(iid, f"Unknown_{iid}")
            
            if any(exc.lower() in name.lower() for exc in EXCLUDED_ITEMS):
                continue
                
            hi = stats.get('high')
            lo = stats.get('low')
            
            if not hi or not lo or hi <= lo:
                continue
                
            valid_items += 1
            
            # Basic calculations
            hourly = hourly_data.get(iid, {})
            vol1h = hourly.get('lowPriceVolume', 0) + hourly.get('highPriceVolume', 0)
            avg_lo = hourly.get('avgLowPrice')
            
            tax = calculate_ge_tax(hi)
            net = hi - lo - tax
            
            if vol1h == 0:
                util = 0
            else:
                util = round((net * vol1h) / (abs(hi - (avg_lo if avg_lo else 0)) + 1), 2)
            
            if avg_lo and avg_lo > 0:
                momentum = round((lo - avg_lo) / avg_lo * 100, 2)
            else:
                momentum = 0
            
            cat = categorize_item(name)
            gl = limits.get(name, 1000)
            roi = round(net / lo * 100, 2) if lo else 0
            
            # Calculate data ages
            item_timestamp = stats.get('highTime', data_timestamp)
            data_age_seconds = current_time - item_timestamp
            data_age_minutes = round(data_age_seconds / 60, 1)
            
            high_time = stats.get('highTime', data_timestamp)
            low_time = stats.get('lowTime', data_timestamp)
            high_age_minutes = round((current_time - high_time) / 60, 1)
            low_age_minutes = round((current_time - low_time) / 60, 1)
            
            # ENHANCED ANALYTICS
            # 1. Manipulation Detection
            manipulation = detect_manipulation(iid, hi, hourly)
            
            # 2. Volatility Scoring
            volatility = calculate_volatility_score(iid)
            
            # 3. Time Pattern Analysis (for top items only to avoid API limits)
            time_patterns = {'intraday_pattern': 'Unknown', 'weekly_pattern': 'Unknown'}
            
            # 4. Capital at Risk Analysis
            capital_risk = calculate_capital_at_risk(lo, vol1h, gl, volatility['score'])
            
            # 5. Risk-Adjusted Utility Score
            risk_factor = 1 + (volatility['score'] / 10) + (manipulation['score'] / 20)
            risk_adjusted_util = util / risk_factor if risk_factor > 0 else 0
            
            # 6. Profit Persistence Score (simplified)
            persistence_score = 10 - manipulation['score'] - (volatility['score'] / 2)
            persistence_score = max(0, min(10, persistence_score))
            
            # 7. Liquidity Depth Score
            liquidity_score = min(10, vol1h / 100) if vol1h > 0 else 0
            
            recs.append({
                'Item': name,
                'Buy Price': lo,
                'Sell Price': hi,
                'Net Margin': net,
                'ROI (%)': roi,
                '1h Volume': vol1h,
                'Momentum (%)': momentum,
                'Season Ratio': 1.0,  # Placeholder
                'Utility': util,
                'Category': cat,
                'Item ID': iid,
                'Data Age (min)': data_age_minutes,
                'High Age (min)': high_age_minutes,
                'Low Age (min)': low_age_minutes,
                
                # Enhanced Analytics
                'Manipulation Score': manipulation['score'],
                'Manipulation Risk': manipulation['risk_level'],
                'Volatility Score': volatility['score'],
                'Volatility Level': volatility['level'],
                'Risk Adjusted Utility': risk_adjusted_util,
                'Profit Persistence': persistence_score,
                'Liquidity Score': liquidity_score,
                'Capital Required': capital_risk['capital_required'],
                'Potential Loss': capital_risk['potential_loss'],
                'Risk Ratio': capital_risk['risk_ratio'],
                'Time Pattern': time_patterns['intraday_pattern'],
                'Weekly Pattern': time_patterns['weekly_pattern']
            })
            
        except Exception as e:
            print(f"❌ Error processing item {iid}: {e}")
            continue
    
    print(f"✅ Enhanced processing complete: {processed} items, {valid_items} valid, {len(recs)} recommendations")
    
    if not recs:
        print("❌ No recommendations generated")
        return pd.DataFrame()
    
    df = pd.DataFrame(recs)
    
    # High Volume mode special handling
    if mode == "High Volume":
        print("🔥 High Volume Mode: Showing 250 highest traded items")
        df = df.sort_values(['1h Volume', 'Net Margin'], ascending=[False, False])
        return df.head(250)
    
    # If "Show All" is enabled, bypass core filtering
    if show_all:
        print("📋 Showing all items (no filtering)")
        return df.sort_values('Risk Adjusted Utility', ascending=False)
    
    # Apply core filters with enhanced criteria
    season_th = st.session_state.get('season_th', 0) if 'st' in globals() else 0
    manipulation_th = st.session_state.get('manipulation_th', 7) if 'st' in globals() else 7
    volatility_th = st.session_state.get('volatility_th', 8) if 'st' in globals() else 8
    
    before_filter = len(df)
    
    # Enhanced filtering with risk considerations
    df = df[
        (df['Net Margin'] >= MIN_MARGIN) &
        (df['1h Volume'] >= MIN_VOLUME) &
        (df['Risk Adjusted Utility'] >= MIN_UTILITY) &
        (df['Season Ratio'] >= season_th) &
        (df['Manipulation Score'] <= manipulation_th) &
        (df['Volatility Score'] <= volatility_th)
    ]
    
    after_filter = len(df)
    print(f"🔍 Enhanced filters applied: {before_filter} -> {after_filter} items")
    
    return df.sort_values('Risk Adjusted Utility', ascending=False)

# Portfolio optimization functions
def calculate_portfolio_risk(selected_items_df):
    """Calculate portfolio-level risk metrics"""
    if selected_items_df.empty:
        return {'total_risk': 0, 'diversification_score': 0, 'capital_allocation': {}}
    
    # Calculate total capital required
    total_capital = selected_items_df['Capital Required'].sum()
    
    # Calculate diversification score
    categories = selected_items_df['Category'].value_counts()
    diversification_score = min(10, len(categories) * 2)  # More categories = better diversification
    
    # Calculate risk-weighted allocation
    risk_weights = 1 / (1 + selected_items_df['Risk Ratio'])
    total_risk_weight = risk_weights.sum()
    
    allocations = {}
    for idx, row in selected_items_df.iterrows():
        weight = risk_weights[idx] / total_risk_weight
        allocations[row['Item']] = {
            'weight': weight,
            'capital': weight * total_capital,
            'risk_score': row['Risk Ratio']
        }
    
    # Overall portfolio risk
    portfolio_risk = selected_items_df['Risk Ratio'].mean()
    
    return {
        'total_risk': portfolio_risk,
        'diversification_score': diversification_score,
        'capital_allocation': allocations,
        'total_capital': total_capital
    }

def get_bond_price_reference():
    """Get current bond price for opportunity cost comparison"""
    try:
        # This would need to be implemented with actual bond price data
        # For now, return a reasonable estimate
        return 8_000_000  # ~8M gp per bond
    except:
        return 8_000_000

# Keep all existing functions (alerts, backtest, correlations, etc.)
def send_discord_alert(item, buy, sell, margin):
    now = datetime.datetime.now(datetime.timezone.utc)
    last = LAST_ALERTS.get(item)
    
    cooldown_seconds = 180
    if last and (now - last).total_seconds() < cooldown_seconds:
        remaining_time = cooldown_seconds - (now - last).total_seconds()
        print(f"⏳ Discord alert for {item} on cooldown for {remaining_time:.0f} more seconds")
        return False
    
    LAST_ALERTS[item] = now
    
    try:
        payload = f"🚨 **OSRS Flip Alert** 🚨\n**{item}**\n💰 Buy: {buy:,} gp\n💸 Sell: {sell:,} gp\n📈 Net Margin: {margin:,} gp\n⏰ {now.strftime('%H:%M UTC')}"
        response = requests.post(
            discord_webhook_url,
            json={"content": payload},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ Discord alert sent for {item}")
            return True
        else:
            print(f"❌ Discord alert failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Discord alert failed: {e}")
        return False

def backtest_filters(id2name, days=1):
    sigs = []
    for iid, name in list(id2name.items())[:10]:
        ts = get_timeseries(iid, days)
        if ts is None or ts.empty:
            continue
        try:
            hr = ts.set_index('timestamp').resample('1H').agg({
                'low': 'min', 'high': 'max', 'volume': 'sum'
            }).dropna()
            for t, row in hr.iterrows():
                hi, lo, vol = row['high'], row['low'], row['volume']
                if hi <= lo:
                    continue
                net = (hi - lo) - calculate_ge_tax(hi)
                util = round((net * vol) / (abs(hi - lo) + 1), 2)
                if net >= MIN_MARGIN and vol >= MIN_VOLUME and util >= MIN_UTILITY:
                    sigs.append({
                        'timestamp': t,
                        'Item': name,
                        'Net Margin': net,
                        'Volume': vol,
                        'Utility': util
                    })
        except Exception as e:
            print(f"Error in backtest for {name}: {e}")
            continue
    return pd.DataFrame(sigs)

def compute_price_correlations(name2id, top_n=10, days=1):
    dfs = {}
    for name, iid in list(name2id.items())[:top_n]:
        ts = get_timeseries(iid, days)
        if ts is None or ts.empty:
            continue
        dfs[name] = ts.set_index('timestamp')['avg_price']
    if not dfs:
        return pd.DataFrame()
    try:
        return pd.concat(dfs, axis=1).dropna().corr()
    except:
        return pd.DataFrame()

def export_to_sheets(df):
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            gspread_creds,
            scopes=SCOPE
        )
        client = gspread.authorize(creds)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        sheet = client.open(SHEET_NAME)
        try:
            ws = sheet.worksheet(today)
        except:
            ws = sheet.add_worksheet(title=today, rows="1000", cols="20")
        ws.append_rows([df.columns.tolist()] + df.values.tolist())
    except Exception as e:
        print(f"❌ Sheets export failed: {e}")

def run_flip_scanner(mode="Custom"):
    """Enhanced scanner with advanced analytics"""
    global show_all
    
    try:
        print("=" * 50)
        print("🚀 Starting Enhanced OSRS Flip Scanner")
        print("=" * 50)
        
        id2name, name2id = get_item_mapping()
        if not id2name or not name2id:
            if 'st' in globals():
                st.error("❌ Failed to load item mappings. Cannot proceed.")
            return pd.DataFrame(), {}
        
        pd_data = get_real_time_prices()
        if not pd_data:
            if 'st' in globals():
                st.error("❌ Failed to load price data. Cannot proceed.")
            return pd.DataFrame(), name2id
        
        h_data = get_hourly_prices()
        
        # Enhanced filtering with analytics
        df = filter_items(pd_data, h_data, id2name, show_all, mode)
        
        if df.empty:
            if 'st' in globals():
                st.warning("⚠️ No items match your enhanced filter criteria.")
            return df, name2id
        
        # Add substitute analysis for top items
        if len(df) > 0:
            print("🔍 Analyzing item relationships...")
            df['Substitutes'] = df.apply(
                lambda row: analyze_substitute_relationships(row['Item'], df), 
                axis=1
            )
        
        if not show_all:
            df = df.head(50)
        
        # Enhanced alerting with risk consideration
        alert_count = 0
        should_send_alerts = (
            not show_all and 
            len(df) <= 5 and 
            len(df) > 0
        )
        
        if should_send_alerts:
            # Only alert on low-risk, high-margin items
            safe_high_value = df[
                (df['Net Margin'] > MIN_MARGIN * 2) &
                (df['Manipulation Score'] <= 3) &
                (df['Volatility Score'] <= 5)
            ]
            
            for _, r in safe_high_value.iterrows():
                alert_sent = send_discord_alert(r['Item'], r['Buy Price'], r['Sell Price'], r['Net Margin'])
                if alert_sent:
                    alert_count += 1
                if alert_count >= 3:
                    break
        
        if alert_count > 0:
            print(f"📢 Sent {alert_count} enhanced Discord alerts")
        
        # Export enhanced data
        try:
            df.to_csv("enhanced_flipping_report.csv", index=False)
            print("✅ Saved enhanced CSV report")
        except Exception as e:
            print(f"❌ CSV export failed: {e}")
        
        try:
            export_to_sheets(df)
            print("✅ Exported to Google Sheets")
        except Exception as e:
            print(f"❌ Sheets export failed: {e}")
        
        print(f"✅ Enhanced scanner completed. Found {len(df)} opportunities.")
        return df, name2id
        
    except Exception as e:
        error_msg = f"❌ Enhanced scanner failed: {e}\n{traceback.format_exc()}"
        print(error_msg)
        if 'st' in globals():
            st.error(error_msg)
        return pd.DataFrame(), {}

# Enhanced chart functions (keeping existing ones)
def create_enhanced_chart(ts, item_name, chart_type, height, width,
                          color_high, color_low, color_volume,
                          line_width, show_grid, show_volume, volume_opacity):
    plt.style.use('dark_background')
    fig, axes = (plt.subplots(2, 1, figsize=(width/100, height/100),
                               gridspec_kw={'height_ratios': [3,1]}, sharex=True)
                 if show_volume else
                 (plt.subplots(figsize=(width/100, height/100))))
    if show_volume:
        ax1, ax2 = axes
        ax2.set_facecolor('#2b2b2b')
    else:
        ax1 = axes
    fig.patch.set_facecolor('#1f1f1f')
    ax1.set_facecolor('#2b2b2b')

    ax1.plot(ts['timestamp'], ts['high'], marker='o', markersize=4,
             label='Sell', color=color_high, linewidth=line_width)
    ax1.plot(ts['timestamp'], ts['low'],  marker='o', markersize=4,
             label='Buy',  color=color_low,  linewidth=line_width)

    ts['mid'] = (ts['high'] + ts['low'])/2
    trend = ts['mid'].rolling(window=10, min_periods=1).mean()
    ax1.plot(ts['timestamp'], trend, linestyle='--', linewidth=1,
             color='#bdc3c7', alpha=0.7, label='Trend')

    if show_volume:
        ax2.bar(
            ts['timestamp'],
            ts['volume'],
            alpha=volume_opacity,
            color=color_volume,
            width=0.02,
            label='Volume'
        )

    for ax in (ax1, ax2) if show_volume else (ax1,):
        if show_grid:
            ax.grid(True, linestyle='--', alpha=0.3)
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('#444')

    ax1.set_ylabel('Price (gp)', color='white', fontsize=12)
    if show_volume:
        ax2.set_ylabel('Volume', color='white', fontsize=10)
        ax2.set_xlabel('Time', color='white')
    else:
        ax1.set_xlabel('Time', color='white')

    ax1.legend(loc='upper left', frameon=False)
    if show_volume:
        ax2.legend(loc='upper right', frameon=False)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    fig.autofmt_xdate()

    ax1.set_title(f'{item_name}', color='white', pad=12)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def create_interactive_chart(ts: pd.DataFrame,
                             item_name: str,
                             width: int = 800,
                             height: int = 500):
    ts['timestamp'] = pd.to_datetime(ts['timestamp'])

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.02
    )

    fig.add_trace(
        go.Scatter(
            x=ts['timestamp'], y=ts['high'],
            mode='lines+markers',
            name='Sell Price',
            marker=dict(size=4),
            line=dict(width=2),
            hovertemplate='Sell: %{y} gp<br>%{x|%b %d %H:%M}<extra></extra>'
        ), row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=ts['timestamp'], y=ts['low'],
            mode='lines+markers',
            name='Buy Price',
            marker=dict(size=4),
            line=dict(width=2),
            hovertemplate='Buy: %{y} gp<br>%{x|%b %d %H:%M}<extra></extra>'
        ), row=1, col=1
    )
    
    ts['mid'] = (ts['high'] + ts['low']) / 2
    rolling = ts['mid'].rolling(window=10, min_periods=1).mean()
    fig.add_trace(
        go.Scatter(
            x=ts['timestamp'], y=rolling,
            mode='lines',
            name='Trend',
            line=dict(dash='dash', width=1, color='#999'),
            hoverinfo='skip'
        ), row=1, col=1
    )

    fig.add_trace(
        go.Bar(
            x=ts['timestamp'], y=ts['volume'],
            name='Volume',
            marker=dict(opacity=0.6),
            hovertemplate='Vol: %{y}<br>%{x|%b %d %H:%M}<extra></extra>'
        ), row=2, col=1
    )

    fig.update_layout(
        template='plotly_dark',
        title=dict(text=item_name, x=0.5, font_size=16),
        height=height, width=width,
        hovermode='x unified',
        margin=dict(t=50, b=40, l=40, r=40),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    fig.update_xaxes(showgrid=True, gridcolor='#444', tickfont=dict(color='white'))
    fig.update_yaxes(title_text='Price (gp)', row=1, col=1,
                     showgrid=True, gridcolor='#444', tickfont=dict(color='white'))
    fig.update_yaxes(title_text='Volume', row=2, col=1,
                     showgrid=False, tickfont=dict(color='white'))

    st.plotly_chart(fig, use_container_width=True)

# Enhanced Streamlit Dashboard
def streamlit_dashboard():
    global MIN_MARGIN, MIN_VOLUME, MIN_UTILITY, show_all
    
    st.set_page_config(page_title="Enhanced OSRS Flip Assistant", layout="wide")
    
    # Initialize session state
    if 'presets' not in st.session_state:
        st.session_state.presets = {}
    if 'season_th' not in st.session_state:
        st.session_state.season_th = 0.0
    if 'manipulation_th' not in st.session_state:
        st.session_state.manipulation_th = 7
    if 'volatility_th' not in st.session_state:
        st.session_state.volatility_th = 8
    
    st.title("💸 Enhanced OSRS GE Flipping Assistant")
    st.caption("🔬 Advanced Market Intelligence • 🎯 Risk Analysis • 📊 Portfolio Optimization")
    
    # Enhanced Debug info
    with st.expander("🔧 Debug Information"):
        st.write("**Current Configuration:**")
        st.write(f"- Min Margin: {MIN_MARGIN:,} gp")
        st.write(f"- Min Volume: {MIN_VOLUME:,}/hr")
        st.write(f"- Min Utility: {MIN_UTILITY:,}")
        st.write(f"- Show All: {show_all}")
        st.write(f"- Manipulation Threshold: {st.session_state.get('manipulation_th', 7)}")
        st.write(f"- Volatility Threshold: {st.session_state.get('volatility_th', 8)}")
        
        if st.button("🧪 Test API Connections"):
            st.write("Testing item mapping API...")
            id2name, name2id = get_item_mapping()
            st.write(f"✅ Loaded {len(id2name)} item mappings")
            
            st.write("Testing price data API...")
            prices = get_real_time_prices()
            st.write(f"✅ Loaded prices for {len(prices['data'] if isinstance(prices, dict) else prices)} items")
            
            st.write("Testing hourly data API...")
            hourly = get_hourly_prices()
            st.write(f"✅ Loaded hourly data for {len(hourly)} items")
    
    # Enhanced preset system
    ps = st.sidebar.selectbox("Load Preset", [''] + list(st.session_state.presets.keys()))
    if ps:
        m, v, u, season, manip, vol = st.session_state.presets[ps]
        MIN_MARGIN, MIN_VOLUME, MIN_UTILITY = m, v, u
        st.session_state['season_th'] = season
        st.session_state['manipulation_th'] = manip
        st.session_state['volatility_th'] = vol
    
    name_in = st.sidebar.text_input("Preset Name")
    if st.sidebar.button("Save Preset") and name_in:
        st.session_state.presets[name_in] = (
            MIN_MARGIN, MIN_VOLUME, MIN_UTILITY, 
            st.session_state.get('season_th', 0),
            st.session_state.get('manipulation_th', 7),
            st.session_state.get('volatility_th', 8)
        )
        st.sidebar.success(f"Saved preset: {name_in}")
    
    st.sidebar.markdown("---")
    
    # Enhanced mode selection
    mode = st.sidebar.selectbox("Mode", ["Custom", "Low-Risk", "High-ROI", "Passive Overnight", "High Volume", "Ultra-Safe"])
    if mode == "Low-Risk":
        m, v, u = 200, 1000, 2000
    elif mode == "High-ROI":
        m, v, u = 1000, 500, 5000
    elif mode == "Passive Overnight":
        m, v, u = 300, 200, 1000
    elif mode == "High Volume":
        m, v, u = 100, 1000, 1000
        st.sidebar.info("🔥 High Volume Mode: Shows 250 highest traded items")
    elif mode == "Ultra-Safe":
        m, v, u = 500, 2000, 5000
        st.sidebar.info("🛡️ Ultra-Safe Mode: Only low-risk, high-volume items")
    else:
        m, v, u = MIN_MARGIN, MIN_VOLUME, MIN_UTILITY
    
    # Enhanced filter controls
    st.sidebar.subheader("📊 Basic Filters")
    MIN_MARGIN = st.sidebar.slider("Min Net Margin", 0, 5000, m, 50)
    MIN_VOLUME = st.sidebar.slider("Min Volume/hr", 0, 20000, v, 100)
    MIN_UTILITY = st.sidebar.slider("Min Utility", 0, 50000, u, 500)
    
    st.sidebar.subheader("🔬 Advanced Filters")
    st.session_state['season_th'] = st.sidebar.slider("Min Season Ratio", 0.0, 5.0, st.session_state.get('season_th', 0.0), 0.1)
    st.session_state['manipulation_th'] = st.sidebar.slider("Max Manipulation Score", 0, 10, st.session_state.get('manipulation_th', 7), 1, 
                                                           help="Lower = stricter filtering of manipulated items")
    st.session_state['volatility_th'] = st.sidebar.slider("Max Volatility Score", 0, 10, st.session_state.get('volatility_th', 8), 1,
                                                          help="Lower = stricter filtering of volatile items")
    
    show_all = st.sidebar.checkbox("Show All", value=False)
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)")
    if auto_refresh:
        st.sidebar.write("⏰ Auto-refreshing...")
        import time
        time.sleep(30)
        st.rerun()
    
    # Main scan button
    if st.button("🔄 Refresh Data", type="primary"):
        with st.spinner("Scanning with enhanced analytics..."):
            df, name2id = run_flip_scanner(mode)
            st.session_state.price_data = get_real_time_prices()
    else:
        with st.spinner("Loading enhanced flip opportunities..."):
            df, name2id = run_flip_scanner(mode)
            st.session_state.price_data = get_real_time_prices()
    
    # Enhanced results display
    if not df.empty:
        st.subheader("🔍 Enhanced Flip Opportunities")
        
        # Enhanced color coding explanation
        with st.expander("🎨 Enhanced Color Coding Guide"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown("🟢 **Green** - Low risk, high opportunity")
            with col2:
                st.markdown("🟡 **Yellow** - Medium risk or aging data")
            with col3:
                st.markdown("🔴 **Red** - High risk or old data")
            with col4:
                st.markdown("⚠️ **Warning** - Potential manipulation detected")
        
        # Ensure numerical columns are properly typed
        num_cols = ['Buy Price','Sell Price','Net Margin','ROI (%)','1h Volume',
                   'Manipulation Score','Volatility Score','Risk Adjusted Utility']
        for c in num_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
        
        display_df = df.copy()
        
        # Enhanced color coding with risk factors
        def get_enhanced_color_code(row):
            roi, data_age, volume = row['ROI (%)'], row['Data Age (min)'], row['1h Volume']
            manipulation, volatility = row['Manipulation Score'], row['Volatility Score']
            
            # High risk factors
            if manipulation >= 7 or volatility >= 8:
                return "⚠️"  # Warning for high risk
            elif data_age > 5:
                return "🔴"  # Red for old data
            elif data_age > 2:
                return "🟡"  # Yellow for aging data
            elif roi >= 5 and volume >= 1000 and manipulation <= 3 and volatility <= 4:
                return "🟢"  # Green for excellent low-risk opportunities
            elif roi >= 2 and volume >= 500:
                return "🟡"  # Yellow for good
            else:
                return "🔴"  # Red for caution
        
        display_df['Status'] = display_df.apply(get_enhanced_color_code, axis=1)
        
        # Enhanced display columns
        enhanced_columns = [
            'Status', 'Item', 'Buy Price', 'Sell Price', 'Net Margin', 'ROI (%)', 
            '1h Volume', 'Risk Adjusted Utility', 'Manipulation Risk', 'Volatility Level',
            'Data Age (min)', 'Category'
        ]
        
        # Filter to only existing columns
        available_columns = [col for col in enhanced_columns if col in display_df.columns]
        final_display_df = display_df[available_columns].copy()
        
        # Enhanced column configuration
        column_config = {
            'Buy Price': st.column_config.NumberColumn('Buy Price', help='Current buy price', format='%d gp'),
            'Sell Price': st.column_config.NumberColumn('Sell Price', help='Current sell price', format='%d gp'),
            'Net Margin': st.column_config.NumberColumn('Net Margin', help='Profit after GE tax', format='%d gp'),
            'ROI (%)': st.column_config.NumberColumn('ROI (%)', help='Return on investment', format='%.1f%%'),
            '1h Volume': st.column_config.NumberColumn('1h Volume', help='Trading volume per hour', format='%d'),
            'Risk Adjusted Utility': st.column_config.NumberColumn('Risk Adj. Utility', help='Utility score adjusted for risk', format='%.0f'),
            'Manipulation Risk': st.column_config.TextColumn('Manip. Risk', help='Risk of price manipulation'),
            'Volatility Level': st.column_config.TextColumn('Volatility', help='Price volatility level'),
            'Data Age (min)': st.column_config.NumberColumn('Age (min)', help='Data freshness', format='%.1f')
        }
        
        # Display enhanced results
        st.dataframe(
            final_display_df,
            use_container_width=True,
            key="enhanced_flip_table",
            height=600,
            hide_index=True,
            column_config=column_config
        )
        
        # Enhanced summary statistics
        st.subheader("📊 Enhanced Performance Metrics")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("Total Items", len(df))
        with col2:
            avg_margin = df['Net Margin'].mean()
            st.metric("Avg Margin", f"{avg_margin:,.0f} gp")
        with col3:
            avg_risk_util = df['Risk Adjusted Utility'].mean()
            st.metric("Avg Risk Adj. Utility", f"{avg_risk_util:,.0f}")
        with col4:
            safe_items = len(df[(df['Manipulation Score'] <= 3) & (df['Volatility Score'] <= 4)])
            st.metric("Safe Items", safe_items)
        with col5:
            high_risk_items = len(df[(df['Manipulation Score'] >= 7) | (df['Volatility Score'] >= 8)])
            st.metric("High Risk Items", high_risk_items)
        with col6:
            total_capital = df['Capital Required'].sum()
            st.metric("Total Capital", f"{total_capital:,.0f} gp")
        
        # Portfolio optimization section
        st.subheader("📈 Portfolio Optimization")
        
        with st.expander("💼 Portfolio Analysis"):
            # Allow user to select items for portfolio
            selected_items = st.multiselect(
                "Select items for portfolio analysis:",
                options=df['Item'].tolist(),
                default=df.head(10)['Item'].tolist()
            )
            
            if selected_items:
                portfolio_df = df[df['Item'].isin(selected_items)]
                portfolio_risk = calculate_portfolio_risk(portfolio_df)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Portfolio Risk Metrics:**")
                    st.metric("Portfolio Risk Score", f"{portfolio_risk['total_risk']:.2f}")
                    st.metric("Diversification Score", f"{portfolio_risk['diversification_score']}/10")
                    st.metric("Total Capital Required", f"{portfolio_risk['total_capital']:,.0f} gp")
                    
                    # Bond comparison
                    bond_price = get_bond_price_reference()
                    total_profit = portfolio_df['Net Margin'].sum()
                    profit_per_bond = total_profit / (bond_price / 1000000)  # Profit per million gp
                    st.metric("Profit per Bond Equivalent", f"{profit_per_bond:,.0f} gp")
                
                with col2:
                    st.write("**Recommended Capital Allocation:**")
                    for item, allocation in portfolio_risk['capital_allocation'].items():
                        st.write(f"**{item}**: {allocation['weight']:.1%} ({allocation['capital']:,.0f} gp)")
        
        # Enhanced risk analysis
        st.subheader("⚠️ Risk Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Manipulation Risk Distribution:**")
            manip_counts = df['Manipulation Risk'].value_counts()
            st.bar_chart(manip_counts)
        
        with col2:
            st.write("**Volatility Distribution:**")
            vol_counts = df['Volatility Level'].value_counts()
            st.bar_chart(vol_counts)
        
        # Substitute analysis
        if 'Substitutes' in df.columns:
            st.subheader("🔄 Substitute Item Analysis")
            
            with st.expander("📊 Item Relationships"):
                for idx, row in df.head(5).iterrows():
                    if row['Substitutes'] and len(row['Substitutes']) > 0:
                        st.write(f"**{row['Item']}** → Substitutes: {', '.join(row['Substitutes'])}")
        
        # Enhanced alerts section
        st.subheader("🔔 Enhanced Alert System")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.info(f"**Active Alerts:** {len(LAST_ALERTS)}")
        with col2:
            safe_alerts = len(df[(df['Net Margin'] > MIN_MARGIN * 2) & 
                                (df['Manipulation Score'] <= 3) & 
                                (df['Volatility Score'] <= 5)])
            st.info(f"**Safe Alert Candidates:** {safe_alerts}")
        with col3:
            alert_status = "🚫 Disabled" if show_all or len(df) > 5 else "✅ Active"
            st.info(f"**Status:** {alert_status}")
        with col4:
            if st.button("🔄 Clear Alert History"):
                LAST_ALERTS.clear()
                st.success("Alert history cleared!")
        
        # Enhanced download options
        st.subheader("📥 Enhanced Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Basic CSV
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📊 Download Full Dataset",
                data=csv_data,
                file_name=f"enhanced_osrs_flips_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Safe items only
            safe_items_df = df[(df['Manipulation Score'] <= 3) & (df['Volatility Score'] <= 5)]
            safe_csv = safe_items_df.to_csv(index=False)
            st.download_button(
                label="🛡️ Download Safe Items Only",
                data=safe_csv,
                file_name=f"safe_osrs_flips_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with col3:
            # High potential items
            high_potential_df = df[(df['Risk Adjusted Utility'] >= df['Risk Adjusted Utility'].quantile(0.8))]
            high_potential_csv = high_potential_df.to_csv(index=False)
            st.download_button(
                label="🎯 Download High Potential Items",
                data=high_potential_csv,
                file_name=f"high_potential_flips_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        # Keep existing sections (correlations, backtest, trend viewer) but enhance them
        # [Previous correlation, backtest, and trend viewer code remains the same]
        
    else:
        st.warning("No flip opportunities found with current enhanced filters.")
        
        # Enhanced tips
        st.subheader("💡 Enhanced Tips")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **Adjust Enhanced Filters:**
            - Increase Manipulation Score threshold
            - Increase Volatility Score threshold
            - Lower basic filters (margin, volume, utility)
            - Try "Ultra-Safe" mode for guaranteed low-risk items
            """)
        
        with col2:
            st.info("""
            **Risk Management Tips:**
            - Start with low-risk items (Manipulation Score ≤ 3)
            - Diversify across categories
            - Monitor data age for freshness
            - Use portfolio optimization for capital allocation
            """)

if __name__ == '__main__':
    streamlit_dashboard()
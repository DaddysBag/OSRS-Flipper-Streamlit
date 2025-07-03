# OSRS Flip Assistant: Real-Time GE Flipping Dashboard + Alerts + Export
# FIXED VERSION - Resolved syntax errors and other issues

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

# Load secrets from .streamlit/secrets.toml
discord_webhook_url = st.secrets["discord"]["webhook_url"]

# gspread service-account credentials as a dict:
gspread_creds = st.secrets["gspread"]

# CONFIGURATION
MIN_MARGIN = 500
MIN_VOLUME = 500
MIN_UTILITY = 10000
EXCLUDED_ITEMS = ["Zulrah's scales", "Rune arrow", "Coal"]
HEADERS = {
    'User-Agent': 'OSRS_Flip_Assistant/1.0 - Real-time GE flipping tool - melon4free on Discord'
}

# Category definitions (simple keyword mapping)
CATEGORY_KEYWORDS = {
    'Raw Materials': ['ore', 'log', 'fish', 'bar', 'gem'],
    'Consumables': ['potion', 'food', 'scroll', 'seed'],
    'Runes & Ammo': ['rune', 'arrow', 'bolt'],
    'Gear & Weapons': ['sword', 'shield', 'helm', 'plate', 'bow', 'staff'],
}

# Google Sheets Integration
SHEET_NAME = 'OSRS Flipping Profits'
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Globals
show_all = False
LAST_ALERTS = {}  # track last alert times per item

# GE tax calculation
def calculate_ge_tax(price):
    tax = math.floor(price * 0.02)
    return min(tax, 5_000_000)

# Fetch mappings & prices with enhanced error handling
def get_item_mapping():
    """
    Fetch OSRS item ID-name mapping from RuneScape Wiki API.
    """
    print("🔍 Fetching item mapping...")
    
    # Use the correct mapping endpoint
    url = "https://prices.runescape.wiki/api/v1/osrs/mapping"
    try:
        print(f"Trying RuneScape Wiki mapping API: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        
        # The mapping API returns a list directly
        mapping_list = r.json()
        print(f"✅ Wiki mapping API success: {len(mapping_list)} items")
        
    except Exception as e:
        print(f"❌ Mapping API failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response text: {e.response.text}")
        return {}, {}
    
    # Process mapping
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
            
            # Store the timestamp from the API response
            timestamp = data.get('timestamp', datetime.datetime.now(datetime.timezone.utc).timestamp())
            
            # Add timestamp to the data structure
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
    # For backward compatibility, return just the data if called without expecting timestamp
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
        # Determine timestep based on days requested
        if days <= 1:
            timestep = "5m"
        elif days <= 7:
            timestep = "1h"
        else:
            timestep = "6h"
            
        # The timeseries API only needs id and timestep according to the docs
        url = f"https://prices.runescape.wiki/api/v1/osrs/timeseries?id={item_id}&timestep={timestep}"
        
        print(f"📊 Fetching timeseries: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        if r.status_code != 200:
            print(f"❌ Timeseries API returned status {r.status_code}: {r.text}")
            return None
            
        response_data = r.json()
        print(f"📊 Timeseries response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
        
        # The response should contain 'data' key with the timeseries
        if 'data' not in response_data:
            print(f"❌ No 'data' key in timeseries response: {response_data}")
            return None
            
        data = response_data['data']
        if not data:
            print(f"❌ Empty data array in timeseries response")
            return pd.DataFrame()
            
        print(f"✅ Got {len(data)} timeseries data points")
        
        df = pd.DataFrame(data)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Calculate average price and volume
        df['avg_price'] = (df['avgLowPrice'] + df['avgHighPrice']) / 2
        df['volume'] = df['lowPriceVolume'] + df['highPriceVolume']
        
        # Rename columns for consistency
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
        
        # Handle different possible field names
        if 'avgHighPrice' in df.columns:
            df['high'] = df['avgHighPrice']
            df['low'] = df['avgLowPrice']
            df['volume'] = df['lowPriceVolume'] + df['highPriceVolume']
        elif 'high' in df.columns:
            # Data already in correct format
            df['volume'] = df.get('lowVolume', 0) + df.get('highVolume', 0)
        else:
            print(f"❌ Unexpected column names: {df.columns.tolist()}")
            return None
        
        return df.sort_values('timestamp')
        
    except Exception as e:
        print(f"❌ Error fetching custom timeseries: {e}")
        return None

# Buy limits with fallback defaults
def get_buy_limits():
    """Load GE buy limits from file, with intelligent defaults if file missing"""
    try:
        with open('ge_limits.json', 'r') as f:
            limits = json.load(f)
            print(f"✅ Loaded {len(limits)} buy limits from file")
            return limits
    except FileNotFoundError:
        print("⚠️ ge_limits.json not found, using default buy limits")
        # Default buy limits for common items
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

# Categorize
def categorize_item(name):
    lname = name.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in lname for kw in kws):
            return cat
    return 'Other'

# FIXED: Main filter with momentum, category, seasonality
def filter_items(price_data_result, hourly_data, id2name, show_all=False, mode="Custom"):
    """Filter and analyze items with enhanced debugging - FIXED VERSION"""
    
    # Handle new data structure with timestamp
    if isinstance(price_data_result, dict) and 'data' in price_data_result:
        price_data = price_data_result['data']
        data_timestamp = price_data_result.get('timestamp', datetime.datetime.now(datetime.timezone.utc).timestamp())
    else:
        price_data = price_data_result
        data_timestamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
    
    print(f"🔄 Filtering items. Price data: {len(price_data)}, Hourly data: {len(hourly_data)}, Mappings: {len(id2name)}")
    
    if not price_data:
        print("❌ No price data available")
        return pd.DataFrame()
    
    if not id2name:
        print("❌ No item mappings available")
        return pd.DataFrame()
    
    limits = get_buy_limits()
    recs = []
    processed = 0
    valid_items = 0
    total_items = len(price_data)
    
    # Use timezone-aware UTC hour
    current_hour = datetime.datetime.now(datetime.timezone.utc).hour
    current_time = datetime.datetime.now(datetime.timezone.utc).timestamp()
    
    # FIXED: Convert items() to list to avoid iteration issues
    price_items = list(price_data.items())
    
    for iid, stats in price_items:
        processed += 1
        
        # Progress logging every 1000 items
        if processed % 1000 == 0:
            print(f"Processed {processed}/{total_items} items...")
        
        try:
            name = id2name.get(iid, f"Unknown_{iid}")
            
            # Skip excluded items
            if any(exc.lower() in name.lower() for exc in EXCLUDED_ITEMS):
                continue
                
            # Get basic price data
            hi = stats.get('high')
            lo = stats.get('low')
            
            if not hi or not lo or hi <= lo:
                continue
                
            valid_items += 1
            
            # Get hourly data
            hourly = hourly_data.get(iid, {})
            vol1h = hourly.get('lowPriceVolume', 0) + hourly.get('highPriceVolume', 0)
            avg_lo = hourly.get('avgLowPrice')
            
            # Calculate metrics
            tax = calculate_ge_tax(hi)
            net = hi - lo - tax
            
            # Avoid division by zero
            if vol1h == 0:
                util = 0
            else:
                util = round((net * vol1h) / (abs(hi - (avg_lo if avg_lo else 0)) + 1), 2)
            
            # momentum - handle division by zero
            if avg_lo and avg_lo > 0:
                momentum = round((lo - avg_lo) / avg_lo * 100, 2)
            else:
                momentum = 0
            
            # seasonality: avg volume for this hour over past 7d
            # Note: This is expensive, so we'll skip it for now to avoid hanging
            season_ratio = 1.0  # Default value
            
            cat = categorize_item(name)
            gl = limits.get(name, 1000)  # Default to 1000 if not found
            roi = round(net / lo * 100, 2) if lo else 0
            
            # Calculate actual data age in seconds
            item_timestamp = stats.get('highTime', data_timestamp)
            data_age_seconds = current_time - item_timestamp
            data_age_minutes = round(data_age_seconds / 60, 1)
            
            # Get individual timestamps for high and low prices
            high_time = stats.get('highTime', data_timestamp)
            low_time = stats.get('lowTime', data_timestamp)
            high_age_minutes = round((current_time - high_time) / 60, 1)
            low_age_minutes = round((current_time - low_time) / 60, 1)
            
            recs.append({
                'Item': name,
                'Buy Price': lo,
                'Sell Price': hi,
                'Net Margin': net,
                'ROI (%)': roi,
                '1h Volume': vol1h,
                'Momentum (%)': momentum,
                'Season Ratio': season_ratio,
                'Utility': util,
                'Category': cat,
                'Item ID': iid,
                'Data Age (min)': data_age_minutes,
                'High Age (min)': high_age_minutes,
                'Low Age (min)': low_age_minutes
            })
            
        except Exception as e:
            print(f"❌ Error processing item {iid}: {e}")
            continue
    
    print(f"✅ Processed {processed} items, found {valid_items} valid items, created {len(recs)} recommendations")
    
    if not recs:
        print("❌ No recommendations generated")
        return pd.DataFrame()
    
    df = pd.DataFrame(recs)
    
    # High Volume mode special handling
    if mode == "High Volume":
        print("🔥 High Volume Mode: Showing 250 highest traded items")
        # Sort by volume first, then by profit
        df = df.sort_values(['1h Volume', 'Net Margin'], ascending=[False, False])
        return df.head(250)  # Return top 250 by volume
    
    # If "Show All" is enabled, bypass core filtering
    if show_all:
        print("📋 Showing all items (no filtering)")
        return df.sort_values('Utility', ascending=False)
    
    # Apply core filters
    season_th = st.session_state.get('season_th', 0) if 'st' in globals() else 0
    before_filter = len(df)
    
    df = df[(df['Net Margin'] >= MIN_MARGIN) &
            (df['1h Volume'] >= MIN_VOLUME) &
            (df['Utility'] >= MIN_UTILITY) &
            (df['Season Ratio'] >= season_th)]
    
    after_filter = len(df)
    print(f"🔍 Applied filters: {before_filter} -> {after_filter} items")
    print(f"   Min Margin: {MIN_MARGIN}, Min Volume: {MIN_VOLUME}, Min Utility: {MIN_UTILITY}, Season Th: {season_th}")
    
    return df.sort_values('Utility', ascending=False)

# Alerts with rate-limit (3 minutes minimum between alerts)
def send_discord_alert(item, buy, sell, margin):
    # Use timezone-aware UTC
    now = datetime.datetime.now(datetime.timezone.utc)
    last = LAST_ALERTS.get(item)
    
    # 3 minute cooldown (180 seconds)
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

# Backtest filters
def backtest_filters(id2name, days=1):
    sigs = []
    for iid, name in list(id2name.items())[:10]:  # Limit for testing
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

# Correlations
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

# Google Sheets
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

# Scanner
def run_flip_scanner(mode="Custom"):
    """Main scanner function with comprehensive error handling - FIXED VERSION"""
    global show_all
    
    try:
        # Step 1: Get item mappings
        print("=" * 50)
        print("🚀 Starting OSRS Flip Scanner")
        print("=" * 50)
        
        id2name, name2id = get_item_mapping()
        if not id2name or not name2id:
            if 'st' in globals():
                st.error("❌ Failed to load item mappings. Cannot proceed.")
            return pd.DataFrame(), {}
        
        # Step 2: Get price data
        pd_data = get_real_time_prices()
        if not pd_data:
            if 'st' in globals():
                st.error("❌ Failed to load price data. Cannot proceed.")
            return pd.DataFrame(), name2id
        
        # Step 3: Get hourly data (optional)
        h_data = get_hourly_prices()
        
        # Step 4: Filter items with mode parameter
        df = filter_items(pd_data, h_data, id2name, show_all, mode)
        
        if df.empty:
            if 'st' in globals():
                st.warning("⚠️ No items match your filter criteria. Try adjusting the filters or enable 'Show All'.")
            return df, name2id
        
        # Step 5: Limit results if not showing all
        if not show_all:
            df = df.head(50)
        
        # Step 6: Send alerts for high-margin items (with strict conditions)
        alert_count = 0
        
        # Only send alerts if we have a reasonable number of results (not showing all items)
        should_send_alerts = (
            not show_all and  # Don't send alerts when "Show All" is enabled
            len(df) <= 5 and  # Only send if 5 or fewer opportunities
            len(df) > 0       # And we have at least one opportunity
        )
        
        if should_send_alerts:
            # Only alert on truly exceptional opportunities (2x minimum margin)
            high_value_items = df[df['Net Margin'] > MIN_MARGIN * 2]
            
            for _, r in high_value_items.iterrows():
                # Send alert and check if it was actually sent (not on cooldown)
                alert_sent = send_discord_alert(r['Item'], r['Buy Price'], r['Sell Price'], r['Net Margin'])
                if alert_sent:
                    alert_count += 1
                    
                # Limit to max 3 alerts per refresh to prevent spam
                if alert_count >= 3:
                    break
        
        if alert_count > 0:
            print(f"📢 Sent {alert_count} Discord alerts")
        elif should_send_alerts and len(df[df['Net Margin'] > MIN_MARGIN * 2]) > 0:
            print(f"⏳ Discord alerts skipped - items on cooldown")
        elif not should_send_alerts:
            print(f"🚫 Discord alerts disabled - showing {len(df)} items (max 5 for alerts)")
        else:
            print(f"📊 No exceptional opportunities for Discord alerts")
        
        # Step 7: Export data
        try:
            df.to_csv("flipping_report.csv", index=False)
            print("✅ Saved CSV report")
        except Exception as e:
            print(f"❌ CSV export failed: {e}")
        
        try:
            export_to_sheets(df)
            print("✅ Exported to Google Sheets")
        except Exception as e:
            print(f"❌ Sheets export failed: {e}")
        
        print(f"✅ Scanner completed successfully. Found {len(df)} opportunities.")
        return df, name2id
        
    except Exception as e:
        error_msg = f"❌ Scanner failed with error: {e}\n{traceback.format_exc()}"
        print(error_msg)
        if 'st' in globals():
            st.error(error_msg)
        return pd.DataFrame(), {}

def create_enhanced_chart(ts, item_name, chart_type, height, width,
                          color_high, color_low, color_volume,
                          line_width, show_grid, show_volume, volume_opacity):
    # 1) Dark theme
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

    # 2) Price lines with markers
    ax1.plot(ts['timestamp'], ts['high'], marker='o', markersize=4,
             label='Sell', color=color_high, linewidth=line_width)
    ax1.plot(ts['timestamp'], ts['low'],  marker='o', markersize=4,
             label='Buy',  color=color_low,  linewidth=line_width)

    # 3) Rolling-average trend
    ts['mid'] = (ts['high'] + ts['low'])/2
    trend = ts['mid'].rolling(window=10, min_periods=1).mean()
    ax1.plot(ts['timestamp'], trend, linestyle='--', linewidth=1,
             color='#bdc3c7', alpha=0.7, label='Trend')

    # 4) Volume bars
    if show_volume:
        ax2.bar(
            ts['timestamp'],
            ts['volume'],
            alpha=volume_opacity,
            color=color_volume,
            width=0.02,
            label='Volume'
        )

    # 5) Styling
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

    # 6) Date formatting
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    fig.autofmt_xdate()

    # 7) Title & layout
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

    # top: price
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
    # optional trend line
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

    # bottom: volume
    fig.add_trace(
        go.Bar(
            x=ts['timestamp'], y=ts['volume'],
            name='Volume',
            marker=dict(opacity=0.6),
            hovertemplate='Vol: %{y}<br>%{x|%b %d %H:%M}<extra></extra>'
        ), row=2, col=1
    )

    # dark styling
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

# Streamlit UI
def streamlit_dashboard():
    global MIN_MARGIN, MIN_VOLUME, MIN_UTILITY, show_all
    
    st.set_page_config(page_title="OSRS Flip Assistant", layout="wide")
    
    # Initialize session state
    if 'presets' not in st.session_state:
        st.session_state.presets = {}
    if 'season_th' not in st.session_state:
        st.session_state.season_th = 0.0
    
    st.title("💸 OSRS GE Flipping Assistant")
    
    # Debug info
    with st.expander("🔧 Debug Information"):
        st.write("**Current Configuration:**")
        st.write(f"- Min Margin: {MIN_MARGIN:,} gp")
        st.write(f"- Min Volume: {MIN_VOLUME:,}/hr")
        st.write(f"- Min Utility: {MIN_UTILITY:,}")
        st.write(f"- Show All: {show_all}")
        st.write(f"- Season Threshold: {st.session_state.get('season_th', 0)}")
        
        if st.button("🧪 Test API Connections"):
            st.write("Testing item mapping API...")
            id2name, name2id = get_item_mapping()
            st.write(f"✅ Loaded {len(id2name)} item mappings")
            
            st.write("Testing price data API...")
            prices = get_real_time_prices()
            st.write(f"✅ Loaded prices for {len(prices)} items")
            
            st.write("Testing hourly data API...")
            hourly = get_hourly_prices()
            st.write(f"✅ Loaded hourly data for {len(hourly)} items")
        
        if st.button("📁 Create Missing Files"):
            # Create ge_limits.json if it doesn't exist
            if not os.path.exists('ge_limits.json'):
                default_limits = get_buy_limits()  # This will return defaults
                try:
                    with open('ge_limits.json', 'w') as f:
                        json.dump(default_limits, f, indent=2)
                    st.success("✅ Created ge_limits.json with default buy limits")
                except Exception as e:
                    st.error(f"❌ Failed to create ge_limits.json: {e}")
            else:
                st.info("ge_limits.json already exists")
    
    # Preset load/save
    ps = st.sidebar.selectbox("Load Preset", [''] + list(st.session_state.presets.keys()))
    if ps:
        m, v, u, season = st.session_state.presets[ps]
        MIN_MARGIN, MIN_VOLUME, MIN_UTILITY = m, v, u
        st.session_state['season_th'] = season
    
    name_in = st.sidebar.text_input("Preset Name")
    if st.sidebar.button("Save Preset") and name_in:
        st.session_state.presets[name_in] = (MIN_MARGIN, MIN_VOLUME, MIN_UTILITY, st.session_state.get('season_th', 0))
        st.sidebar.success(f"Saved preset: {name_in}")
    
    st.sidebar.markdown("---")
    
    # Mode selection with new High Volume mode
    mode = st.sidebar.selectbox("Mode", ["Custom", "Low-Risk", "High-ROI", "Passive Overnight", "High Volume"])
    if mode == "Low-Risk":
        m, v, u = 200, 1000, 2000
    elif mode == "High-ROI":
        m, v, u = 1000, 500, 5000
    elif mode == "Passive Overnight":
        m, v, u = 300, 200, 1000
    elif mode == "High Volume":
        # High Volume mode: focus on liquid markets with good profit
        m, v, u = 100, 1000, 1000  # Lower barriers for high volume items
        st.sidebar.info("🔥 High Volume Mode: Shows 250 highest traded items sorted by profit")
    else:
        m, v, u = MIN_MARGIN, MIN_VOLUME, MIN_UTILITY
    
    # Filter controls
    MIN_MARGIN = st.sidebar.slider("Min Net Margin", 0, 5000, m, 50)
    MIN_VOLUME = st.sidebar.slider("Min Volume/hr", 0, 20000, v, 100)
    MIN_UTILITY = st.sidebar.slider("Min Utility", 0, 50000, u, 500)
    st.session_state['season_th'] = st.sidebar.slider("Min Season Ratio", 0.0, 5.0, st.session_state.get('season_th', 0.0), 0.1)
    show_all = st.sidebar.checkbox("Show All", value=False)
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)")
    if auto_refresh:
        st.sidebar.write("⏰ Auto-refreshing...")
        import time
        time.sleep(30)
        st.rerun()  # Fixed deprecated method
    
    # Main scan button
    if st.button("🔄 Refresh Data", type="primary"):
        with st.spinner("Scanning for flip opportunities..."):
            df, name2id = run_flip_scanner(mode)
            # Store price data for trend viewer
            if 'price_data' not in st.session_state:
                st.session_state.price_data = get_real_time_prices()
    else:
        # Run initial scan
        with st.spinner("Loading flip opportunities..."):
            df, name2id = run_flip_scanner(mode)
            # Store price data for trend viewer
            if 'price_data' not in st.session_state:
                st.session_state.price_data = get_real_time_prices()
    
    # Get price data for trend viewer
    price_data = st.session_state.get('price_data', {})
    
    # Display results with color coding
    if not df.empty:
        st.subheader("🔍 Top Flip Opportunities")
        
        # Add color coding explanation
        with st.expander("🎨 Color Coding Guide"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown("🟢 **Green** - Fresh data (<2m) with high ROI & Volume")
            with col2:
                st.markdown("🟡 **Yellow** - Aging data (2-5m) or moderate ROI")
            with col3:
                st.markdown("🔴 **Red** - Old data (>5m) or low ROI")
            with col4:
                st.markdown("⏱️ **Age** - Shows when price was last traded")
        
        # Create enhanced dataframe with better formatting and color coding
        display_df = df.copy()
        
        # Add color coding based on ROI and data age
        def get_color_code(roi, data_age, volume):
            if data_age > 5:  # Data older than 5 minutes
                return "🔴"  # Red for old data
            elif data_age > 2:  # Data older than 2 minutes
                return "🟡"  # Yellow for aging data
            elif roi >= 5 and volume >= 1000:  # High ROI and volume
                return "🟢"  # Green for excellent
            elif roi >= 2 and volume >= 500:   # Moderate ROI and volume
                return "🟡"  # Yellow for good
            else:
                return "🔴"  # Red for caution
        
        # Apply color coding
        display_df['Status'] = display_df.apply(
            lambda row: get_color_code(row['ROI (%)'], row['Data Age (min)'], row['1h Volume']), 
            axis=1
        )
        
        # Add additional calculated columns
        display_df['Current Price'] = display_df['Buy Price'].apply(lambda x: f"{x:,}")
        display_df['Approx. Offer Price'] = display_df.apply(
            lambda row: f"{row['Buy Price']:,} ({row['Low Age (min)']:.1f}m ago)", 
            axis=1)
        display_df['Approx. Sell Price'] = display_df.apply(
            lambda row: f"{row['Sell Price']:,} ({row['High Age (min)']:.1f}m ago)", 
            axis=1)
        display_df['Tax'] = display_df['Sell Price'].apply(lambda x: f"{calculate_ge_tax(x):,}")
        display_df['Approx. Profit (gp)'] = display_df['Net Margin'].apply(lambda x: f"{x:,}")
        display_df['ROI%'] = display_df['ROI (%)'].apply(lambda x: f"{x:.1f}%")
        display_df['Buying Quantity (per hour)'] = display_df['1h Volume'].apply(lambda x: f"{x:,}")
        display_df['Selling Quantity (per hour)'] = display_df['1h Volume'].apply(lambda x: f"{x:,}")
        
        # Get buy limits for display
        limits = get_buy_limits()
        display_df['GE Limit'] = display_df['Item'].apply(lambda x: f"{limits.get(x, 'N/A'):,}" if limits.get(x) else "N/A")
        
        # Calculate buy/sell ratio (spread as percentage of buy price)
        display_df['Buy/Sell Ratio'] = display_df.apply(
            lambda row: f"{((row['Sell Price'] - row['Buy Price']) / row['Buy Price'] * 100):+.2f}%", 
            axis=1
        )
        
        # Select and reorder columns to match GE Tracker layout with color coding
        columns_to_display = [
            'Status',
            'Item',
            'Current Price',
            'Approx. Offer Price', 
            'Approx. Sell Price',
            'Tax',
            'Approx. Profit (gp)',
            'ROI%',
            'Buying Quantity (per hour)',
            'Selling Quantity (per hour)',
            'Buy/Sell Ratio',
            'GE Limit'
        ]
        
        # Create the display dataframe
        final_display_df = display_df[columns_to_display].copy()
        
        # Apply custom CSS for color coding
        st.markdown("""
        <style>
        .stDataFrame {
            font-size: 12px;
        }
        .green-row {
            background-color: rgba(76, 175, 80, 0.1);
        }
        .yellow-row {
            background-color: rgba(255, 235, 59, 0.1);
        }
        .red-row {
            background-color: rgba(244, 67, 54, 0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display with enhanced styling
        st.dataframe(
            final_display_df, 
            use_container_width=True, 
            key="color_coded_flip_table",
            height=600,
            hide_index=True
        )
        
        # Mode-specific information
        if mode == "High Volume":
            st.info(f"🔥 **High Volume Mode**: Showing top {len(df)} highest traded items sorted by volume and profit")
        
        # Add summary statistics bar
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_items = len(df)
            st.metric("Total Items", total_items)
        
        with col2:
            avg_margin = df['Net Margin'].mean()
            st.metric("Avg Margin", f"{avg_margin:,.0f} gp")
        
        with col3:
            max_margin = df['Net Margin'].max()
            st.metric("Max Margin", f"{max_margin:,.0f} gp")
        
        with col4:
            avg_roi = df['ROI (%)'].mean()
            st.metric("Avg ROI", f"{avg_roi:.1f}%")
        
        with col5:
            total_volume = df['1h Volume'].sum()
            st.metric("Total Volume/hr", f"{total_volume:,.0f}")
        
        # Add filtering controls similar to GE Tracker
        with st.expander("🔧 Advanced Filters"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                category_filter = st.multiselect(
                    "Filter by Category", 
                    options=df['Category'].unique(),
                    default=df['Category'].unique()
                )
            
            with col2:
                min_roi_filter = st.slider("Min ROI %", 0.0, 20.0, 0.0, 0.1)
                max_roi_filter = st.slider("Max ROI %", 0.0, 50.0, 50.0, 0.1)
            
            with col3:
                min_volume_filter = st.slider("Min Volume/hr", 0, 10000, 0, 100)
                max_volume_filter = st.slider("Max Volume/hr", 0, 50000, 50000, 100)
            
            # Apply advanced filters
            if category_filter:
                filtered_df = df[
                    (df['Category'].isin(category_filter)) &
                    (df['ROI (%)'] >= min_roi_filter) &
                    (df['ROI (%)'] <= max_roi_filter) &
                    (df['1h Volume'] >= min_volume_filter) &
                    (df['1h Volume'] <= max_volume_filter)
                ]
                
                if not filtered_df.empty and not filtered_df.equals(df):
                    st.write(f"**Filtered Results:** {len(filtered_df)} items")
                    
                    # Update display with filtered data
                    filtered_display_df = filtered_df.copy()
                    filtered_display_df['Approx. Offer Price'] = filtered_display_df['Buy Price'].apply(lambda x: f"{x:,}")
                    filtered_display_df['Approx. Sell Price'] = filtered_display_df['Sell Price'].apply(lambda x: f"{x:,}")
                    filtered_display_df['Tax'] = filtered_display_df['Sell Price'].apply(lambda x: f"{calculate_ge_tax(x):,}")
                    filtered_display_df['Approx. Profit (gp)'] = filtered_display_df['Net Margin'].apply(lambda x: f"{x:,}")
                    filtered_display_df['ROI%'] = filtered_display_df['ROI (%)'].apply(lambda x: f"{x:.1f}%")
                    filtered_display_df['Buying Quantity (per hour)'] = filtered_display_df['1h Volume'].apply(lambda x: f"{x:,}")
                    filtered_display_df['Selling Quantity (per hour)'] = filtered_display_df['1h Volume'].apply(lambda x: f"{x:,}")
                    filtered_display_df['GE Limit'] = filtered_display_df['Item'].apply(lambda x: f"{limits.get(x, 'N/A'):,}" if limits.get(x) else "N/A")
                    filtered_display_df['Buy/Sell Ratio'] = filtered_display_df.apply(
                        lambda row: f"{((row['Sell Price'] - row['Buy Price']) / row['Buy Price'] * 100):+.2f}%", 
                        axis=1
                    )
                    
                    #Only keep the columns that actually exist
                    available = [c for c in columns_to_display if c in filtered_display_df.columns]
                    missing   = [c for c in columns_to_display if c not in filtered_display_df.columns]

                    if missing:
                        st.warning(f"The following columns are missing and will be hidden: {missing}")

                    if not available:
                        st.error("No columns to display—please check your filters or data source.")
                        return  # or st.stop() to halt execution here

                    final_filtered_df = filtered_display_df[available].copy()
                    st.dataframe(
                        final_filtered_df,
                        use_container_width=True,
                        key="filtered_flip_table",
                        height=400,
                        hide_index=True
                    )
                    
                    st.write("Columns we have right now:", list(filtered_display_df.columns))
        
        # Create a container for the main data table that won't refresh when charts update
        table_container = st.container()
        
        # Download button with enhanced CSV export
        enhanced_csv = df.copy()
        enhanced_csv['Tax'] = enhanced_csv['Sell Price'].apply(calculate_ge_tax)
        enhanced_csv['GE_Limit'] = enhanced_csv['Item'].apply(lambda x: limits.get(x, 'N/A'))
        enhanced_csv['Buy_Sell_Ratio'] = ((enhanced_csv['Sell Price'] - enhanced_csv['Buy Price']) / enhanced_csv['Buy Price'] * 100).round(2)
        
        csv_data = enhanced_csv.to_csv(index=False)
        st.download_button(
            label="📥 Download Enhanced CSV",
            data=csv_data,
            file_name=f"osrs_flips_enhanced_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
        # Category summary
        st.subheader("📂 Category Summary")
        if 'Category' in df.columns:
            cat_summary = df.groupby('Category').agg({
                'Utility': ['count', 'mean'],
                'Net Margin': 'mean',
                'ROI (%)': 'mean'
            }).round(2)
            cat_summary.columns = ['Signals', 'Avg Utility', 'Avg Margin', 'Avg ROI%']
            st.dataframe(cat_summary, key="category_summary_table")
        
        # Price correlations section with detailed explanation
        if len(name2id) > 0:
            st.subheader("🔗 Price Correlations Analysis")
            
            # Add explanation
            with st.expander("ℹ️ What are Price Correlations?"):
                st.write("""
                **Price Correlations** measure how similarly two items' prices move together over time:
                
                📊 **Correlation Values:**
                - **+1.0** = Perfect positive correlation (prices always move together)
                - **0.0** = No correlation (prices move independently)  
                - **-1.0** = Perfect negative correlation (prices move opposite)
                
                💡 **Trading Applications:**
                - **High Positive Correlation (0.7-1.0):** Items that rise/fall together - good for diversified flipping
                - **Negative Correlation (-0.7 to -1.0):** Items that move opposite - potential hedging opportunities
                - **Low Correlation (0.0-0.3):** Independent items - good for portfolio diversification
                
                🎯 **Correlation Threshold:** Only shows correlations above your selected minimum strength
                """)
            
            ct = st.sidebar.slider("Correlation Threshold", 0.0, 1.0, 0.8, 0.05, 
                                   help="Only show correlations above this strength (0.8 = 80% correlation)")
            
            if st.button("🔍 Compute Correlations"):
                with st.spinner("Computing price correlations..."):
                    corrs = compute_price_correlations(name2id, 10, 1)
                    if not corrs.empty:
                        pairs = [(i, j, round(corrs.loc[i, j], 2)) 
                                for i in corrs for j in corrs 
                                if i < j and corrs.loc[i, j] >= ct]
                        if pairs:
                            corr_df = pd.DataFrame(pairs, columns=['Item A', 'Item B', 'Correlation'])
                            corr_df['Correlation Strength'] = corr_df['Correlation'].apply(
                                lambda x: "🔥 Very Strong" if x >= 0.9 else
                                         "💪 Strong" if x >= 0.7 else
                                         "📈 Moderate" if x >= 0.5 else
                                         "📊 Weak"
                            )
                            st.dataframe(corr_df, key="correlation_table")
                            
                            # Show correlation insights
                            st.info(f"🔍 Found {len(pairs)} item pairs with correlation ≥ {ct}")
                            if len(pairs) > 0:
                                strongest = corr_df.iloc[0]
                                st.success(f"🏆 Strongest correlation: **{strongest['Item A']}** ↔ **{strongest['Item B']}** ({strongest['Correlation']})")
                        else:
                            st.warning(f"No correlations above {ct} found. Try lowering the threshold.")
                    else:
                        st.error("Unable to compute correlations - insufficient data.")
        
        # Backtest
        st.subheader("📈 Backtest Filters")
        days = st.slider("Days to Backtest", 1, 7, 1)
        if st.button("Run Backtest"):
            with st.spinner("Running backtest..."):
                res = backtest_filters(name2id, days)
                if not res.empty:
                    st.dataframe(res)
                else:
                    st.write("No backtest signals found.")
        
        # Enhanced Trend viewer
        st.subheader("📊 Advanced Trend Viewer")
        
        # Search and selection
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("🔍 Search item:", placeholder="Type item name...").lower()
        with col2:
            chart_type = st.selectbox("📈 Chart Type", ["Line Chart", "Candlestick", "Area Chart", "Volume Bars"])
        
        filtered = df[df['Item'].str.lower().str.contains(search, regex=False)] if search else df
        
        if not filtered.empty:
            # Item selection and timeframe
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                sel = st.selectbox("Select item", filtered['Item'])
            with col2:
                timestep = st.selectbox("Time Step", ["5m", "1h", "6h", "24h"], index=1)
            with col3:
                show_volume = st.checkbox("Show Volume", value=True)
            
            # Chart customization options
            with st.expander("🎨 Chart Customization"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    chart_height = st.slider("Chart Height", 400, 800, 600)
                    price_color_high = st.color_picker("High Price Color", "#e74c3c")
                with col2:
                    chart_width = st.slider("Chart Width", 800, 1400, 1200)
                    price_color_low = st.color_picker("Low Price Color", "#27ae60")
                with col3:
                    line_width = st.slider("Line Width", 1, 5, 2)
                    volume_color = st.color_picker("Volume Color", "#3498db")
                with col4:
                    show_grid = st.checkbox("Show Grid", value=True)
                    volume_opacity = st.slider("Volume Opacity", 0.1, 1.0, 0.3)
            
            if sel:
                tid = name2id.get(sel)
                if tid:
                    # Create a separate container for chart updates to prevent table refresh
                    chart_container = st.container()
                    
                    with chart_container:
                        with st.spinner(f"Loading trend data for {sel}..."):
                            # Get timeseries data with custom timestep
                            ts = get_timeseries_custom(tid, timestep)
                            
                            if ts is not None and not ts.empty:
                                st.success(f"✅ Found {len(ts)} data points for {sel}")
                                
                                # Data filtering options
                                with st.expander("🔧 Data Filters"):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        min_price = st.number_input("Min Price Filter", min_value=0, value=0, key=f"min_price_{sel}")
                                    with col2:
                                        max_price = st.number_input("Max Price Filter", min_value=0, value=int(ts['high'].max()) if not ts.empty else 0, key=f"max_price_{sel}")
                                    with col3:
                                        min_volume = st.number_input("Min Volume Filter", min_value=0, value=0, key=f"min_volume_{sel}")
                                
                                # Apply filters
                                if min_price > 0 or max_price > 0 or min_volume > 0:
                                    filtered_ts = ts.copy()
                                    if min_price > 0:
                                        filtered_ts = filtered_ts[filtered_ts['low'] >= min_price]
                                    if max_price > 0:
                                        filtered_ts = filtered_ts[filtered_ts['high'] <= max_price]
                                    if min_volume > 0:
                                        filtered_ts = filtered_ts[filtered_ts['volume'] >= min_volume]
                                    ts = filtered_ts
                                
                                create_interactive_chart(
                                    ts,
                                    item_name=sel,
                                    width=chart_width,
                                    height=chart_height
                                )
                                
                                # Create enhanced chart - this won't trigger table refresh
                                #create_enhanced_chart(ts, sel, chart_type, chart_height, chart_width, 
                                #                    price_color_high, price_color_low, volume_color,
                                #                    line_width, show_grid, show_volume, volume_opacity)
                                
                                # Data analysis section
                                st.subheader("📈 Price Analysis")
                                
                                # Summary statistics in columns
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric(
                                        "Current Price Range", 
                                        f"{ts['low'].iloc[-1]:,.0f} - {ts['high'].iloc[-1]:,.0f} gp",
                                        f"{((ts['high'].iloc[-1] - ts['low'].iloc[-1]) / ts['low'].iloc[-1] * 100):+.1f}% spread"
                                    )
                                with col2:
                                    price_change = ts['high'].iloc[-1] - ts['high'].iloc[0]
                                    st.metric(
                                        "Price Change", 
                                        f"{price_change:+,.0f} gp",
                                        f"{(price_change / ts['high'].iloc[0] * 100):+.2f}%"
                                    )
                                with col3:
                                    avg_volume = ts['volume'].mean()
                                    st.metric(
                                        "Avg Volume", 
                                        f"{avg_volume:,.0f}",
                                        f"Total: {ts['volume'].sum():,.0f}"
                                    )
                                with col4:
                                    volatility = ts['high'].std() / ts['high'].mean() * 100
                                    st.metric(
                                        "Volatility", 
                                        f"{volatility:.1f}%",
                                        "Price stability"
                                    )
                                
                                # Price distribution
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.subheader("📊 Price Distribution")
                                    fig_hist = plt.figure(figsize=(8, 5))
                                    plt.hist(ts['high'], bins=20, alpha=0.7, color=price_color_high, label='High Prices')
                                    plt.hist(ts['low'], bins=20, alpha=0.7, color=price_color_low, label='Low Prices')
                                    plt.xlabel('Price (gp)')
                                    plt.ylabel('Frequency')
                                    plt.title(f'{sel} - Price Distribution')
                                    plt.legend()
                                    plt.grid(True, alpha=0.3)
                                    st.pyplot(fig_hist)
                                
                                with col2:
                                    st.subheader("📈 Moving Averages")
                                    if len(ts) >= 5:
                                        # Calculate moving averages
                                        ts['ma_5'] = ts['high'].rolling(window=5).mean()
                                        ts['ma_10'] = ts['high'].rolling(window=min(10, len(ts))).mean()
                                        
                                        fig_ma = plt.figure(figsize=(8, 5))
                                        plt.plot(ts['timestamp'], ts['high'], label='High Price', alpha=0.7, color=price_color_high)
                                        plt.plot(ts['timestamp'], ts['ma_5'], label='MA 5', linewidth=2, color='orange')
                                        if len(ts) >= 10:
                                            plt.plot(ts['timestamp'], ts['ma_10'], label='MA 10', linewidth=2, color='purple')
                                        plt.xlabel('Time')
                                        plt.ylabel('Price (gp)')
                                        plt.title(f'{sel} - Moving Averages')
                                        plt.legend()
                                        plt.grid(True, alpha=0.3)
                                        plt.xticks(rotation=45)
                                        plt.tight_layout()
                                        st.pyplot(fig_ma)
                                    else:
                                        st.info("Need at least 5 data points for moving averages")
                                
                                # Trading opportunities
                                st.subheader("💡 Trading Insights")
                                
                                # Calculate potential profit
                                current_spread = ts['high'].iloc[-1] - ts['low'].iloc[-1]
                                tax = calculate_ge_tax(ts['high'].iloc[-1])
                                net_profit = current_spread - tax
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.info(f"**Current Spread:** {current_spread:,.0f} gp")
                                    st.info(f"**GE Tax:** {tax:,.0f} gp")
                                    st.info(f"**Net Profit:** {net_profit:,.0f} gp")
                                
                                with col2:
                                    # Price trend analysis
                                    if len(ts) >= 6:
                                        recent_trend = "📈 Rising" if ts['high'].iloc[-1] > ts['high'].iloc[-5] else "📉 Falling"
                                    else:
                                        recent_trend = "📊 Insufficient data"
                                    st.info(f"**Recent Trend:** {recent_trend}")
                                    
                                    # Volume trend
                                    vol_trend = "📈 Increasing" if ts['volume'].iloc[-1] > ts['volume'].mean() else "📉 Decreasing"
                                    st.info(f"**Volume Trend:** {vol_trend}")
                                
                                with col3:
                                    # Best time to trade (based on volume)
                                    if len(ts) > 1:
                                        best_hour = ts.groupby(ts['timestamp'].dt.hour)['volume'].mean().idxmax()
                                        st.info(f"**Peak Volume Hour:** {best_hour}:00")
                                    else:
                                        st.info("**Peak Volume Hour:** N/A")
                                    
                                    # Profit score
                                    profit_score = min(100, max(0, (net_profit / 1000) + (ts['volume'].iloc[-1] / 100)))
                                    st.info(f"**Profit Score:** {profit_score:.0f}/100")
                                
                                # Raw data table
                                with st.expander("📋 Raw Data"):
                                    # Format the data nicely
                                    display_data = ts[['timestamp', 'high', 'low', 'volume']].copy()
                                    display_data['timestamp'] = display_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
                                    display_data['high'] = display_data['high'].apply(lambda x: f"{x:,.0f}")
                                    display_data['low'] = display_data['low'].apply(lambda x: f"{x:,.0f}")
                                    display_data['volume'] = display_data['volume'].apply(lambda x: f"{x:,.0f}")
                                    display_data.columns = ['Time', 'High Price', 'Low Price', 'Volume']
                                    st.dataframe(display_data, use_container_width=True, key=f"raw_data_{sel}")
                                
                                # Export options
                                col1, col2 = st.columns(2)
                                with col1:
                                    csv_data = ts.to_csv(index=False)
                                    st.download_button(
                                        label="📥 Download CSV",
                                        data=csv_data,
                                        file_name=f"{sel}_trends_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                        mime="text/csv",
                                        key=f"download_{sel}"
                                    )
                                with col2:
                                    if st.button("📊 Add to Watchlist", key=f"watchlist_{sel}"):
                                        if 'watchlist' not in st.session_state:
                                            st.session_state.watchlist = []
                                        if sel not in st.session_state.watchlist:
                                            st.session_state.watchlist.append(sel)
                                            st.success(f"Added {sel} to watchlist!")
                                        else:
                                            st.info(f"{sel} already in watchlist")
                            
                            else:
                                st.error("❌ No trend data available for this item")
                                
                                # Show debug information
                                with st.expander("🔧 Debug Information"):
                                    st.write(f"**Item:** {sel}")
                                    st.write(f"**Item ID:** {tid}")
                                    st.write(f"**Timestep:** {timestep}")
                                    
                                    # Test API call manually
                                    try:
                                        url = f"https://prices.runescape.wiki/api/v1/osrs/timeseries?id={tid}&timestep={timestep}"
                                        st.write(f"**API URL:** {url}")
                                        
                                        r = requests.get(url, headers=HEADERS, timeout=15)
                                        st.write(f"**Status Code:** {r.status_code}")
                                        
                                        if r.status_code == 200:
                                            data = r.json()
                                            if 'data' in data and data['data']:
                                                st.write(f"**Data Points:** {len(data['data'])}")
                                                st.json(data['data'][0])
                                            else:
                                                st.warning("API returned empty data - this item may not have recent trading activity")
                                        else:
                                            st.error(f"API Error: {r.text}")
                                            
                                    except Exception as e:
                                        st.error(f"API call failed: {e}")
                else:
                    st.error(f"❌ Item ID not found for '{sel}'")
        # Discord Alert Status with improved information
        st.subheader("🔔 Discord Alert Status")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.info(f"**Active Alerts:** {len(LAST_ALERTS)}")
        
        with col2:
            st.info(f"**Cooldown:** 3 minutes")
        
        with col3:
            alert_status = "🚫 Disabled" if show_all or len(df) > 5 else "✅ Active"
            st.info(f"**Status:** {alert_status}")
        
        with col4:
            if st.button("🔄 Clear Alert History"):
                LAST_ALERTS.clear()
                st.success("Alert history cleared!")
        
        # Alert conditions explanation
        if show_all or len(df) > 5:
            st.warning("""
            🚫 **Discord Alerts Disabled**
            - Alerts are disabled when "Show All" is enabled
            - Alerts are disabled when showing more than 5 items
            - This prevents spam when displaying large datasets
            """)
        else:
            st.success("""
            ✅ **Discord Alerts Active**
            - Will alert on exceptional opportunities (2x minimum margin)
            - Maximum 3 alerts per refresh
            - 3-minute cooldown per item
            """)
        
        # Show recent alerts with more details
        if LAST_ALERTS:
            with st.expander("📋 Recent Alert History"):
                alert_data = []
                now = datetime.datetime.now(datetime.timezone.utc)
                
                for item, last_time in LAST_ALERTS.items():
                    time_since = (now - last_time).total_seconds()
                    if time_since >= 180:
                        status = "✅ Ready"
                        status_color = "🟢"
                    else:
                        remaining = 180 - time_since
                        status = f"⏳ Cooldown ({remaining:.0f}s)"
                        status_color = "🔴"
                    
                    alert_data.append({
                        'Item': item,
                        'Last Alert': last_time.strftime('%H:%M:%S UTC'),
                        'Time Since': f"{time_since:.0f}s ago",
                        'Status': status,
                        '': status_color
                    })
                
                if alert_data:
                    alert_df = pd.DataFrame(alert_data)
                    st.dataframe(alert_df, key="detailed_alert_history_table", use_container_width=True)
        
        # Watchlist section with enhanced functionality
        if 'watchlist' in st.session_state and st.session_state.watchlist:
            st.subheader("⭐ Watchlist")
            
            # Quick watchlist overview
            watchlist_data = []
            for item in st.session_state.watchlist:
                item_row = df[df['Item'] == item]
                if not item_row.empty:
                    row = item_row.iloc[0]
                    watchlist_data.append({
                        'Item': item,
                        'Buy Price': f"{row['Buy Price']:,.0f}",
                        'Sell Price': f"{row['Sell Price']:,.0f}",
                        'Net Margin': f"{row['Net Margin']:,.0f}",
                        'ROI (%)': f"{row['ROI (%)']:.1f}%",
                        'Volume': f"{row['1h Volume']:,.0f}"
                    })
            
            if watchlist_data:
                watchlist_df = pd.DataFrame(watchlist_data)
                st.dataframe(watchlist_df, key="watchlist_table", use_container_width=True)
            
            # Individual watchlist item management
            st.write("**Manage Watchlist Items:**")
            for item in st.session_state.watchlist:
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Check if item is in current results
                    item_row = df[df['Item'] == item]
                    if not item_row.empty:
                        margin = item_row.iloc[0]['Net Margin']
                        roi = item_row.iloc[0]['ROI (%)']
                        st.write(f"📌 **{item}** - Margin: {margin:,.0f} gp | ROI: {roi:.1f}%")
                    else:
                        st.write(f"📌 **{item}** - Not in current results")
                with col2:
                    if st.button(f"Remove", key=f"remove_{item}"):
                        st.session_state.watchlist.remove(item)
                        st.rerun()
        
        # Performance metrics
        st.subheader("📊 Performance Metrics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_margin = df['Net Margin'].mean()
            st.metric("Avg Margin", f"{avg_margin:,.0f} gp")
        with col2:
            avg_roi = df['ROI (%)'].mean()
            st.metric("Avg ROI", f"{avg_roi:.1f}%")
        with col3:
            total_volume = df['1h Volume'].sum()
            st.metric("Total Volume", f"{total_volume:,.0f}")
        with col4:
            high_margin_count = len(df[df['Net Margin'] > MIN_MARGIN * 2])
            st.metric("High Margin Items", f"{high_margin_count}")
    
    else:
        st.warning("No flip opportunities found. Try adjusting your filters or enable 'Show All' to see all items.")
        
        # Show helpful tips when no results
        st.subheader("💡 Tips to Find More Opportunities")
        col1, col2 = st.columns(2)
        with col1:
            st.info("""
            **Adjust Your Filters:**
            - Lower Min Margin (try 200-500 gp)
            - Lower Min Volume (try 100-300)
            - Lower Min Utility (try 1000-5000)
            - Enable "Show All" to see everything
            """)
        with col2:
            st.info("""
            **Market Conditions:**
            - Try different times of day
            - Check if it's a weekend (lower volume)
            - Consider seasonal effects
            - Use "Low-Risk" mode for more results
            """)

if __name__ == '__main__':
    streamlit_dashboard()
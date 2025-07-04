"""
OSRS Data Fetchers Module
Handles all API calls to RuneScape Wiki for prices and item data
"""

import requests
import pandas as pd
import datetime
import traceback

# Configuration
HEADERS = {
    'User-Agent': 'OSRS_Flip_Assistant/1.0 - Real-time GE flipping tool - melon4free on Discord'
}


def get_item_mapping():
    """
    Fetch OSRS item ID-name mapping from RuneScape Wiki API.
    """
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
        print(
            f"📊 Timeseries response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")

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
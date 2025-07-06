"""
OSRS Filters Module
Item filtering logic, backtesting, and correlation analysis
"""

import pandas as pd
import datetime
import streamlit as st
from utils import calculate_ge_tax, categorize_item, get_buy_limits
from analytics import detect_manipulation, calculate_volatility_score, calculate_capital_at_risk
from data_fetchers import get_timeseries

# Configuration
EXCLUDED_ITEMS = ["Zulrah's scales", "Rune arrow", "Coal"]


def filter_items(price_data_result, hourly_data, id2name, show_all=False, mode="Custom"):
    """Filter and analyze items with enhanced analytics"""

    # Handle data structure with timestamp
    if isinstance(price_data_result, dict) and 'data' in price_data_result:
        price_data = price_data_result['data']
        data_timestamp = price_data_result.get('timestamp', datetime.datetime.now(datetime.timezone.utc).timestamp())
    else:
        price_data = price_data_result
        data_timestamp = datetime.datetime.now(datetime.timezone.utc).timestamp()

    print(
        f"🔄 Filtering items. Price data: {len(price_data)}, Hourly data: {len(hourly_data)}, Mappings: {len(id2name)}")

    if not price_data or not id2name:
        print("❌ No data available")
        return pd.DataFrame()

    limits = get_buy_limits()
    recs = []
    processed = 0
    valid_items = 0
    total_items = len(price_data)

    current_time = datetime.datetime.now(datetime.timezone.utc).timestamp()
    price_items = list(price_data.items())

    for iid, stats in price_items:
        processed += 1

        if processed % 1000 == 0:
            print(f"Processed {processed}/{total_items} items...")

        try:
            name = id2name.get(iid, f"Unknown_{iid}")

            # Skip excluded items
            if any(exc.lower() in name.lower() for exc in EXCLUDED_ITEMS):
                continue

            hi = stats.get('high')
            lo = stats.get('low')

            if not hi or not lo or hi <= lo:
                continue

            valid_items += 1

            # Get hourly data
            hourly = hourly_data.get(iid, {})
            vol1h = hourly.get('lowPriceVolume', 0) + hourly.get('highPriceVolume', 0)
            avg_lo = hourly.get('avgLowPrice')

            # Calculate basic metrics
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

            season_ratio = 1.0  # Default value
            cat = categorize_item(name)
            gl = limits.get(name, 1000)
            roi = round(net / lo * 100, 2) if lo else 0

            # Enhanced analytics
            manipulation = detect_manipulation(iid, hi, hourly)
            volatility = calculate_volatility_score(iid, hi, hourly)
            capital_risk = calculate_capital_at_risk(lo, vol1h, gl, volatility['score'])

            # Risk-adjusted scoring
            risk_factor = 1 + (volatility['score'] / 10) + (manipulation['score'] / 20)
            risk_adjusted_util = util / risk_factor if risk_factor > 0 else 0

            persistence_score = 10 - manipulation['score'] - (volatility['score'] / 2)
            persistence_score = max(0, min(10, persistence_score))

            liquidity_score = min(10, vol1h / 100) if vol1h > 0 else 0

            # Calculate data ages
            item_timestamp = stats.get('highTime', data_timestamp)
            data_age_seconds = current_time - item_timestamp
            data_age_minutes = round(data_age_seconds / 60, 1)

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
                'Low Age (min)': low_age_minutes,
                'Manipulation Score': manipulation['score'],
                'Manipulation Risk': manipulation['risk_level'],
                'Volatility Score': volatility['score'],
                'Volatility Level': volatility['level'],
                'Risk Adjusted Utility': risk_adjusted_util,
                'Profit Persistence': persistence_score,
                'Liquidity Score': liquidity_score,
                'Capital Required': capital_risk['capital_required'],
                'Potential Loss': capital_risk['potential_loss'],
                'Risk Ratio': capital_risk['risk_ratio']
            })

        except Exception as e:
            print(f"❌ Error processing item {iid}: {e}")
            continue

    print(f"✅ Processed {processed} items, found {valid_items} valid items, created {len(recs)} recommendations")

    if not recs:
        return pd.DataFrame()

    df = pd.DataFrame(recs)

    # Mode-specific handling
    if mode == "High Volume":
        df = df.sort_values(['1h Volume', 'Net Margin'], ascending=[False, False])
        return df.head(250)

    if show_all:
        return df.sort_values('Utility', ascending=False)

    # Apply filters with session state
    min_margin = st.session_state.get('min_margin', 500)
    min_volume = st.session_state.get('min_volume', 500)
    min_utility = st.session_state.get('min_utility', 10000)
    season_th = st.session_state.get('season_th', 0)
    manipulation_th = st.session_state.get('manipulation_th', 7)
    volatility_th = st.session_state.get('volatility_th', 8)

    df = df[
        (df['Net Margin'] >= min_margin) &
        (df['1h Volume'] >= min_volume) &
        (df['Utility'] >= min_utility) &
        (df['Season Ratio'] >= season_th) &
        (df['Manipulation Score'] <= manipulation_th) &
        (df['Volatility Score'] <= volatility_th)
        ]

    return df.sort_values('Risk Adjusted Utility', ascending=False)

def run_flip_scanner(mode="Custom"):
    """Main scanner function with comprehensive error handling"""
    import streamlit as st
    import pandas as pd
    import traceback
    from data_fetchers import get_item_mapping, get_real_time_prices, get_hourly_prices
    from alerts import send_discord_alert

    # Get show_all from session state instead of global
    show_all = st.session_state.get('show_all_table', False)
    MIN_MARGIN = st.session_state.get('min_margin', 500)

    try:
        # Step 1: Get item mappings
        print("=" * 50)
        print("🚀 Starting OSRS Flip Scanner")
        print("=" * 50)

        id2name, name2id = get_item_mapping()
        if not id2name or not name2id:
            st.error("❌ Failed to load item mappings. Cannot proceed.")
            return pd.DataFrame(), {}

        # Step 2: Get price data
        pd_data = get_real_time_prices()
        if not pd_data:
            st.error("❌ Failed to load price data. Cannot proceed.")
            return pd.DataFrame(), name2id

        # Step 3: Get hourly data (optional)
        h_data = get_hourly_prices()

        # Step 4: Filter items with mode parameter
        df = filter_items(pd_data, h_data, id2name, show_all, mode)

        if df.empty:
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
                len(df) > 0  # And we have at least one opportunity
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

        # Google Sheets export (optional - you can comment this out if causing issues)
        # try:
        #     export_to_sheets(df)
        #     print("✅ Exported to Google Sheets")
        # except Exception as e:
        #     print(f"❌ Sheets export failed: {e}")

        print(f"✅ Scanner completed successfully. Found {len(df)} opportunities.")
        return df, name2id

    except Exception as e:
        error_msg = f"❌ Scanner failed with error: {e}\n{traceback.format_exc()}"
        print(error_msg)
        st.error(error_msg)
        return pd.DataFrame(), {}

def backtest_filters(id2name, days=1):
    """Backtest filter conditions on historical data"""
    sigs = []
    min_margin = st.session_state.get('min_margin', 500)
    min_volume = st.session_state.get('min_volume', 500)
    min_utility = st.session_state.get('min_utility', 10000)

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
                if net >= min_margin and vol >= min_volume and util >= min_utility:
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
    """Compute price correlations between items"""
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
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

from data_fetchers import (
    get_item_mapping,
    get_real_time_prices,
    get_summary,
    get_hourly_prices,
    get_timeseries,
    get_timeseries_custom
)

from utils import (
    calculate_ge_tax,
    categorize_item,
    get_buy_limits
)

from analytics import (
    detect_manipulation,
    calculate_volatility_score,
    calculate_capital_at_risk
)

from charts import (
    create_enhanced_chart,
    create_interactive_chart
)

from filters import (
    filter_items,
    backtest_filters,
    compute_price_correlations
)

from alerts import (
    send_discord_alert,
    get_alert_history,
    clear_alert_history
)

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

# Global cache for performance
MANIPULATION_CACHE = {}
VOLATILITY_CACHE = {}

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


def show_opportunities_page():
    global MIN_MARGIN, MIN_VOLUME, MIN_UTILITY, show_all

    # Debug Info
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

        # Enhanced Sidebar with Better Organization
        st.sidebar.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.sidebar.markdown("### 🎯 Trading Strategy")

        # Strategy mode selection with descriptions
        mode_descriptions = {
            "Custom": "💡 Use custom filter settings below",
            "Low-Risk": "💡 Conservative trading with stable items",
            "High-ROI": "💡 Higher returns with increased risk",
            "Passive Overnight": "💡 Set-and-forget overnight flips",
            "High Volume": "💡 Focus on liquid, high-volume items"
        }

        mode = st.sidebar.selectbox(
            "Select Trading Mode",
            ["Custom", "Low-Risk", "High-ROI", "Passive Overnight", "High Volume"],
            help="Choose your trading strategy"
        )

        # Show mode description
        st.sidebar.caption(mode_descriptions[mode])

        # Apply mode-specific values
        if mode == "Low-Risk":
            m, v, u = 200, 1000, 2000
        elif mode == "High-ROI":
            m, v, u = 1000, 500, 5000
        elif mode == "Passive Overnight":
            m, v, u = 300, 200, 1000
        elif mode == "High Volume":
            m, v, u = 100, 1000, 1000
        else:
            m, v, u = MIN_MARGIN, MIN_VOLUME, MIN_UTILITY

        st.sidebar.markdown('</div>', unsafe_allow_html=True)

        # Custom Filters Section (only show if Custom mode)
        if mode == "Custom":
            st.sidebar.markdown('<div class="filter-section">', unsafe_allow_html=True)
            st.sidebar.markdown("### 💰 Profit Filters")

            # Filter controls with better formatting
            new_min_margin = st.sidebar.slider(
                "Min Net Margin (gp)",
                0, 5000,
                st.session_state.get('min_margin', m),
                50,
                help="Minimum profit after GE tax"
            )
            if new_min_margin != st.session_state.get('min_margin', m):
                st.session_state['min_margin'] = new_min_margin
            MIN_MARGIN = st.session_state.get('min_margin', m)

            new_min_volume = st.sidebar.slider(
                "Min Volume/hr",
                0, 20000,
                st.session_state.get('min_volume', v),
                100,
                help="Minimum hourly trading volume"
            )
            if new_min_volume != st.session_state.get('min_volume', v):
                st.session_state['min_volume'] = new_min_volume
            MIN_VOLUME = st.session_state.get('min_volume', v)

            new_min_utility = st.sidebar.slider(
                "Min Utility Score",
                0, 50000,
                st.session_state.get('min_utility', u),
                500,
                help="Minimum utility score (profit × volume)"
            )
            if new_min_utility != st.session_state.get('min_utility', u):
                st.session_state['min_utility'] = new_min_utility
            MIN_UTILITY = st.session_state.get('min_utility', u)

            new_season_th = st.sidebar.slider(
                "Min Season Ratio",
                0.0, 5.0,
                st.session_state.get('season_th', 0.0),
                0.1,
                help="Seasonal price adjustment factor"
            )
            if new_season_th != st.session_state.get('season_th', 0.0):
                st.session_state['season_th'] = new_season_th

            st.sidebar.markdown('</div>', unsafe_allow_html=True)

            # Risk Management Section
            st.sidebar.markdown('<div class="filter-section">', unsafe_allow_html=True)
            st.sidebar.markdown("### 🔬 Risk Management")

            new_manipulation_th = st.sidebar.slider(
                "Max Manipulation Score",
                0, 10,
                st.session_state.get('manipulation_th', 7),
                1,
                help="Lower = stricter filtering of potentially manipulated items"
            )
            if new_manipulation_th != st.session_state.get('manipulation_th', 7):
                st.session_state['manipulation_th'] = new_manipulation_th

            new_volatility_th = st.sidebar.slider(
                "Max Volatility Score",
                0, 10,
                st.session_state.get('volatility_th', 8),
                1,
                help="Lower = stricter filtering of volatile items"
            )
            if new_volatility_th != st.session_state.get('volatility_th', 8):
                st.session_state['volatility_th'] = new_volatility_th

            st.sidebar.markdown('</div>', unsafe_allow_html=True)

        # Preset Management Section
        st.sidebar.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.sidebar.markdown("### 📋 Preset Management")

        # Preset load/save with better UI
        preset_options = [''] + list(st.session_state.presets.keys())
        ps = st.sidebar.selectbox(
            "Load Saved Preset",
            preset_options,
            help="Load previously saved filter configurations"
        )

        if ps:
            m, v, u, season = st.session_state.presets[ps]
            MIN_MARGIN, MIN_VOLUME, MIN_UTILITY = m, v, u
            st.session_state['season_th'] = season
            st.sidebar.success(f"✅ Loaded preset: {ps}")

        # Save new preset
        col1, col2 = st.sidebar.columns([2, 1])
        with col1:
            name_in = st.text_input("Preset Name", placeholder="Enter name...", label_visibility="collapsed")
        with col2:
            if st.button("💾 Save", help="Save current settings as preset") and name_in:
                st.session_state.presets[name_in] = (MIN_MARGIN, MIN_VOLUME, MIN_UTILITY,
                                                     st.session_state.get('season_th', 0))
                st.sidebar.success(f"💾 Saved: {name_in}")

        st.sidebar.markdown('</div>', unsafe_allow_html=True)

        # Display Options Section
        st.sidebar.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.sidebar.markdown("### ⚙️ Display Options")

        show_all = st.sidebar.checkbox(
            "Show All Items",
            value=False,
            help="Display all items regardless of filters"
        )

        # Mobile view toggle
        mobile_view = st.sidebar.checkbox(
            "📱 Mobile-Friendly View",
            value=False,
            help="Simplified layout optimized for mobile devices"
        )
        if mobile_view != st.session_state.get('mobile_view', False):
            st.session_state['mobile_view'] = mobile_view

        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox(
            "Auto-refresh (30s)",
            help="Automatically refresh data every 30 seconds"
        )

        if auto_refresh:
            st.sidebar.caption("⏰ Auto-refreshing every 30 seconds...")
            import time
            time.sleep(30)
            st.rerun()

        # Keyboard shortcuts info - ADD THIS NEW SECTION HERE
        with st.sidebar.expander("⌨️ Keyboard Shortcuts"):
            st.markdown("""
            **Available Shortcuts:**
            - `Ctrl + R` - Refresh data
            - `Ctrl + /` - Focus search
            - `Escape` - Clear current selection

            **Mobile Gestures:**
            - Swipe left/right on table rows
            - Pull down to refresh (experimental)
            """)

        st.sidebar.markdown('</div>', unsafe_allow_html=True)  # This closing tag stays at the end

    # Main scan button
    if st.button("🔄 Refresh Data", type="primary"):
        # Enhanced loading with progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("🔍 Loading item mappings...")
            progress_bar.progress(20)

            status_text.text("💰 Fetching current market prices...")
            progress_bar.progress(40)

            status_text.text("📊 Analyzing opportunities...")
            progress_bar.progress(60)

            with st.spinner("🔄 Processing data..."):
                df, name2id = run_flip_scanner(mode)

            progress_bar.progress(80)
            status_text.text("✅ Finalizing results...")

            # Store price data for trend viewer
            if 'price_data' not in st.session_state:
                st.session_state.price_data = get_real_time_prices()

            progress_bar.progress(100)
            status_text.text("🎉 Scan complete!")

            # Clear progress indicators after short delay
            import time
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Error during scan: {e}")

    else:
        # Run initial scan with loading
        if 'initial_load_done' not in st.session_state:
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("🚀 Starting OSRS Flip Assistant...")
                progress_bar.progress(10)

                status_text.text("🔍 Loading item database...")
                progress_bar.progress(30)

                status_text.text("💰 Fetching market data...")
                progress_bar.progress(50)

                status_text.text("📊 Finding opportunities...")
                progress_bar.progress(70)

                # Enhanced loading for initial scan
                loading_container = st.empty()
                loading_container.markdown("""
                                <div style="text-align: center; padding: 20px;">
                                    <div class="loading-spinner"></div>
                                    <p style="color: #4CAF50; margin-top: 10px;">🎯 Analyzing flipping opportunities...</p>
                                </div>
                                """, unsafe_allow_html=True)

                df, name2id = run_flip_scanner(mode)

                # Clear loading
                loading_container.empty()
                df, name2id = run_flip_scanner(mode)

                progress_bar.progress(90)
                status_text.text("✅ Ready!")

                # Store price data for trend viewer
                if 'price_data' not in st.session_state:
                    st.session_state.price_data = get_real_time_prices()

                progress_bar.progress(100)
                status_text.text("🎉 Welcome to OSRS Flip Assistant!")

                # Mark initial load as complete
                st.session_state.initial_load_done = True

                # Clear progress after delay
                import time
                time.sleep(1.5)
                progress_bar.empty()
                status_text.empty()

            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Error during initial load: {e}")
        else:
            # Quick load for subsequent visits
            # Create enhanced loading container
            loading_container = st.empty()
            loading_container.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <div class="loading-spinner"></div>
                        <p style="color: #4CAF50; margin-top: 10px;">🔄 Processing data...</p>
                    </div>
                    """, unsafe_allow_html=True)

            # Process data
            df, name2id = run_flip_scanner(mode)
            if 'price_data' not in st.session_state:
                st.session_state.price_data = get_real_time_prices()

            # Clear loading
            loading_container.empty()

    # Get price data for trend viewer
    price_data = st.session_state.get('price_data', {})

    # Display results with color coding
    if not df.empty:
        # Create enhanced table header
        avg_margin = df['Net Margin'].mean()
        avg_risk_util = df['Risk Adjusted Utility'].mean() if 'Risk Adjusted Utility' in df.columns else 0
        create_table_header(len(df), avg_margin, avg_risk_util)

        if not df.empty:
            # Add advanced features
            st.markdown("---")

            # Temporary simple search until we add the advanced version
            search_term = ""
            category_filter = "All Categories"
            sort_option = "Profit Margin"

            # Profit Calculator
            create_profit_calculator()

            # Create enhanced table header
            avg_margin = df['Net Margin'].mean()
            avg_risk_util = df['Risk Adjusted Utility'].mean() if 'Risk Adjusted Utility' in df.columns else 0
            create_table_header(len(df), avg_margin, avg_risk_util)

        # Add color coding explanation
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            total_items = len(df)
            st.metric("Total Items", total_items)

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
            if 'Capital Required' in df.columns:
                total_capital = df['Capital Required'].sum()
                st.metric("Total Capital", f"{total_capital:,.0f} gp")
            else:
                st.metric("Total Volume/hr", f"{df['1h Volume'].sum():,.0f}")

        # Ensure numerical columns are properly typed for sorting
        num_cols = ['Buy Price', 'Sell Price', 'Net Margin', 'ROI (%)', '1h Volume']
        for c in num_cols:
            df[c] = pd.to_numeric(df[c], errors='coerce')

        display_df = df.copy()

        # Add color coding based on ROI and data age
        def get_enhanced_color_code(row):
            roi, data_age, volume = row['ROI (%)'], row['Data Age (min)'], row['1h Volume']

            # Check if enhanced columns exist
            if 'Manipulation Score' in row and 'Volatility Score' in row:
                manipulation, volatility = row['Manipulation Score'], row['Volatility Score']

                # Enhanced status with detailed categories
                if manipulation >= 7 or volatility >= 8:
                    return "🔴 High Risk"  # Red for high risk
                elif data_age > 5:
                    return "🔴 Stale Data"  # Red for old data
                elif data_age > 2:
                    return "🟡 Aging Data"  # Yellow for aging data
                elif roi >= 5 and volume >= 1000 and manipulation <= 3 and volatility <= 4:
                    return "🟢 Excellent"  # Green for excellent low-risk opportunities
                elif roi >= 2 and volume >= 500:
                    return "🟡 Good"  # Yellow for good
                else:
                    return "🔴 Caution"  # Red for caution
            else:
                # Fall back to original logic if enhanced columns don't exist
                if data_age > 5:
                    return "🔴 Stale Data"
                elif data_age > 2:
                    return "🟡 Aging Data"
                elif roi >= 5 and volume >= 1000:
                    return "🟢 Excellent"
                elif roi >= 2 and volume >= 500:
                    return "🟡 Good"
                else:
                    return "🔴 Caution"

        # Apply enhanced status badges
        def create_status_badge(row):
            status = get_enhanced_color_code(row)

            if "Excellent" in status:
                return "🟢 EXCELLENT"
            elif "Good" in status:
                return "🟡 GOOD"
            else:
                return "🔴 CAUTION"

        display_df['Status'] = display_df.apply(create_status_badge, axis=1)

        # Get buy limits for display
        limits = get_buy_limits()

        # Create formatted columns that preserve numerical sorting
        # Keep original numerical columns and add formatted display columns
        display_df['Buy Price (formatted)'] = display_df['Buy Price'].apply(lambda x: f"{x:,}")
        display_df['Sell Price (formatted)'] = display_df['Sell Price'].apply(lambda x: f"{x:,}")
        display_df['Net Margin (formatted)'] = display_df['Net Margin'].apply(lambda x: f"{x:,}")
        display_df['ROI (formatted)'] = display_df['ROI (%)'].apply(lambda x: f"{x:.1f}%")
        display_df['Volume (formatted)'] = display_df['1h Volume'].apply(lambda x: f"{x:,}")

        # Enhanced data freshness indicators
        def format_price_with_freshness(price, age_minutes):
            if age_minutes <= 1:
                freshness_class = "data-fresh"
                freshness_icon = "🟢"
            elif age_minutes <= 3:
                freshness_class = "data-aging"
                freshness_icon = "🟡"
            else:
                freshness_class = "data-stale"
                freshness_icon = "🔴"

            return f'{freshness_icon} {price:,} gp <small>({age_minutes:.1f}m ago)</small>'

        display_df['Approx. Offer Price'] = display_df.apply(
            lambda row: format_price_with_freshness(row['Buy Price'], row['Low Age (min)']),
            axis=1)
        display_df['Approx. Sell Price'] = display_df.apply(
            lambda row: format_price_with_freshness(row['Sell Price'], row['High Age (min)']),
            axis=1)
        display_df['Tax'] = display_df['Sell Price'].apply(lambda x: f"{calculate_ge_tax(x):,}")
        display_df['Tax'] = display_df['Sell Price'].apply(lambda x: f"{calculate_ge_tax(x):,}")
        display_df['GE Limit'] = display_df['Item'].apply(
            lambda x: f"{limits.get(x, 'N/A'):,}" if limits.get(x) else "N/A")
        display_df['Buy/Sell Ratio'] = display_df.apply(
            lambda row: f"{((row['Sell Price'] - row['Buy Price']) / row['Buy Price'] * 100):+.2f}%",
            axis=1
        )

        # Add Chart column before creating display dataframe
        display_df['Quick Actions'] = display_df['Item'].apply(lambda x: "📊 Chart | ⭐ Watch | 📋 Copy")

        # Select columns for display - use original numerical columns for sorting
        columns_to_display = [
            'Status',
            'Item',
            'Quick Actions',
            'Buy Price',
            'Sell Price',
            'Net Margin',
            'ROI (%)',
            '1h Volume',
            'Risk Adjusted Utility',
            'Manipulation Risk',
            'Volatility Level',
            'Approx. Offer Price',
            'Approx. Sell Price',
            'Tax',
            'GE Limit'
        ]

        # Create the display dataframe
        final_display_df = display_df[columns_to_display].copy()

        # Apply custom CSS for better formatting
        st.markdown("""
        <style>
        .stDataFrame {
            font-size: 12px;
        }
        </style>
        """, unsafe_allow_html=True)

        # Use column configuration to format display while preserving sorting
        column_config = {
            'Buy Price': st.column_config.NumberColumn(
                'Buy Price',
                help='Current buy price',
                format='%d gp'
            ),
            'Sell Price': st.column_config.NumberColumn(
                'Sell Price',
                help='Current sell price',
                format='%d gp'
            ),
            'Net Margin': st.column_config.NumberColumn(
                'Net Margin',
                help='Profit after GE tax',
                format='%d gp'
            ),
            'ROI (%)': st.column_config.NumberColumn(
                'ROI (%)',
                help='Return on investment',
                format='%.1f%%'
            ),
            '1h Volume': st.column_config.NumberColumn(
                '1h Volume',
                help='Trading volume per hour',
                format='%d'
            ),
            'Risk Adjusted Utility': st.column_config.NumberColumn(
                'Risk Adj. Utility',
                help='Utility score adjusted for manipulation and volatility risk',
                format='%.0f'
            ),
            'Manipulation Risk': st.column_config.TextColumn(
                'Manip. Risk',
                help='Risk level of price manipulation (Normal/Low/Medium/High)'
            ),
            'Volatility Level': st.column_config.TextColumn(
                'Volatility',
                help='Price volatility level (Very Low to Very High)'
            )
        }

        # Custom table with clickable item names + Pagination
        st.caption("💡 Click any item name to view its chart")

        # Pagination controls
        total_items = len(final_display_df)
        items_per_page = 25

        # Initialize pagination state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 0

        # Calculate pagination info
        total_pages = (total_items + items_per_page - 1) // items_per_page  # Ceiling division
        start_idx = st.session_state.current_page * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)

        # Add CSS for styling
        st.markdown("""
        <style>
        .item-name-btn {
            background: none !important;
            border: none !important;
            color: #4CAF50 !important;
            text-decoration: none !important;
            cursor: pointer !important;
            font-weight: 500 !important;
            padding: 4px 8px !important;
            text-align: left !important;
            width: 100% !important;
            font-family: monospace !important;
        }

        .item-name-btn:hover {
            color: #45a049 !important;
            background-color: rgba(76, 175, 80, 0.1) !important;
            text-decoration: underline !important;
        }

        .table-row {
            border-bottom: 1px solid #333 !important;
            padding: 2px 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Alternative: Show All button
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📋 Show All in Table", help="Show all items in a scrollable table"):
                st.session_state['show_all_table'] = True
                st.rerun()

        # Check if user wants to see all items in a regular table
        if st.session_state.get('show_all_table', False):
            st.markdown("---")
            st.subheader("📊 All Items - Scrollable Table")

            # Show regular dataframe with all items
            st.dataframe(
                final_display_df,
                use_container_width=True,
                key="all_items_table",
                height=600,
                hide_index=True,
                column_config=column_config
            )

            # Quick chart access below full table
            st.markdown("---")
            st.subheader("📈 Quick Chart Access")

            # Search for specific item
            search_item = st.text_input("🔍 Search for item to chart:",
                                        placeholder="Type exact item name...",
                                        key="full_table_search")

            if search_item:
                matching_items = final_display_df[
                    final_display_df['Item'].str.contains(search_item, case=False, na=False)]
                if not matching_items.empty:
                    for _, row in matching_items.head(5).iterrows():
                        if st.button(f"📊 {row['Item']}",
                                     key=f"full_search_{row['Item']}",
                                     help=f"Chart for {row['Item']}"):
                            st.session_state['selected_item'] = row['Item']
                            st.session_state.page = 'charts'
                            st.rerun()
                else:
                    st.warning("No items found matching your search.")

            # Back to paginated view
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📄 ⬅️ Back to Paginated View", type="primary", use_container_width=True):
                    st.session_state['show_all_table'] = False
                    st.rerun()

            return  # Skip the paginated table if showing all

        # Get current page items
        current_page_items = final_display_df.iloc[start_idx:end_idx]

        # Create table header
        # Mobile-responsive table header
        if st.session_state.get('mobile_view', False):
            # Simplified mobile layout
            st.markdown("### 📱 Mobile View")
            # We'll create a simplified mobile table layout
        else:
            # Desktop table header
            header_cols = st.columns([0.4, 2, 1, 1, 1.2, 1, 1, 1.5, 1.2, 1.2, 1.2, 1.2])
        headers = ['Status', 'Item Name', 'Buy Price', 'Sell Price', 'Net Margin', 'ROI (%)',
                   '1h Volume', 'Risk Adj. Utility', 'Manip. Risk', 'Volatility', 'Tax', 'GE Limit']

        for i, header in enumerate(headers):
            if i < len(header_cols):
                header_cols[i].markdown(f"**{header}**")

        st.markdown("---")

        # Pre-format all data outside the loop for better performance
        formatted_page_data = []
        for idx, (_, row) in enumerate(current_page_items.iterrows()):
            item_name = row['Item']
            roi_color = "🟢" if row['ROI (%)'] >= 5 else "🟡" if row['ROI (%)'] >= 2 else "🔴"
            risk = row.get('Manipulation Risk', 'N/A')
            risk_color = "🟢" if risk == "Normal" else "🟡" if risk == "Low" else "🔴"
            vol = row.get('Volatility Level', 'N/A')
            vol_color = "🟢" if "Low" in str(vol) else "🟡" if "Medium" in str(vol) else "🔴"

            formatted_page_data.append({
                'idx': idx,
                'status': row['Status'],
                'item_name': item_name,
                'buy_price': f"{row['Buy Price']:,}",
                'sell_price': f"{row['Sell Price']:,}",
                'net_margin': f"**{row['Net Margin']:,}**",
                'roi_display': f"{roi_color} {row['ROI (%)']:.1f}%",
                'volume': f"{row['1h Volume']:,}",
                'risk_util': f"{row['Risk Adjusted Utility']:,.0f}",
                'risk_display': f"{risk_color} {risk}",
                'vol_display': f"{vol_color} {vol}",
                'tax': row['Tax'],
                'ge_limit': row['GE Limit'],
                'button_key': f"item_page_{st.session_state.current_page}_idx_{idx}_{hash(item_name)}"
            })

        # Create table rows using pre-formatted data
        for row_data in formatted_page_data:
            with st.container():
                cols = st.columns([0.4, 2, 1, 1, 1.2, 1, 1, 1.5, 1.2, 1.2, 1.2, 1.2])

                cols[0].write(row_data['status'])

                with cols[1]:
                    if st.button(
                            row_data['item_name'],
                            key=row_data['button_key'],
                            help=f"Click to view {row_data['item_name']} chart",
                            use_container_width=True
                    ):
                        st.session_state['selected_item'] = row_data['item_name']
                        st.session_state.page = 'charts'
                        st.rerun()

                cols[2].write(row_data['buy_price'])
                cols[3].write(row_data['sell_price'])
                cols[4].write(row_data['net_margin'])
                cols[5].write(row_data['roi_display'])
                cols[6].write(row_data['volume'])
                cols[7].write(row_data['risk_util'])
                cols[8].write(row_data['risk_display'])
                cols[9].write(row_data['vol_display'])
                cols[10].write(row_data['tax'])
                cols[11].write(row_data['ge_limit'])

        # Pagination controls at the bottom (repeat for convenience)
        st.markdown("""
        <div class="pagination-container">
            <div class="pagination-info">📄 Page Navigation</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([1, 1, 2, 1])

        with col1:
            if st.button("⬅️ Prev", disabled=st.session_state.current_page == 0, key="bottom_prev"):
                st.session_state.current_page = max(0, st.session_state.current_page - 1)
                st.rerun()

        with col2:
            if st.button("➡️ Next", disabled=st.session_state.current_page >= total_pages - 1, key="bottom_next"):
                st.session_state.current_page = min(total_pages - 1, st.session_state.current_page + 1)
                st.rerun()

        with col3:
            st.markdown(f"""
            <div style="text-align: center; color: #4CAF50; font-weight: 500; padding: 8px;">
            📄 Page {st.session_state.current_page + 1} of {total_pages} 
            <span style="color: #bbb;">({start_idx + 1}-{end_idx} of {total_items} items)</span>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            # Quick jump to first/last page
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("⏮️ First", disabled=st.session_state.current_page == 0):
                    st.session_state.current_page = 0
                    st.rerun()
            with col_b:
                if st.button("⏭️ Last", disabled=st.session_state.current_page >= total_pages - 1):
                    st.session_state.current_page = total_pages - 1
                    st.rerun()

        # Enhanced item chart navigation
        st.subheader("📊 Quick Chart Access")

        # Create a more user-friendly interface with search
        col1, col2 = st.columns([3, 1])

        with col1:
            # Add search functionality
            search_term = st.text_input("🔍 Search for item to chart:",
                                        placeholder="Type item name...",
                                        key="chart_search")

            # Filter items based on search
            if search_term:
                filtered_items = [item for item in df['Item'].tolist()
                                  if search_term.lower() in item.lower()]
            else:
                filtered_items = df['Item'].tolist()

            # Show filtered selection
            if filtered_items:
                selected_item = st.selectbox(
                    f"Select from {len(filtered_items)} items:",
                    options=filtered_items,
                    key="enhanced_item_selector",
                    help="Select an item to view its detailed price chart"
                )
            else:
                st.warning("No items match your search")
                selected_item = None

        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if selected_item:
                if st.button(f"📈 Chart {selected_item}", type="primary", use_container_width=True):
                    st.session_state['selected_item'] = selected_item
                    st.session_state.page = 'charts'  # Navigate to charts page
                    st.rerun()

        # Quick access buttons for top items
        if len(df) > 0:
            st.write("**🚀 Quick Access - Top Opportunities:**")

            # Show top 5 items as quick buttons
            top_items = df.head(5)['Item'].tolist()

            # Create columns for buttons
            button_cols = st.columns(min(len(top_items), 5))

            for i, item in enumerate(top_items):
                with button_cols[i]:
                    if st.button(f"📊 {item[:15]}{'...' if len(item) > 15 else ''}",
                                 key=f"quick_chart_{i}_{item}",
                                 help=f"View chart for {item}",
                                 use_container_width=True):
                        st.session_state['selected_item'] = item
                        st.session_state.page = 'charts'
                        st.rerun()

        # Mode-specific information
        if mode == "High Volume":
            st.info(f"🔥 **High Volume Mode**: Showing top {len(df)} highest traded items sorted by volume and profit")

        # Export options
        create_export_options(df)

        # Watchlist management
        create_watchlist_manager()

        # Enhanced Trend viewer
        st.markdown("""
        <div class="chart-section">
            <h2 style="color: #4CAF50; margin-bottom: 20px;">📊 Advanced Trend Viewer</h2>
            <p style="color: #bbb; margin-bottom: 20px;">Interactive price analysis with real-time data</p>
        </div>
        """, unsafe_allow_html=True)

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
                                        min_price = st.number_input("Min Price Filter", min_value=0, value=0,
                                                                    key=f"min_price_{sel}")
                                    with col2:
                                        max_price = st.number_input("Max Price Filter", min_value=0,
                                                                    value=int(ts['high'].max()) if not ts.empty else 0,
                                                                    key=f"max_price_{sel}")
                                    with col3:
                                        min_volume = st.number_input("Min Volume Filter", min_value=0, value=0,
                                                                     key=f"min_volume_{sel}")

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
                                # create_enhanced_chart(ts, sel, chart_type, chart_height, chart_width,
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
                                    plt.hist(ts['high'], bins=20, alpha=0.7, color=price_color_high,
                                             label='High Prices')
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
                                        plt.plot(ts['timestamp'], ts['high'], label='High Price', alpha=0.7,
                                                 color=price_color_high)
                                        plt.plot(ts['timestamp'], ts['ma_5'], label='MA 5', linewidth=2, color='orange')
                                        if len(ts) >= 10:
                                            plt.plot(ts['timestamp'], ts['ma_10'], label='MA 10', linewidth=2,
                                                     color='purple')
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
                                        recent_trend = "📈 Rising" if ts['high'].iloc[-1] > ts['high'].iloc[
                                            -5] else "📉 Falling"
                                    else:
                                        recent_trend = "📊 Insufficient data"
                                    st.info(f"**Recent Trend:** {recent_trend}")

                                    # Volume trend
                                    vol_trend = "📈 Increasing" if ts['volume'].iloc[-1] > ts[
                                        'volume'].mean() else "📉 Decreasing"
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
                                            show_success_message(f"Added {sel} to watchlist!", "⭐")
                                        else:
                                            show_warning_message(f"{sel} already in watchlist", "📌")

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
                                                st.warning(
                                                    "API returned empty data - this item may not have recent trading activity")
                                        else:
                                            st.error(f"API Error: {r.text}")

                                    except Exception as e:
                                        st.error(f"API call failed: {e}")
                else:
                    st.error(f"❌ Item ID not found for '{sel}'")
        # Discord Alert Status with improved information
        st.markdown('<div class="alert-success">', unsafe_allow_html=True)
        st.markdown("### 🔔 Discord Alert Status")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.info(f"**Active Alerts:** {len(get_alert_history())}")

        with col2:
            st.info(f"**Cooldown:** 3 minutes")

        with col3:
            alert_status = "🚫 Disabled" if show_all or len(df) > 5 else "✅ Active"
            st.info(f"**Status:** {alert_status}")

        with col4:
            if st.button("🔄 Clear Alert History"):
                clear_alert_history()
                show_success_message("Alert history cleared!", "🗑️")

        st.markdown('</div>', unsafe_allow_html=True)

        # Alert conditions explanation with enhanced styling
        if show_all or len(df) > 5:
            st.markdown("""
            <div class="alert-warning">
            <strong>🚫 Discord Alerts Disabled</strong><br>
            • Alerts are disabled when "Show All" is enabled<br>
            • Alerts are disabled when showing more than 5 items<br>
            • This prevents spam when displaying large datasets
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="alert-success">
            <strong>✅ Discord Alerts Active</strong><br>
            • Will alert on exceptional opportunities (2x minimum margin)<br>
            • Maximum 3 alerts per refresh<br>
            • 3-minute cooldown per item
            </div>
            """, unsafe_allow_html=True)

        # Show recent alerts with more details
        if get_alert_history():
            with st.expander("📋 Recent Alert History"):
                alert_data = []
                now = datetime.datetime.now(datetime.timezone.utc)

                for item, last_time in get_alert_history().items():
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
        show_warning_message("No flip opportunities found. Try adjusting your filters or enable 'Show All' to see all items.", "📊")

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


def show_charts_page():
    """Enhanced charts page with navigation and item analysis"""

    # Check if we have a selected item
    selected_item = st.session_state.get('selected_item', None)

    if not selected_item:
        # No item selected - show selection interface
        st.warning("📊 No item selected for chart analysis")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.info("""
            **To view an item chart:**
            1. Go back to the Opportunities page
            2. Use the item selector to choose an item
            3. Click the chart button to return here
            """)

        with col2:
            if st.button("🔍 Browse Opportunities", type="primary"):
                st.session_state.page = 'opportunities'
                st.rerun()

        return

    # Item is selected - show chart interface
    st.success(f"📈 Analyzing: **{selected_item}**")

    # Navigation and controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        # Change item button
        if st.button("🔄 Select Different Item", type="secondary"):
            st.session_state.page = 'opportunities'
            st.rerun()

    with col2:
        # Time period selector
        time_period = st.selectbox("📅 Time Period",
                                   ["Day", "Week", "Month", "Year"],
                                   index=1,  # Default to Week
                                   key="chart_time_period")

    with col3:
        # Chart type selector
        chart_type = st.selectbox("📊 Chart Type",
                                  ["Interactive", "Traditional"],
                                  key="chart_type_selector")

    with col4:
        # Export options
        if st.button("📥 Export Data", help="Download chart data as CSV"):
            st.info("Export functionality coming soon!")

    # Map time periods to timestep values
    time_mapping = {
        "Day": "5m",
        "Week": "1h",
        "Month": "6h",
        "Year": "24h"
    }
    timestep = time_mapping[time_period]

    # Get item data
    try:
        # Get item mappings
        from data_fetchers import get_item_mapping, get_timeseries_custom
        id2name, name2id = get_item_mapping()

        if selected_item not in name2id:
            st.error(f"❌ Item '{selected_item}' not found in database")
            return

        item_id = name2id[selected_item]

        # Load chart data
        with st.spinner(f"Loading {time_period.lower()} data for {selected_item}..."):
            ts = get_timeseries_custom(item_id, timestep)

        if ts is None or ts.empty:
            st.error(f"❌ No chart data available for {selected_item}")

            # Show debug info
            with st.expander("🔧 Debug Information"):
                st.write(f"**Item:** {selected_item}")
                st.write(f"**Item ID:** {item_id}")
                st.write(f"**Time Period:** {time_period}")
                st.write(f"**Timestep:** {timestep}")

                # Test API manually
                import requests
                HEADERS = {'User-Agent': 'OSRS_Flip_Assistant/1.0'}
                url = f"https://prices.runescape.wiki/api/v1/osrs/timeseries?id={item_id}&timestep={timestep}"

                try:
                    r = requests.get(url, headers=HEADERS, timeout=10)
                    st.write(f"**API URL:** {url}")
                    st.write(f"**Status Code:** {r.status_code}")
                    if r.status_code == 200:
                        data = r.json()
                        st.write(f"**Data Points:** {len(data.get('data', []))}")
                    else:
                        st.write(f"**Error:** {r.text}")
                except Exception as e:
                    st.write(f"**API Error:** {e}")
            return

        # Success - display the chart
        st.success(f"✅ Loaded {len(ts)} data points for {time_period.lower()} view")

        # Chart options
        with st.expander("🎨 Chart Settings"):
            col1, col2 = st.columns(2)
            with col1:
                chart_height = st.slider("Chart Height", 400, 800, 600)
                show_volume = st.checkbox("Show Volume", value=True)
            with col2:
                chart_width = st.slider("Chart Width", 800, 1400, 1000)
                show_trend = st.checkbox("Show Trend Line", value=True)

        # Get current timestep from session state or use default
        current_timestep = st.session_state.get('chart_timestep', timestep)

        # Check if we need to reload data due to timestep change
        if st.session_state.get('chart_reload_needed', False):
            st.session_state['chart_reload_needed'] = False
            # Reload data with new timestep
            with st.spinner(f"Loading data with new time period..."):
                ts = get_timeseries_custom(item_id, current_timestep)

            if ts is None or ts.empty:
                st.error(f"❌ No data available for selected time period")
                return

        # Display the enhanced chart with time controls
        from charts import create_interactive_chart
        create_interactive_chart(
            ts,
            item_name=selected_item,
            width=chart_width,
            height=chart_height,
            show_time_controls=True,
            current_timestep=current_timestep
        )

        # Chart analysis
        show_chart_analysis(ts, selected_item, time_period)

    except Exception as e:
        st.error(f"❌ Error loading chart: {e}")
        import traceback
        st.code(traceback.format_exc())


def show_chart_analysis(ts, item_name, time_period):
    """Display analysis of the chart data"""

    st.subheader("📊 Chart Analysis")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        current_high = ts['high'].iloc[-1]
        current_low = ts['low'].iloc[-1]
        spread = current_high - current_low
        st.metric(
            "Current Spread",
            f"{spread:,.0f} gp",
            f"{(spread / current_low * 100):+.1f}%"
        )

    with col2:
        price_change = ts['high'].iloc[-1] - ts['high'].iloc[0]
        change_pct = (price_change / ts['high'].iloc[0]) * 100
        st.metric(
            f"{time_period} Price Change",
            f"{price_change:+,.0f} gp",
            f"{change_pct:+.1f}%"
        )

    with col3:
        avg_volume = ts['volume'].mean()
        total_volume = ts['volume'].sum()
        st.metric(
            "Average Volume",
            f"{avg_volume:,.0f}",
            f"Total: {total_volume:,.0f}"
        )

    with col4:
        volatility = (ts['high'].std() / ts['high'].mean()) * 100
        st.metric(
            "Price Volatility",
            f"{volatility:.1f}%",
            "Lower is more stable"
        )

    # Price trend analysis
    st.subheader("📈 Price Trends")

    if len(ts) >= 10:
        # Calculate moving averages
        ts['ma_short'] = ts['high'].rolling(window=5).mean()
        ts['ma_long'] = ts['high'].rolling(window=min(20, len(ts) // 2)).mean()

        # Trend direction
        recent_trend = "📈 Bullish" if ts['ma_short'].iloc[-1] > ts['ma_long'].iloc[-1] else "📉 Bearish"
        trend_strength = abs(ts['ma_short'].iloc[-1] - ts['ma_long'].iloc[-1]) / ts['ma_long'].iloc[-1] * 100

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Trend Direction:** {recent_trend}")
            st.info(f"**Trend Strength:** {trend_strength:.1f}%")

        with col2:
            # Support and resistance levels
            resistance = ts['high'].quantile(0.8)
            support = ts['low'].quantile(0.2)
            st.info(f"**Resistance Level:** {resistance:,.0f} gp")
            st.info(f"**Support Level:** {support:,.0f} gp")

    # Trading opportunities
    st.subheader("💡 Trading Insights")

    from utils import calculate_ge_tax

    # Current flip potential
    current_spread = ts['high'].iloc[-1] - ts['low'].iloc[-1]
    tax = calculate_ge_tax(ts['high'].iloc[-1])
    net_profit = current_spread - tax
    roi = (net_profit / ts['low'].iloc[-1]) * 100 if ts['low'].iloc[-1] > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(f"**Potential Profit:** {net_profit:,.0f} gp")
        st.info(f"**ROI:** {roi:.1f}%")

    with col2:
        # Volume analysis
        vol_trend = "📈 Increasing" if ts['volume'].iloc[-1] > avg_volume else "📉 Decreasing"
        st.info(f"**Volume Trend:** {vol_trend}")

        # Best trading times
        if len(ts) > 24:  # Only if we have enough data
            hourly_vol = ts.groupby(ts['timestamp'].dt.hour)['volume'].mean()
            best_hour = hourly_vol.idxmax() if not hourly_vol.empty else "Unknown"
            st.info(f"**Peak Trading Hour:** {best_hour}:00")

    with col3:
        # Risk assessment
        price_stability = "High" if volatility < 5 else "Medium" if volatility < 15 else "Low"
        st.info(f"**Price Stability:** {price_stability}")

        # Recommendation
        if roi > 3 and volatility < 10:
            recommendation = "🟢 Good Opportunity"
        elif roi > 1 and volatility < 20:
            recommendation = "🟡 Moderate Opportunity"
        else:
            recommendation = "🔴 High Risk"
        st.info(f"**Recommendation:** {recommendation}")


def inject_custom_css():
    """Inject custom CSS for OSRS-themed dark UI"""
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Root Variables */
        :root {
            --primary-bg: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            --card-bg: rgba(255, 255, 255, 0.05);
            --card-border: rgba(255, 255, 255, 0.1);
            --accent-color: #4CAF50;
            --text-primary: #e0e0e0;
            --text-secondary: #bbb;
            --osrs-gold: #ffd700;
        }

        /* Global Overrides */
        .stApp {
            background: var(--primary-bg) !important;
            font-family: 'Inter', 'Segoe UI', sans-serif !important;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Main content styling */
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1400px !important;
        }

        /* Headers */
        h1, h2, h3 {
            color: var(--osrs-gold) !important;
            font-weight: 600 !important;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5) !important;
        }

        h1 {
            font-size: 2.5rem !important;
            margin-bottom: 1rem !important;
        }

        /* Card-like containers */
        .stContainer > div {
            background: var(--card-bg) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 15px !important;
            padding: 20px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        }

        /* Sidebar styling */
        .css-1d391kg {
            background: rgba(255, 255, 255, 0.03) !important;
            border-right: 1px solid var(--card-border) !important;
        }

        /* Text color overrides */
        .stMarkdown, .stText, p, span, div {
            color: var(--text-primary) !important;
        }

        /* Metric styling */
        [data-testid="metric-container"] {
            background: var(--card-bg) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 10px !important;
            padding: 15px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        }

        [data-testid="metric-container"]:hover {
            transform: translateY(-2px) !important;
            border-color: var(--accent-color) !important;
            transition: all 0.2s ease !important;
        }

        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent-color), #45a049) !important;
            border: none !important;
            border-radius: 8px !important;
            color: white !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2) !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3) !important;
        }

        /* Input styling */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stSlider > div > div > div > div {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 8px !important;
            color: var(--text-primary) !important;
        }

        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus {
            border-color: var(--accent-color) !important;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
        }
        
        /* Enhanced Sidebar Styling */
        .css-1d391kg, .css-1cypcdb, .css-17eq0hr {
            background: rgba(255, 255, 255, 0.03) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        /* Sidebar headers */
        .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
            color: #4CAF50 !important;
            border-bottom: 1px solid rgba(76, 175, 80, 0.2) !important;
            padding-bottom: 10px !important;
            margin-bottom: 15px !important;
        }
        
        /* Sidebar selectbox styling */
        .css-1d391kg .stSelectbox > div > div {
            background: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 8px !important;
        }
        
        /* Sidebar slider styling */
        .css-1d391kg .stSlider {
            padding: 10px 0 !important;
        }
        
        .css-1d391kg .stSlider > div > div > div {
            background: rgba(76, 175, 80, 0.2) !important;
        }
        
        /* Sidebar text styling */
        .css-1d391kg .stMarkdown p {
            color: #e0e0e0 !important;
            font-size: 0.9rem !important;
        }
        
        /* Sidebar caption styling */
        .css-1d391kg .stCaption {
            color: #bbb !important;
            font-style: italic !important;
        }
        
        /* Enhanced Filter Panel Styling */
        .filter-section {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            margin-bottom: 20px !important;
        }
        
        .filter-section h3 {
            color: #4CAF50 !important;
            font-size: 1.1rem !important;
            margin-bottom: 15px !important;
            border-bottom: 1px solid rgba(76, 175, 80, 0.2) !important;
            padding-bottom: 8px !important;
        }
        
        /* Strategy mode buttons */
        .strategy-button {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 8px !important;
            padding: 10px 15px !important;
            margin: 5px !important;
            color: #e0e0e0 !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            text-align: center !important;
        }
        
        .strategy-button:hover {
            border-color: #4CAF50 !important;
            background: rgba(76, 175, 80, 0.1) !important;
        }
        
        .strategy-button.active {
            background: #4CAF50 !important;
            border-color: #4CAF50 !important;
            color: white !important;
        }
        
        /* Filter input styling */
        .stSlider > div > div > div > div > div {
            background: #4CAF50 !important;
        }
        
        .stSlider > div > div > div > div {
            background: rgba(76, 175, 80, 0.2) !important;
        }
        
        /* Selectbox custom styling */
        .stSelectbox > div > div > div {
            background: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            color: #e0e0e0 !important;
        }
        
        .results-container {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
            margin: 20px 0 !important;
        }
        
        .table-header {
            background: rgba(76, 175, 80, 0.1) !important;
            border-bottom: 1px solid rgba(76, 175, 80, 0.3) !important;
            padding: 15px 20px !important;
            margin-bottom: 0 !important;
        }
        
        .table-header h2 {
            color: #4CAF50 !important;
            font-size: 1.5rem !important;
            margin-bottom: 5px !important;
        }
        
        .table-header p {
            color: #bbb !important;
            margin: 0 !important;
            font-size: 0.9rem !important;
        }
        
        /* Status indicator styling */
        .status-excellent {
            background: #27ae60 !important;
            color: white !important;
            padding: 4px 8px !important;
            border-radius: 12px !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
        }
        
        .status-good {
            background: #f39c12 !important;
            color: white !important;
            padding: 4px 8px !important;
            border-radius: 12px !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
        }
        
        .status-caution {
            background: #e74c3c !important;
            color: white !important;
            padding: 4px 8px !important;
            border-radius: 12px !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
        }
        
        /* DataFrames styling */
        .stDataFrame {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
        }
        
        .stDataFrame table {
            background: transparent !important;
        }
        
        .stDataFrame th {
            background: rgba(76, 175, 80, 0.1) !important;
            color: #4CAF50 !important;
            font-weight: 600 !important;
            border-bottom: 2px solid rgba(76, 175, 80, 0.3) !important;
        }
        
        .stDataFrame td {
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            color: #e0e0e0 !important;
        }
        
        .stDataFrame tr:hover {
            background: rgba(76, 175, 80, 0.05) !important;
        }
        
        /* Performance metrics cards */
        .metrics-grid {
            display: grid !important;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)) !important;
            gap: 20px !important;
            margin: 30px 0 !important;
        }
        
        /* Alert panels */
        .alert-success {
            background: rgba(40, 167, 69, 0.1) !important;
            border: 1px solid rgba(40, 167, 69, 0.3) !important;
            border-radius: 8px !important;
            padding: 15px !important;
            margin: 20px 0 !important;
            color: #28a745 !important;
        }
        
        .alert-warning {
            background: rgba(255, 193, 7, 0.1) !important;
            border: 1px solid rgba(255, 193, 7, 0.3) !important;
            border-radius: 8px !important;
            padding: 15px !important;
            margin: 20px 0 !important;
            color: #ffc107 !important;
        }
        
        .alert-danger {
            background: rgba(220, 53, 69, 0.1) !important;
            border: 1px solid rgba(220, 53, 69, 0.3) !important;
            border-radius: 8px !important;
            padding: 15px !important;
            margin: 20px 0 !important;
            color: #dc3545 !important;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            text-align: center !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        }
        
        .metric-card:hover {
            transform: translateY(-3px) !important;
            border-color: #4CAF50 !important;
            box-shadow: 0 8px 24px rgba(76, 175, 80, 0.2) !important;
        }
        
        .metric-value {
            font-size: 2rem !important;
            font-weight: bold !important;
            color: #4CAF50 !important;
            margin-bottom: 5px !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        }
        
        .metric-label {
            color: #bbb !important;
            font-size: 0.9rem !important;
            font-weight: 400 !important;
        }
        
        .metric-delta {
            font-size: 0.8rem !important;
            margin-top: 5px !important;
        }
        
        .metric-delta.positive {
            color: #27ae60 !important;
        }
        
        .metric-delta.negative {
            color: #e74c3c !important;
        }
        
        /* Enhanced pagination */
        .pagination-container {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            padding: 15px !important;
            margin: 20px 0 !important;
            text-align: center !important;
        }
        
        .pagination-info {
            color: #4CAF50 !important;
            font-weight: 500 !important;
            font-size: 1rem !important;
        }
        
        /* Chart section styling */
        .chart-section {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 25px !important;
            margin-top: 30px !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
        }
        
        .chart-controls {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 8px !important;
            padding: 15px !important;
            margin-bottom: 20px !important;
        }
        
        /* Loading spinner */
        .loading-spinner {
            display: inline-block !important;
            width: 20px !important;
            height: 20px !important;
            border: 3px solid rgba(76, 175, 80, 0.3) !important;
            border-radius: 50% !important;
            border-top-color: #4CAF50 !important;
            animation: spin 1s ease-in-out infinite !important;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .metric-value {
                font-size: 1.5rem !important;
            }
            
            .table-header h2 {
                font-size: 1.2rem !important;
            }
            
            .metric-card {
                padding: 15px !important;
            }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
            }
            70% {
                box-shadow: 0 0 0 10px rgba(76, 175, 80, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
            }
        }
        
        /* Animated elements */
        .fade-in {
            animation: fadeInUp 0.6s ease-out;
        }
        
        .slide-in {
            animation: slideInRight 0.5s ease-out;
        }
        
        /* Enhanced button animations */
        .stButton > button {
            position: relative !important;
            overflow: hidden !important;
        }
        
        .stButton > button::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent) !important;
            transition: left 0.5s !important;
        }
        
        .stButton > button:hover::before {
            left: 100% !important;
        }
        
        /* Pulse animation for important elements */
        .pulse-success {
            animation: pulse 2s infinite;
        }
        
        /* Enhanced tooltips */
        .enhanced-tooltip {
            position: relative !important;
            cursor: help !important;
        }
        
        .enhanced-tooltip::after {
            content: attr(data-tooltip) !important;
            position: absolute !important;
            bottom: 125% !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            background: rgba(0, 0, 0, 0.9) !important;
            color: white !important;
            padding: 8px 12px !important;
            border-radius: 6px !important;
            font-size: 0.8rem !important;
            white-space: nowrap !important;
            opacity: 0 !important;
            visibility: hidden !important;
            transition: all 0.3s ease !important;
            z-index: 1000 !important;
        }
        
        .enhanced-tooltip::before {
            content: '' !important;
            position: absolute !important;
            bottom: 115% !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            border: 5px solid transparent !important;
            border-top-color: rgba(0, 0, 0, 0.9) !important;
            opacity: 0 !important;
            visibility: hidden !important;
            transition: all 0.3s ease !important;
        }
        
        .enhanced-tooltip:hover::after,
        .enhanced-tooltip:hover::before {
            opacity: 1 !important;
            visibility: visible !important;
        }
        
        /* Mobile Responsive Improvements */
        @media (max-width: 768px) {
            .stApp {
                padding: 10px !important;
            }
            
            .main .block-container {
                padding: 1rem !important;
                max-width: 100% !important;
            }
            
            h1 {
                font-size: 1.8rem !important;
                text-align: center !important;
            }
            
            .metric-card {
                padding: 15px 10px !important;
                margin-bottom: 10px !important;
            }
            
            .metric-value {
                font-size: 1.5rem !important;
            }
            
            .filter-section {
                padding: 15px !important;
                margin-bottom: 15px !important;
            }
            
            .table-header {
                padding: 10px 15px !important;
            }
            
            .table-header h2 {
                font-size: 1.2rem !important;
            }
            
            /* Stack columns on mobile */
            .stColumns {
                flex-direction: column !important;
            }
            
            .stColumn {
                width: 100% !important;
                margin-bottom: 10px !important;
            }
            
            /* Mobile-friendly buttons */
            .stButton > button {
                width: 100% !important;
                padding: 12px !important;
                font-size: 0.9rem !important;
            }
            
            /* Mobile pagination */
            .pagination-container {
                padding: 10px !important;
            }
            
            /* Mobile chart section */
            .chart-section {
                padding: 15px !important;
            }
            
            /* Hide some elements on mobile for cleaner look */
            .hide-mobile {
                display: none !important;
            }
        }
        
        @media (max-width: 480px) {
            .metric-value {
                font-size: 1.2rem !important;
            }
            
            .metric-label {
                font-size: 0.8rem !important;
            }
            
            .pagination-info {
                font-size: 0.8rem !important;
            }
        }
        
        /* Dark mode toggle styling */
        .theme-toggle {
            position: fixed !important;
            top: 20px !important;
            right: 20px !important;
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 20px !important;
            padding: 8px 16px !important;
            color: #e0e0e0 !important;
            cursor: pointer !important;
            backdrop-filter: blur(10px) !important;
            transition: all 0.3s ease !important;
            z-index: 1000 !important;
            font-size: 0.9rem !important;
        }
        
        .theme-toggle:hover {
            background: rgba(76, 175, 80, 0.2) !important;
            border-color: #4CAF50 !important;
            transform: translateY(-2px) !important;
        }
        
        /* Smooth scrolling */
        html {
            scroll-behavior: smooth !important;
        }
        
        /* Enhanced focus states for accessibility */
        button:focus,
        input:focus,
        select:focus {
            outline: 2px solid #4CAF50 !important;
            outline-offset: 2px !important;
        }
        
        .stApp {
            will-change: auto !important;
        }
        
        /* Lazy loading placeholders */
        .lazy-placeholder {
            background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%) !important;
            background-size: 200% 100% !important;
            animation: shimmer 1.5s infinite !important;
        }
        
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        
        /* Enhanced scrollbar */
        ::-webkit-scrollbar {
            width: 12px !important;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 6px !important;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(76, 175, 80, 0.3) !important;
            border-radius: 6px !important;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(76, 175, 80, 0.5) !important;
        }
        
        /* Performance indicators */
        .performance-badge {
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            background: rgba(76, 175, 80, 0.9) !important;
            color: white !important;
            padding: 8px 12px !important;
            border-radius: 20px !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
            z-index: 1000 !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        }
        
        /* Enhanced data freshness indicators */
        .data-fresh {
            color: #27ae60 !important;
            font-weight: 600 !important;
        }
        
        .data-stale {
            color: #e74c3c !important;
            font-weight: 600 !important;
        }
        
        .data-aging {
            color: #f39c12 !important;
            font-weight: 600 !important;
        }
        
        /* Advanced table row highlighting */
        .profit-excellent {
            background: linear-gradient(90deg, rgba(39, 174, 96, 0.1), rgba(39, 174, 96, 0.05)) !important;
            border-left: 3px solid #27ae60 !important;
        }
        
        .profit-good {
            background: linear-gradient(90deg, rgba(243, 156, 18, 0.1), rgba(243, 156, 18, 0.05)) !important;
            border-left: 3px solid #f39c12 !important;
        }
        
        .profit-caution {
            background: linear-gradient(90deg, rgba(231, 76, 60, 0.1), rgba(231, 76, 60, 0.05)) !important;
            border-left: 3px solid #e74c3c !important;
        }
        
        /* Advanced status badges */
        .status-badge {
            display: inline-block !important;
            padding: 4px 10px !important;
            border-radius: 12px !important;
            font-size: 0.75rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
        }
        
        .status-excellent {
            background: linear-gradient(135deg, #27ae60, #2ecc71) !important;
            color: white !important;
        }
        
        .status-good {
            background: linear-gradient(135deg, #f39c12, #e67e22) !important;
            color: white !important;
        }
        
        .status-caution {
            background: linear-gradient(135deg, #e74c3c, #c0392b) !important;
            color: white !important;
        }
        
        /* Quick action buttons */
        .quick-action {
            background: rgba(52, 152, 219, 0.1) !important;
            border: 1px solid rgba(52, 152, 219, 0.3) !important;
            color: #3498db !important;
            padding: 6px 12px !important;
            border-radius: 6px !important;
            font-size: 0.8rem !important;
            margin: 2px !important;
            transition: all 0.2s ease !important;
        }
        
        .quick-action:hover {
            background: rgba(52, 152, 219, 0.2) !important;
            border-color: #3498db !important;
            transform: translateY(-1px) !important;
        }

    </style>
    """, unsafe_allow_html=True)

def create_enhanced_header():
    """Create the enhanced header with status indicators"""

    # Get cache stats for status bar
    from cache_manager import cache_manager
    cache_stats = cache_manager.get_stats()

    # Calculate time since last update
    current_time = datetime.datetime.now()
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = current_time

    time_diff = current_time - st.session_state.last_update_time
    minutes_ago = int(time_diff.total_seconds() / 60)

    # Main header
    st.markdown("""
    <h1 style="color: #ffd700; font-size: 2.5rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);">
    💸 OSRS GE Flipping Assistant
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p style="color: #bbb; font-size: 1.1rem; margin-bottom: 20px;">
    Real-time Grand Exchange opportunity scanner with advanced analytics
    </p>
    """, unsafe_allow_html=True)

    # Status indicators using columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.success("✅ API Connected")

    with col2:
        st.info(f"📊 Cache Hit Rate: {cache_stats['hit_rate']:.1f}%")

    with col3:
        st.info(f"⏰ Last Update: {minutes_ago} min ago")

    with col4:
        alert_status = "🔔 Active" if not st.session_state.get('show_all_table', False) else "🚫 Disabled"
        if "Active" in alert_status:
            st.success(alert_status)
        else:
            st.warning(alert_status)

def create_table_header(total_items, avg_margin, avg_risk_util):
    """Create enhanced table header with summary info"""

    st.markdown("""
    <div class="results-container">
        <div class="table-header">
            <h2>🔍 Top Flip Opportunities</h2>
            <p>Real-time market analysis with risk assessment</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Items", total_items)

    with col2:
        st.metric("Avg Margin", f"{avg_margin:,.0f} gp")

    with col3:
        st.metric("Avg Risk Adj. Utility", f"{avg_risk_util:,.0f}")

    with col4:
        # Calculate safe items count
        safe_items = "📊 Loading..."
        st.metric("Analysis", safe_items)

def create_enhanced_metrics(df):
    """Create beautiful metrics cards with enhanced styling"""

    if df.empty:
        return

    # Calculate metrics
    total_items = len(df)
    avg_margin = df['Net Margin'].mean()
    max_margin = df['Net Margin'].max()
    avg_roi = df['ROI (%)'].mean()
    total_volume = df['1h Volume'].sum()

    # Calculate additional metrics
    safe_items = len(df[(df.get('Manipulation Score', 0) <= 3) & (df.get('Volatility Score', 0) <= 4)])
    high_risk_items = len(df[(df.get('Manipulation Score', 10) >= 7) | (df.get('Volatility Score', 10) >= 8)])

    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0;">
    """, unsafe_allow_html=True)

    # Create individual metric cards using columns
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_items}</div>
            <div class="metric-label">Total Opportunities</div>
            <div class="metric-delta positive">📊 Active</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_margin:,.0f}</div>
            <div class="metric-label">Avg Margin (gp)</div>
            <div class="metric-delta positive">💰 Profit</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_roi:.1f}%</div>
            <div class="metric-label">Avg ROI</div>
            <div class="metric-delta positive">📈 Returns</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{safe_items}</div>
            <div class="metric-label">Safe Items</div>
            <div class="metric-delta positive">🛡️ Low Risk</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_volume:,.0f}</div>
            <div class="metric-label">Total Volume/hr</div>
            <div class="metric-delta positive">🔄 Liquidity</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

def show_error_message(message, icon="❌", details=None):
    """Show a beautiful error message with optional details"""
    st.markdown(f"""
    <div style="
        background: rgba(220, 53, 69, 0.1);
        border: 1px solid rgba(220, 53, 69, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #dc3545;
        font-weight: 500;
    ">
        <div style="font-size: 1.1rem; margin-bottom: 5px;">
            {icon} {message}
        </div>
        {f'<div style="font-size: 0.9rem; color: #999; margin-top: 8px;">{details}</div>' if details else ''}
    </div>
    """, unsafe_allow_html=True)

def show_info_message(message, icon="ℹ️"):
    """Show a beautiful info message"""
    st.markdown(f"""
    <div style="
        background: rgba(52, 152, 219, 0.1);
        border: 1px solid rgba(52, 152, 219, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #3498db;
        font-weight: 500;
        text-align: center;
    ">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)

def create_performance_monitor():
    """Create a performance monitoring badge"""

    # Get current performance metrics
    from cache_manager import cache_manager
    cache_stats = cache_manager.get_stats()

    # Calculate performance score
    hit_rate = cache_stats.get('hit_rate', 0)
    if hit_rate >= 80:
        performance_status = "🚀 Excellent"
        performance_color = "#27ae60"
    elif hit_rate >= 60:
        performance_status = "⚡ Good"
        performance_color = "#f39c12"
    else:
        performance_status = "🐌 Slow"
        performance_color = "#e74c3c"

    st.markdown(f"""
    <div class="performance-badge" style="background: {performance_color};">
        {performance_status} ({hit_rate:.0f}%)
    </div>
    """, unsafe_allow_html=True)

def add_copy_functionality():
    """Add copy to clipboard functionality"""
    st.markdown("""
    <script>
        function copyItemData(itemName, buyPrice, sellPrice) {
            const copyText = itemName + ': Buy ' + buyPrice + ', Sell ' + sellPrice;
            navigator.clipboard.writeText(copyText).then(function() {
                alert('Copied: ' + copyText);
            });
        }
    </script>
    """, unsafe_allow_html=True)

def create_advanced_search_no_refresh():
    """Create advanced search with no page refresh"""

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    ">
        <h3 style="color: #4CAF50; margin-bottom: 15px;">🔍 Advanced Item Search</h3>

        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 15px;">
            <div>
                <input type="text" id="searchInput" placeholder="Enter item name, category, or ID..." style="
                    width: 100%;
                    padding: 10px 12px;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-size: 0.9rem;
                " oninput="filterResults()">
            </div>

            <div>
                <select id="categoryFilter" style="
                    width: 100%;
                    padding: 10px 12px;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-size: 0.9rem;
                " onchange="filterResults()">
                    <option value="">All Categories</option>
                    <option value="Raw Materials">Raw Materials</option>
                    <option value="Consumables">Consumables</option>
                    <option value="Runes & Ammo">Runes & Ammo</option>
                    <option value="Gear & Weapons">Gear & Weapons</option>
                    <option value="Other">Other</option>
                </select>
            </div>

            <div>
                <select id="sortOption" style="
                    width: 100%;
                    padding: 10px 12px;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-size: 0.9rem;
                " onchange="sortResults()">
                    <option value="profit">Profit Margin</option>
                    <option value="roi">ROI %</option>
                    <option value="volume">Volume</option>
                    <option value="risk">Risk Score</option>
                    <option value="name">Item Name</option>
                </select>
            </div>
        </div>
    </div>

    <script>
        function filterResults() {
            // This would filter your actual table rows
            console.log('Filtering results...');
            // Implementation depends on how your table is structured
        }

        function sortResults() {
            // This would sort your actual table
            console.log('Sorting results...');
            // Implementation depends on how your table is structured
        }
    </script>
    """, unsafe_allow_html=True)

def create_profit_calculator():
    """Create a profit calculator with zero page refreshes using JavaScript"""

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    ">
        <h3 style="color: #4CAF50; margin-bottom: 15px;">💰 Real-Time Profit Calculator</h3>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
            <div>
                <label style="color: #e0e0e0; font-size: 0.9rem; margin-bottom: 5px; display: block;">Buy Price (gp)</label>
                <input type="number" id="buyPrice" value="1000" min="1" style="
                    width: 100%;
                    padding: 8px 12px;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-size: 0.9rem;
                " oninput="calculateProfit()">
            </div>

            <div>
                <label style="color: #e0e0e0; font-size: 0.9rem; margin-bottom: 5px; display: block;">Sell Price (gp)</label>
                <input type="number" id="sellPrice" value="1100" min="1" style="
                    width: 100%;
                    padding: 8px 12px;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-size: 0.9rem;
                " oninput="calculateProfit()">
            </div>

            <div>
                <label style="color: #e0e0e0; font-size: 0.9rem; margin-bottom: 5px; display: block;">Quantity</label>
                <input type="number" id="quantity" value="100" min="1" style="
                    width: 100%;
                    padding: 8px 12px;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-size: 0.9rem;
                " oninput="calculateProfit()">
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0;">
            <div style="
                background: rgba(76, 175, 80, 0.1);
                border: 1px solid rgba(76, 175, 80, 0.3);
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: #4CAF50; font-size: 1.5rem; font-weight: bold;" id="netProfitPerItem">0 gp</div>
                <div style="color: #bbb; font-size: 0.9rem;">Net Profit/Item</div>
            </div>

            <div style="
                background: rgba(52, 152, 219, 0.1);
                border: 1px solid rgba(52, 152, 219, 0.3);
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: #3498db; font-size: 1.5rem; font-weight: bold;" id="totalProfit">0 gp</div>
                <div style="color: #bbb; font-size: 0.9rem;">Total Profit</div>
            </div>

            <div style="
                background: rgba(155, 89, 182, 0.1);
                border: 1px solid rgba(155, 89, 182, 0.3);
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: #9b59b6; font-size: 1.5rem; font-weight: bold;" id="roi">0%</div>
                <div style="color: #bbb; font-size: 0.9rem;">ROI</div>
            </div>

            <div style="
                background: rgba(241, 196, 15, 0.1);
                border: 1px solid rgba(241, 196, 15, 0.3);
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: #f1c40f; font-size: 1.5rem; font-weight: bold;" id="geTax">0 gp</div>
                <div style="color: #bbb; font-size: 0.9rem;">GE Tax</div>
            </div>
        </div>

        <div id="profitAssessment" style="
            text-align: center;
            padding: 10px;
            border-radius: 6px;
            margin-top: 15px;
            font-weight: 500;
        "></div>
    </div>

    <script>
        function calculateGETax(price) {
            // GE tax calculation: 2% capped at 5M
            const tax = Math.floor(price * 0.02);
            return Math.min(tax, 5000000);
        }

        function formatNumber(num) {
            return new Intl.NumberFormat().format(num);
        }

        function calculateProfit() {
            const buyPrice = parseInt(document.getElementById('buyPrice').value) || 0;
            const sellPrice = parseInt(document.getElementById('sellPrice').value) || 0;
            const quantity = parseInt(document.getElementById('quantity').value) || 0;

            if (buyPrice <= 0 || sellPrice <= 0 || quantity <= 0) {
                // Reset displays if invalid input
                document.getElementById('netProfitPerItem').textContent = '0 gp';
                document.getElementById('totalProfit').textContent = '0 gp';
                document.getElementById('roi').textContent = '0%';
                document.getElementById('geTax').textContent = '0 gp';
                document.getElementById('profitAssessment').innerHTML = '';
                return;
            }

            const geTax = calculateGETax(sellPrice);
            const netProfitPerItem = sellPrice - buyPrice - geTax;
            const totalProfit = netProfitPerItem * quantity;
            const roi = buyPrice > 0 ? (netProfitPerItem / buyPrice) * 100 : 0;

            // Update displays with instant formatting
            document.getElementById('netProfitPerItem').textContent = formatNumber(netProfitPerItem) + ' gp';
            document.getElementById('totalProfit').textContent = formatNumber(totalProfit) + ' gp';
            document.getElementById('roi').textContent = roi.toFixed(1) + '%';
            document.getElementById('geTax').textContent = formatNumber(geTax) + ' gp';

            // Update profit assessment
            const assessmentDiv = document.getElementById('profitAssessment');
            if (roi >= 5) {
                assessmentDiv.innerHTML = '🟢 <strong>Excellent opportunity!</strong> ' + roi.toFixed(1) + '% ROI';
                assessmentDiv.style.background = 'rgba(40, 167, 69, 0.1)';
                assessmentDiv.style.border = '1px solid rgba(40, 167, 69, 0.3)';
                assessmentDiv.style.color = '#28a745';
            } else if (roi >= 2) {
                assessmentDiv.innerHTML = '🟡 <strong>Good opportunity!</strong> ' + roi.toFixed(1) + '% ROI';
                assessmentDiv.style.background = 'rgba(255, 193, 7, 0.1)';
                assessmentDiv.style.border = '1px solid rgba(255, 193, 7, 0.3)';
                assessmentDiv.style.color = '#ffc107';
            } else if (roi >= 0) {
                assessmentDiv.innerHTML = '🔴 <strong>Low profit margin</strong> - ' + roi.toFixed(1) + '% ROI';
                assessmentDiv.style.background = 'rgba(220, 53, 69, 0.1)';
                assessmentDiv.style.border = '1px solid rgba(220, 53, 69, 0.3)';
                assessmentDiv.style.color = '#dc3545';
            } else {
                assessmentDiv.innerHTML = '💸 <strong>Loss!</strong> You would lose ' + formatNumber(Math.abs(netProfitPerItem)) + ' gp per item';
                assessmentDiv.style.background = 'rgba(220, 53, 69, 0.2)';
                assessmentDiv.style.border = '1px solid rgba(220, 53, 69, 0.5)';
                assessmentDiv.style.color = '#dc3545';
            }
        }

        // Calculate on page load
        calculateProfit();

        // Add input styling
        document.querySelectorAll('input[type="number"]').forEach(input => {
            input.addEventListener('focus', function() {
                this.style.borderColor = '#4CAF50';
                this.style.boxShadow = '0 0 0 2px rgba(76, 175, 80, 0.2)';
            });

            input.addEventListener('blur', function() {
                this.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                this.style.boxShadow = 'none';
            });
        });
    </script>
    """, unsafe_allow_html=True)

def create_watchlist_manager():
    """Create advanced watchlist management"""

    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    ">
        <h3 style="color: #4CAF50; margin-bottom: 15px;">⭐ Watchlist Manager</h3>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.watchlist:
        st.write(f"**📋 Watching {len(st.session_state.watchlist)} items:**")

        # Display watchlist in a nice format
        for i, item in enumerate(st.session_state.watchlist):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {item}")
            with col2:
                if st.button("❌", key=f"remove_watch_{i}", help=f"Remove {item}"):
                    st.session_state.watchlist.remove(item)
                    st.rerun()

        # Clear all button
        if st.button("🗑️ Clear All Watchlist", type="secondary"):
            st.session_state.watchlist = []
            show_success_message("Watchlist cleared!")
            st.rerun()
    else:
        st.info("📝 No items in watchlist. Click ⭐ Watch buttons to add items!")

    return st.session_state.watchlist

def create_export_options(df):
    """Create advanced export options"""

    if df.empty:
        return

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    ">
        <h3 style="color: #4CAF50; margin-bottom: 15px;">📥 Export Options</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # CSV Export
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📊 Export CSV",
            data=csv_data,
            file_name=f"osrs_opportunities_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            help="Download as Excel-compatible CSV",
            use_container_width=True
        )

    with col2:
        # JSON Export
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            label="📋 Export JSON",
            data=json_data,
            file_name=f"osrs_opportunities_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            help="Download as JSON for API use",
            use_container_width=True
        )

    with col3:
        # Top 10 Export
        top_10 = df.head(10)
        top_10_csv = top_10.to_csv(index=False)
        st.download_button(
            label="🏆 Top 10 CSV",
            data=top_10_csv,
            file_name=f"osrs_top_10_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            help="Download top 10 opportunities",
            use_container_width=True
        )

    with col4:
        # Watchlist Export
        if st.session_state.get('watchlist'):
            watchlist_df = df[df['Item'].isin(st.session_state.watchlist)]
            if not watchlist_df.empty:
                watchlist_csv = watchlist_df.to_csv(index=False)
                st.download_button(
                    label="⭐ Watchlist CSV",
                    data=watchlist_csv,
                    file_name=f"osrs_watchlist_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    help="Download watchlist items",
                    use_container_width=True
                )
            else:
                st.button("⭐ Watchlist CSV", disabled=True, help="No watchlist items in current results")
        else:
            st.button("⭐ Watchlist CSV", disabled=True, help="Watchlist is empty")

def show_success_message(message, icon="✅"):
    """Show a beautiful success message"""
    st.markdown(f"""
    <div style="
        background: rgba(40, 167, 69, 0.1);
        border: 1px solid rgba(40, 167, 69, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #28a745;
        text-align: center;
        font-weight: 500;
    ">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)

def show_warning_message(message, icon="⚠️"):
    """Show a beautiful warning message"""
    st.markdown(f"""
    <div style="
        background: rgba(255, 193, 7, 0.1);
        border: 1px solid rgba(255, 193, 7, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #ffc107;
        text-align: center;
        font-weight: 500;
    ">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)

# Streamlit UI
def streamlit_dashboard():
    st.set_page_config(
        page_title="💸 OSRS GE Flipping Assistant",
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon="💰"
    )

    # Inject our custom CSS
    inject_custom_css()

    # Add performance monitoring
    create_performance_monitor()

    # Add copy functionality
    add_copy_functionality()

    # Add theme toggle and advanced interactions
    st.markdown("""
        <div class="theme-toggle" onclick="toggleTheme()">
            🌙 Dark Mode
        </div>

        <script>
            function toggleTheme() {
                // Add theme toggle functionality
                const app = document.querySelector('.stApp');
                if (app.style.filter === 'invert(1) hue-rotate(180deg)') {
                    app.style.filter = '';
                    document.querySelector('.theme-toggle').innerHTML = '🌙 Dark Mode';
                } else {
                    app.style.filter = 'invert(1) hue-rotate(180deg)';
                    document.querySelector('.theme-toggle').innerHTML = '☀️ Light Mode';
                }
            }

            // Add smooth animations to elements as they appear
            function addAnimations() {
                const elements = document.querySelectorAll('.metric-card, .filter-section, .results-container');
                elements.forEach((el, index) => {
                    el.style.animationDelay = (index * 0.1) + 's';
                    el.classList.add('fade-in');
                });
            }

            // Run animations when page loads
            setTimeout(addAnimations, 100);

            // Add keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                // Ctrl+R to refresh
                if (e.ctrlKey && e.key === 'r') {
                    e.preventDefault();
                    const refreshBtn = document.querySelector('[data-testid="stButton"] button');
                    if (refreshBtn && refreshBtn.textContent.includes('Refresh')) {
                        refreshBtn.click();
                    }
                }

                // Ctrl+/ to focus search
                if (e.ctrlKey && e.key === '/') {
                    e.preventDefault();
                    const searchInput = document.querySelector('input[placeholder*="Search"], input[placeholder*="search"]');
                    if (searchInput) {
                        searchInput.focus();
                    }
                }
            });
        </script>
        """, unsafe_allow_html=True)

    # Initialize session state
    if 'presets' not in st.session_state:
        st.session_state.presets = {}

    if 'season_th' not in st.session_state:
        st.session_state.season_th = 0.0
    if 'manipulation_th' not in st.session_state:
        st.session_state.manipulation_th = 7
    if 'volatility_th' not in st.session_state:
        st.session_state.volatility_th = 8
    if 'show_chart_page' not in st.session_state:
        st.session_state.show_chart_page = False
    if 'selected_item' not in st.session_state:
        st.session_state.selected_item = None

    st.session_state['min_margin'] = MIN_MARGIN
    st.session_state['min_volume'] = MIN_VOLUME
    st.session_state['min_utility'] = MIN_UTILITY

    # Enhanced multi-page navigation with breadcrumbs
    pages = {
        "🔍 Opportunities": "opportunities",
        "📊 Item Charts": "charts"
    }

    if 'page' not in st.session_state:
        st.session_state.page = 'opportunities'

    # Breadcrumb navigation
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # Show current location
        if st.session_state.page == 'opportunities':
            st.markdown("📍 **Home** > Opportunities")
        elif st.session_state.page == 'charts':
            selected_item = st.session_state.get('selected_item', 'Unknown Item')
            st.markdown(f"📍 **Home** > [Opportunities](?) > Charts > {selected_item}")

    with col2:
        # Page selector (but less prominent)
        selected_page = st.selectbox("Go to:", list(pages.keys()),
                                     index=list(pages.values()).index(st.session_state.page),
                                     key="main_nav")
        if pages[selected_page] != st.session_state.page:
            st.session_state.page = pages[selected_page]
            st.rerun()

    with col3:
        # Quick actions
        if st.session_state.page == 'charts':
            if st.button("⬅️ Back to Opportunities", type="secondary"):
                st.session_state.page = 'opportunities'
                st.rerun()

    # Page content with dynamic titles
    if st.session_state.page == 'opportunities':
        create_enhanced_header()
        show_opportunities_page()
    elif st.session_state.page == 'charts':
        selected_item = st.session_state.get('selected_item', 'No Item Selected')
        # Use enhanced header for charts page too
        create_enhanced_header()
        if selected_item:
            st.markdown(f"""
            <h2 style="color: #4CAF50; margin-top: 20px; font-weight: 600;">
            📊 {selected_item} - Price Chart Analysis
            </h2>
            """, unsafe_allow_html=True)
        show_charts_page()

if __name__ == '__main__':
    streamlit_dashboard()
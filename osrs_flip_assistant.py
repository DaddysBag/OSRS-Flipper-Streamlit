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
    st.session_state['min_margin'] = MIN_MARGIN

    MIN_VOLUME = st.sidebar.slider("Min Volume/hr", 0, 20000, v, 100)
    st.session_state['min_volume'] = MIN_VOLUME

    MIN_UTILITY = st.sidebar.slider("Min Utility", 0, 50000, u, 500)
    st.session_state['min_utility'] = MIN_UTILITY

    st.session_state['season_th'] = st.sidebar.slider("Min Season Ratio", 0.0, 5.0,
                                                      st.session_state.get('season_th', 0.0), 0.1)

    st.sidebar.subheader("🔬 Advanced Risk Filters")
    st.session_state['manipulation_th'] = st.sidebar.slider(
        "Max Manipulation Score", 0, 10,
        st.session_state.get('manipulation_th', 7), 1,
        help="Lower = stricter filtering of potentially manipulated items"
    )
    st.session_state['volatility_th'] = st.sidebar.slider(
        "Max Volatility Score", 0, 10,
        st.session_state.get('volatility_th', 8), 1,
        help="Lower = stricter filtering of volatile items"
    )

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

                # High risk factors take priority
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
            else:
                # Fall back to original logic if enhanced columns don't exist
                if data_age > 5:
                    return "🔴"
                elif data_age > 2:
                    return "🟡"
                elif roi >= 5 and volume >= 1000:
                    return "🟢"
                elif roi >= 2 and volume >= 500:
                    return "🟡"
                else:
                    return "🔴"

        # Apply the enhanced color coding
        display_df['Status'] = display_df.apply(get_enhanced_color_code, axis=1)

        # Get buy limits for display
        limits = get_buy_limits()

        # Create formatted columns that preserve numerical sorting
        # Keep original numerical columns and add formatted display columns
        display_df['Buy Price (formatted)'] = display_df['Buy Price'].apply(lambda x: f"{x:,}")
        display_df['Sell Price (formatted)'] = display_df['Sell Price'].apply(lambda x: f"{x:,}")
        display_df['Net Margin (formatted)'] = display_df['Net Margin'].apply(lambda x: f"{x:,}")
        display_df['ROI (formatted)'] = display_df['ROI (%)'].apply(lambda x: f"{x:.1f}%")
        display_df['Volume (formatted)'] = display_df['1h Volume'].apply(lambda x: f"{x:,}")

        # Add additional calculated columns
        display_df['Approx. Offer Price'] = display_df.apply(
            lambda row: f"{row['Buy Price']:,} ({row['Low Age (min)']:.1f}m ago)",
            axis=1)
        display_df['Approx. Sell Price'] = display_df.apply(
            lambda row: f"{row['Sell Price']:,} ({row['High Age (min)']:.1f}m ago)",
            axis=1)
        display_df['Tax'] = display_df['Sell Price'].apply(lambda x: f"{calculate_ge_tax(x):,}")
        display_df['GE Limit'] = display_df['Item'].apply(
            lambda x: f"{limits.get(x, 'N/A'):,}" if limits.get(x) else "N/A")
        display_df['Buy/Sell Ratio'] = display_df.apply(
            lambda row: f"{((row['Sell Price'] - row['Buy Price']) / row['Buy Price'] * 100):+.2f}%",
            axis=1
        )

        # Add Chart column before creating display dataframe
        display_df['Chart'] = display_df['Item'].apply(lambda x: f"📊 View")

        # Select columns for display - use original numerical columns for sorting
        columns_to_display = [
            'Status',
            'Item',
            'Chart',  # ← NEW: Add Chart column
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
            'Buy/Sell Ratio',
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

        # Display with proper numerical sorting
        st.dataframe(
            final_display_df,
            use_container_width=True,
            key="properly_sorted_flip_table",
            height=600,
            hide_index=True,
            column_config=column_config
        )

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

        # Portfolio optimization section
        st.subheader("📈 Portfolio Optimization")

        with st.expander("💼 Portfolio Analysis"):
            # Allow user to select items for portfolio analysis
            selected_items = st.multiselect(
                "Select items for portfolio analysis:",
                options=df['Item'].tolist(),
                default=df.head(min(10, len(df)))['Item'].tolist() if not df.empty else []
            )

            if selected_items:
                portfolio_df = df[df['Item'].isin(selected_items)]

                # Calculate portfolio metrics
                total_capital = portfolio_df[
                    'Capital Required'].sum() if 'Capital Required' in portfolio_df.columns else 0
                total_margin = portfolio_df['Net Margin'].sum()
                avg_risk = portfolio_df['Risk Ratio'].mean() if 'Risk Ratio' in portfolio_df.columns else 0

                # Diversification score
                categories = portfolio_df['Category'].value_counts()
                diversification_score = min(10, len(categories) * 2)

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Portfolio Metrics:**")
                    st.metric("Total Items", len(portfolio_df))
                    st.metric("Total Potential Margin", f"{total_margin:,.0f} gp")
                    st.metric("Diversification Score", f"{diversification_score}/10")

                    if total_capital > 0:
                        st.metric("Total Capital Required", f"{total_capital:,.0f} gp")
                        st.metric("Average Risk Ratio", f"{avg_risk:.2%}")

                with col2:
                    st.write("**Category Breakdown:**")
                    category_counts = portfolio_df['Category'].value_counts()
                    st.bar_chart(category_counts)

                    # Risk distribution
                    if 'Manipulation Risk' in portfolio_df.columns:
                        st.write("**Risk Distribution:**")
                        risk_counts = portfolio_df['Manipulation Risk'].value_counts()
                        for risk, count in risk_counts.items():
                            st.write(f"• {risk}: {count} items")

        # Enhanced risk analysis section
        st.subheader("⚠️ Risk Analysis")

        col1, col2 = st.columns(2)

        with col1:
            if 'Manipulation Risk' in df.columns:
                st.write("**Manipulation Risk Distribution:**")
                manip_counts = df['Manipulation Risk'].value_counts()
                st.bar_chart(manip_counts)
            else:
                st.write("**Traditional Risk Factors:**")
                high_margin = len(df[df['Net Margin'] > df['Net Margin'].quantile(0.8)])
                high_volume = len(df[df['1h Volume'] > df['1h Volume'].quantile(0.8)])
                st.write(f"• High Margin Items: {high_margin}")
                st.write(f"• High Volume Items: {high_volume}")

        with col2:
            if 'Volatility Level' in df.columns:
                st.write("**Volatility Distribution:**")
                vol_counts = df['Volatility Level'].value_counts()
                st.bar_chart(vol_counts)
            else:
                st.write("**Data Freshness:**")
                fresh_data = len(df[df['Data Age (min)'] <= 2])
                aging_data = len(df[(df['Data Age (min)'] > 2) & (df['Data Age (min)'] <= 5)])
                old_data = len(df[df['Data Age (min)'] > 5])
                st.write(f"• Fresh Data (<2m): {fresh_data}")
                st.write(f"• Aging Data (2-5m): {aging_data}")
                st.write(f"• Old Data (>5m): {old_data}")

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
                    filtered_display_df['Approx. Offer Price'] = filtered_display_df['Buy Price'].apply(
                        lambda x: f"{x:,}")
                    filtered_display_df['Approx. Sell Price'] = filtered_display_df['Sell Price'].apply(
                        lambda x: f"{x:,}")
                    filtered_display_df['Tax'] = filtered_display_df['Sell Price'].apply(
                        lambda x: f"{calculate_ge_tax(x):,}")
                    filtered_display_df['Approx. Profit (gp)'] = filtered_display_df['Net Margin'].apply(
                        lambda x: f"{x:,}")
                    filtered_display_df['ROI%'] = filtered_display_df['ROI (%)'].apply(lambda x: f"{x:.1f}%")
                    filtered_display_df['Buying Quantity (per hour)'] = filtered_display_df['1h Volume'].apply(
                        lambda x: f"{x:,}")
                    filtered_display_df['Selling Quantity (per hour)'] = filtered_display_df['1h Volume'].apply(
                        lambda x: f"{x:,}")
                    filtered_display_df['GE Limit'] = filtered_display_df['Item'].apply(
                        lambda x: f"{limits.get(x, 'N/A'):,}" if limits.get(x) else "N/A")
                    filtered_display_df['Buy/Sell Ratio'] = filtered_display_df.apply(
                        lambda row: f"{((row['Sell Price'] - row['Buy Price']) / row['Buy Price'] * 100):+.2f}%",
                        axis=1
                    )

                    # Only keep the columns that actually exist
                    available = [c for c in columns_to_display if c in filtered_display_df.columns]
                    missing = [c for c in columns_to_display if c not in filtered_display_df.columns]

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
        enhanced_csv['Buy_Sell_Ratio'] = (
                    (enhanced_csv['Sell Price'] - enhanced_csv['Buy Price']) / enhanced_csv['Buy Price'] * 100).round(2)

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
                                st.success(
                                    f"🏆 Strongest correlation: **{strongest['Item A']}** ↔ **{strongest['Item B']}** ({strongest['Correlation']})")
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
                                                st.warning(
                                                    "API returned empty data - this item may not have recent trading activity")
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
            st.info(f"**Active Alerts:** {len(get_alert_history())}")

        with col2:
            st.info(f"**Cooldown:** 3 minutes")

        with col3:
            alert_status = "🚫 Disabled" if show_all or len(df) > 5 else "✅ Active"
            st.info(f"**Status:** {alert_status}")

        with col4:
            if st.button("🔄 Clear Alert History"):
                clear_alert_history()
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

def show_charts_page():
    st.write("Charts page - coming next!")

# Streamlit UI
def streamlit_dashboard():

    st.set_page_config(page_title="OSRS Flip Assistant", layout="wide")

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

    # Multi-page navigation
    pages = {
        "🔍 Opportunities": "opportunities",
        "📊 Item Charts": "charts"
    }

    if 'page' not in st.session_state:
        st.session_state.page = 'opportunities'

    selected_page = st.selectbox("Navigate to:", list(pages.keys()),
                                 index=list(pages.values()).index(st.session_state.page))
    st.session_state.page = pages[selected_page]

    if st.session_state.page == 'opportunities':
        st.title("💸 OSRS GE Flipping Assistant")
        show_opportunities_page()
    elif st.session_state.page == 'charts':
        st.title("📊 Detailed Item Charts")
        show_charts_page()

if __name__ == '__main__':
    streamlit_dashboard()
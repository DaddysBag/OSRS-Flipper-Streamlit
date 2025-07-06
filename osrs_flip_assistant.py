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
import sys
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

from src.styles.main_styles import inject_modern_osrs_styles, inject_interactive_javascript
from src.components.header import create_enhanced_header, create_navigation, create_page_title, create_performance_badge
from src.components.sidebar import create_complete_sidebar
from src.components.data_loader import load_flip_data, create_debug_section
from src.components.results_table import display_paginated_table
from src.components.modern_table import create_modern_results_table
from src.components.performance_metrics import create_performance_badge_advanced

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

def show_opportunities_page():
    """Opportunities page - now handled by dedicated page controller"""
    from src.pages.opportunities_page import show_opportunities_page as opportunities_controller
    opportunities_controller()

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
    inject_modern_osrs_styles()
    inject_interactive_javascript()

    try:
        from src.utils.mobile_utils import inject_mobile_detection, inject_mobile_styles
        inject_mobile_detection()
        inject_mobile_styles()
    except ImportError:
        # Mobile utils not available yet - continue without them
        pass

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
    """Create a profit calculator with real-time updates using Streamlit widgets"""

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    ">
        <h3 style="color: #4CAF50; margin-bottom: 15px;">💰 Real-Time Profit Calculator</h3>
    </div>
    """, unsafe_allow_html=True)

    # Use Streamlit widgets but make them update in real-time
    col1, col2, col3 = st.columns(3)

    with col1:
        buy_price = st.number_input("Buy Price (gp)", min_value=1, value=1000, step=1, key="calc_buy")

    with col2:
        sell_price = st.number_input("Sell Price (gp)", min_value=1, value=1100, step=1, key="calc_sell")

    with col3:
        quantity = st.number_input("Quantity", min_value=1, value=100, step=1, key="calc_qty")

    # Calculate automatically whenever inputs change
    from utils import calculate_ge_tax

    tax = calculate_ge_tax(sell_price)
    net_profit_per_item = sell_price - buy_price - tax
    total_profit = net_profit_per_item * quantity
    roi = (net_profit_per_item / buy_price) * 100 if buy_price > 0 else 0

    # Display results with enhanced styling
    st.markdown("**💰 Results:**")
    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.metric("Net Profit/Item", f"{net_profit_per_item:,} gp")
    with col_b:
        st.metric("Total Profit", f"{total_profit:,} gp")
    with col_c:
        st.metric("ROI", f"{roi:.1f}%")
    with col_d:
        st.metric("GE Tax", f"{tax:,} gp")

    # Enhanced profit assessment with custom styling
    if roi >= 5:
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
            🟢 <strong>Excellent opportunity!</strong> {roi:.1f}% ROI
        </div>
        """, unsafe_allow_html=True)
    elif roi >= 2:
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
            🟡 <strong>Good opportunity!</strong> {roi:.1f}% ROI
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="
            background: rgba(220, 53, 69, 0.1);
            border: 1px solid rgba(220, 53, 69, 0.3);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            color: #dc3545;
            text-align: center;
            font-weight: 500;
        ">
            🔴 <strong>Low profit margin</strong> - {roi:.1f}% ROI
        </div>
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
    # Add these new imports after your existing imports
    from src.components.tools import (
        create_profit_calculator,
        create_export_options,
        create_watchlist_manager,
        create_quick_chart_access
    )
    from src.components.alerts_metrics import (
        create_performance_metrics,
        create_alert_status_display,
        display_watchlist_status,
        create_market_insights
    )
    from src.pages.charts_page import show_charts_page

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

    # Navigation
    create_navigation()

    # Page content with dynamic titles
    if st.session_state.page == 'opportunities':
        create_enhanced_header()
        create_performance_badge_advanced()
        show_opportunities_page()
    elif st.session_state.page == 'charts':
        selected_item = st.session_state.get('selected_item', 'No Item Selected')
        create_enhanced_header()
        create_performance_badge_advanced()
        create_page_title('charts', selected_item)
        # Use the new dedicated charts page component
        from src.pages.charts_page import show_charts_page
        show_charts_page()

if __name__ == '__main__':
    streamlit_dashboard()
"""
Charts Page Component
Dedicated page for item chart analysis
"""

import streamlit as st
import requests
from data_fetchers import get_item_mapping, get_timeseries_custom
from charts import create_interactive_chart
from utils import calculate_ge_tax


def show_charts_page():
    """Enhanced charts page with navigation and item analysis"""

    # Check if we have a selected item
    selected_item = st.session_state.get('selected_item', None)

    if not selected_item:
        display_no_item_selected()
        return

    # Item is selected - show chart interface
    display_chart_interface(selected_item)


def display_no_item_selected():
    """Display interface when no item is selected"""

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


def display_chart_interface(selected_item):
    """Display the main chart interface for the selected item"""

    st.success(f"📈 Analyzing: **{selected_item}**")

    # Navigation and controls
    display_chart_controls(selected_item)

    # Get item data and display chart
    try:
        display_item_chart(selected_item)
    except Exception as e:
        st.error(f"❌ Error loading chart: {e}")
        display_chart_debug_info(selected_item)


def display_chart_controls(selected_item):
    """Display chart navigation and control buttons"""

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

    return time_period, chart_type


def display_item_chart(selected_item):
    """Load and display the chart for the selected item"""

    # Get item mappings
    id2name, name2id = get_item_mapping()

    if selected_item not in name2id:
        st.error(f"❌ Item '{selected_item}' not found in database")
        return

    item_id = name2id[selected_item]

    # Map time periods to timestep values
    time_period = st.session_state.get('chart_time_period', 'Week')
    time_mapping = {
        "Day": "5m",
        "Week": "1h",
        "Month": "6h",
        "Year": "24h"
    }
    timestep = time_mapping[time_period]

    # Load chart data
    with st.spinner(f"Loading {time_period.lower()} data for {selected_item}..."):
        ts = get_timeseries_custom(item_id, timestep)

    if ts is None or ts.empty:
        display_no_chart_data(selected_item, item_id, timestep, time_period)
        return

    # Success - display the chart
    st.success(f"✅ Loaded {len(ts)} data points for {time_period.lower()} view")

    # Chart options
    display_chart_options()

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
    create_interactive_chart(
        ts,
        item_name=selected_item,
        width=st.session_state.get('chart_width', 1000),
        height=st.session_state.get('chart_height', 600),
        show_time_controls=True,
        current_timestep=current_timestep
    )

    # Chart analysis
    display_chart_analysis(ts, selected_item, time_period)


def display_chart_options():
    """Display chart customization options"""

    with st.expander("🎨 Chart Settings"):
        col1, col2 = st.columns(2)
        with col1:
            chart_height = st.slider("Chart Height", 400, 800, 600, key="chart_height")
            show_volume = st.checkbox("Show Volume", value=True, key="chart_show_volume")
        with col2:
            chart_width = st.slider("Chart Width", 800, 1400, 1000, key="chart_width")
            show_trend = st.checkbox("Show Trend Line", value=True, key="chart_show_trend")


def display_no_chart_data(selected_item, item_id, timestep, time_period):
    """Display message when no chart data is available"""

    st.error(f"❌ No chart data available for {selected_item}")
    display_chart_debug_info(selected_item, item_id, timestep, time_period)


def display_chart_debug_info(selected_item, item_id=None, timestep=None, time_period=None):
    """Display debug information for chart issues"""

    with st.expander("🔧 Debug Information"):
        st.write(f"**Item:** {selected_item}")
        if item_id:
            st.write(f"**Item ID:** {item_id}")
        if time_period:
            st.write(f"**Time Period:** {time_period}")
        if timestep:
            st.write(f"**Timestep:** {timestep}")

        # Test API manually if we have the info
        if item_id and timestep:
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


def display_chart_analysis(ts, item_name, time_period):
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
    display_trend_analysis(ts, time_period)

    # Trading opportunities
    display_trading_insights(ts, item_name)


def display_trend_analysis(ts, time_period):
    """Display price trend analysis"""

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


def display_trading_insights(ts, item_name):
    """Display trading insights and recommendations"""

    st.subheader("💡 Trading Insights")

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
        avg_volume = ts['volume'].mean()
        vol_trend = "📈 Increasing" if ts['volume'].iloc[-1] > avg_volume else "📉 Decreasing"
        st.info(f"**Volume Trend:** {vol_trend}")

        # Best trading times
        if len(ts) > 24:  # Only if we have enough data
            hourly_vol = ts.groupby(ts['timestamp'].dt.hour)['volume'].mean()
            best_hour = hourly_vol.idxmax() if not hourly_vol.empty else "Unknown"
            st.info(f"**Peak Trading Hour:** {best_hour}:00")

    with col3:
        # Risk assessment
        volatility = (ts['high'].std() / ts['high'].mean()) * 100
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
"""
Alerts and Metrics Component
Handles Discord alerts status and performance metrics display
"""

import streamlit as st
import pandas as pd
import datetime
from alerts import get_alert_history, clear_alert_history


def create_performance_metrics(df):
    """Display performance metrics in a clean layout"""

    if df.empty:
        return

    st.subheader("📊 Performance Metrics")

    # Calculate metrics
    total_items = len(df)
    avg_margin = df['Net Margin'].mean()
    max_margin = df['Net Margin'].max()
    avg_roi = df['ROI (%)'].mean()
    total_volume = df['1h Volume'].sum()

    # Calculate additional metrics if columns exist
    safe_items = 0
    high_risk_items = 0
    total_capital = 0

    if 'Manipulation Score' in df.columns and 'Volatility Score' in df.columns:
        safe_items = len(df[(df['Manipulation Score'] <= 3) & (df['Volatility Score'] <= 4)])
        high_risk_items = len(df[(df['Manipulation Score'] >= 7) | (df['Volatility Score'] >= 8)])

    if 'Capital Required' in df.columns:
        total_capital = df['Capital Required'].sum()

    # Display metrics in columns
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Items", total_items)

    with col2:
        st.metric("Avg Margin", f"{avg_margin:,.0f} gp")

    with col3:
        st.metric("Avg ROI", f"{avg_roi:.1f}%")

    with col4:
        st.metric("Total Volume", f"{total_volume:,.0f}")

    with col5:
        if safe_items > 0:
            st.metric("Safe Items", f"{safe_items}")
        else:
            st.metric("Max Margin", f"{max_margin:,.0f} gp")

    # Additional metrics row
    if safe_items > 0 or high_risk_items > 0 or total_capital > 0:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if safe_items > 0:
                st.metric("Low Risk Items", safe_items, delta="🛡️ Safe")

        with col2:
            if high_risk_items > 0:
                st.metric("High Risk Items", high_risk_items, delta="⚠️ Risky")

        with col3:
            if total_capital > 0:
                st.metric("Total Capital Req.", f"{total_capital:,.0f} gp")

        with col4:
            # Profit efficiency metric
            efficiency = (avg_margin * total_items) / total_volume if total_volume > 0 else 0
            st.metric("Profit Efficiency", f"{efficiency:.2f}")


def create_alert_status_display(df, show_all):
    """Display Discord alert status and management"""

    st.markdown("""
    <div style="background: rgba(40, 167, 69, 0.1); border: 1px solid rgba(40, 167, 69, 0.3);
                border-radius: 8px; padding: 20px; margin: 20px 0;">
    """, unsafe_allow_html=True)

    st.markdown("### 🔔 Discord Alert Status")

    # Alert status metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        active_alerts = len(get_alert_history())
        st.info(f"**Active Alerts:** {active_alerts}")

    with col2:
        st.info(f"**Cooldown:** 3 minutes")

    with col3:
        alert_status = "🚫 Disabled" if show_all or len(df) > 5 else "✅ Active"
        st.info(f"**Status:** {alert_status}")

    with col4:
        if st.button("🔄 Clear Alert History"):
            clear_alert_history()
            show_success_message("Alert history cleared!", "🗑️")

    st.markdown("</div>", unsafe_allow_html=True)

    # Alert conditions explanation
    if show_all or len(df) > 5:
        st.markdown("""
        <div style="background: rgba(255, 193, 7, 0.1); border: 1px solid rgba(255, 193, 7, 0.3);
                    border-radius: 8px; padding: 15px; margin: 10px 0; color: #ffc107;">
        <strong>🚫 Discord Alerts Disabled</strong><br>
        • Alerts are disabled when "Show All" is enabled<br>
        • Alerts are disabled when showing more than 5 items<br>
        • This prevents spam when displaying large datasets
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(40, 167, 69, 0.1); border: 1px solid rgba(40, 167, 69, 0.3);
                    border-radius: 8px; padding: 15px; margin: 10px 0; color: #28a745;">
        <strong>✅ Discord Alerts Active</strong><br>
        • Will alert on exceptional opportunities (2x minimum margin)<br>
        • Maximum 3 alerts per refresh<br>
        • 3-minute cooldown per item
        </div>
        """, unsafe_allow_html=True)

    # Show recent alerts with details
    display_alert_history()


def display_alert_history():
    """Display detailed alert history"""

    alert_history = get_alert_history()

    if alert_history:
        with st.expander("📋 Recent Alert History"):
            alert_data = []
            now = datetime.datetime.now(datetime.timezone.utc)

            for item, last_time in alert_history.items():
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


def display_watchlist_status(df):
    """Display current watchlist status if items exist"""

    if 'watchlist' in st.session_state and st.session_state.watchlist:
        st.subheader("⭐ Watchlist Status")

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
            st.dataframe(watchlist_df, key="watchlist_status_table", use_container_width=True)

            # Watchlist summary metrics
            col1, col2, col3 = st.columns(3)

            # Calculate watchlist metrics
            watchlist_items = df[df['Item'].isin(st.session_state.watchlist)]
            if not watchlist_items.empty:
                avg_watchlist_margin = watchlist_items['Net Margin'].mean()
                avg_watchlist_roi = watchlist_items['ROI (%)'].mean()
                total_watchlist_volume = watchlist_items['1h Volume'].sum()

                with col1:
                    st.metric("Watchlist Avg Margin", f"{avg_watchlist_margin:,.0f} gp")
                with col2:
                    st.metric("Watchlist Avg ROI", f"{avg_watchlist_roi:.1f}%")
                with col3:
                    st.metric("Watchlist Total Volume", f"{total_watchlist_volume:,.0f}")


def create_market_insights(df):
    """Create market insights and analysis"""

    if df.empty:
        return

    st.subheader("💡 Market Insights")

    # Calculate market insights
    high_margin_items = len(df[df['Net Margin'] > 1000])
    high_roi_items = len(df[df['ROI (%)'] > 5])
    high_volume_items = len(df[df['1h Volume'] > 1000])

    # Time-based insights
    current_hour = datetime.datetime.now().hour
    if 12 <= current_hour <= 18:
        time_status = "🌅 Peak Trading Hours"
        time_desc = "High activity period - good liquidity expected"
    elif 18 <= current_hour <= 22:
        time_status = "🌆 Evening Hours"
        time_desc = "Moderate activity - stable prices"
    elif 22 <= current_hour <= 6:
        time_status = "🌙 Overnight Period"
        time_desc = "Lower activity - overnight flip opportunities"
    else:
        time_status = "🌄 Morning Hours"
        time_desc = "Building activity - price stabilization"

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"""
        **Market Analysis:**
        - 🎯 High Margin Items: {high_margin_items}
        - 📈 High ROI Items: {high_roi_items}
        - 🔄 High Volume Items: {high_volume_items}
        - 📊 Total Opportunities: {len(df)}
        """)

    with col2:
        st.info(f"""
        **Trading Conditions:**
        - ⏰ {time_status}
        - 📝 {time_desc}
        - 🎲 Risk Level: {"Low" if high_margin_items > 10 else "Medium" if high_margin_items > 5 else "High"}
        - 💡 Recommendation: {"Great time to trade" if high_margin_items > 10 else "Good opportunities available" if high_margin_items > 5 else "Limited opportunities"}
        """)


def show_success_message(message, icon="✅"):
    """Show a beautiful success message"""
    st.markdown(f"""
    <div style="background: rgba(40, 167, 69, 0.1); border: 1px solid rgba(40, 167, 69, 0.3);
                border-radius: 8px; padding: 15px; margin: 10px 0; color: #28a745;
                text-align: center; font-weight: 500;">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)
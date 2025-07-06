"""
Page Sections Component
Contains organized sections for the opportunities page
"""

import streamlit as st
from src.components.alerts_metrics import (
    create_performance_metrics,
    create_alert_status_display,
    display_watchlist_status,
    create_market_insights
)
from src.components.results_table import display_paginated_table
from src.components.tools import (
    create_profit_calculator,
    create_export_options,
    create_watchlist_manager,
    create_quick_chart_access
)


def create_results_section(df):
    """Create the main results section"""
    st.markdown("## 📊 Trading Opportunities")

    # Main results table
    display_paginated_table(df)


def create_tools_section(df):
    """Create the trading tools section"""
    st.markdown("---")
    st.markdown("## 🛠️ Trading Tools")

    col1, col2 = st.columns(2)

    with col1:
        create_profit_calculator()

    with col2:
        create_export_options(df)


def create_navigation_section(df):
    """Create the navigation and charts section"""
    st.markdown("---")
    st.markdown("## 🧭 Navigation & Charts")

    create_quick_chart_access(df)


def create_management_section(df):
    """Create the management section"""
    st.markdown("---")
    st.markdown("## 📋 Management")

    col1, col2 = st.columns(2)

    with col1:
        create_watchlist_manager()

    with col2:
        display_watchlist_status(df)


def create_status_section(df, show_all):
    """Create the status and alerts section"""
    st.markdown("---")
    st.markdown("## 📊 Status & Alerts")

    # Two column layout for better organization
    col1, col2 = st.columns(2)

    with col1:
        create_alert_status_display(df, show_all)

    with col2:
        create_market_insights(df)


def create_no_results_section(filters):
    """Create content when no results are found"""
    st.warning("⚠️ No flip opportunities found. Try adjusting your filters or enable 'Show All'.")

    # Show current filter settings
    with st.expander("🔧 Current Filter Settings"):
        st.write(f"**Mode:** {filters['mode']}")
        st.write(f"**Min Margin:** {filters['margin']:,} gp")
        st.write(f"**Min Volume:** {filters['volume']:,}")
        st.write(f"**Min Utility:** {filters['utility']:,}")
        st.write(f"**Show All:** {filters['show_all']}")

    # Suggest filter adjustments
    st.info(
        "💡 **Suggestions:**\n- Lower your margin requirements\n- Reduce volume thresholds\n- Enable 'Show All' option\n- Try a different trading mode")
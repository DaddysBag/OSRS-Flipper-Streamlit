"""
Data Loading Component
Handles all data fetching and caching logic
"""

import streamlit as st
import pandas as pd
from data_fetchers import get_real_time_prices
from osrs_flip_assistant import run_flip_scanner


def load_flip_data(mode, force_refresh=False):
    """
    Load flip opportunity data with caching and progress indicators

    Args:
        mode: Trading mode (Custom, High-ROI, etc.)
        force_refresh: Whether to force refresh the data

    Returns:
        tuple: (df, name2id) - DataFrame of opportunities and name to ID mapping
    """

    # Initialize defaults
    df = pd.DataFrame()
    name2id = {}

    # Handle forced refresh (button clicked)
    if force_refresh:
        with st.spinner("🔄 Processing data..."):
            df, name2id = run_flip_scanner(mode)
            if 'price_data' not in st.session_state:
                st.session_state.price_data = get_real_time_prices()
        return df, name2id

    # Handle initial load
    if 'initial_load_done' not in st.session_state:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("🚀 Starting OSRS Flip Assistant...")
            progress_bar.progress(30)

            status_text.text("💰 Fetching market data...")
            progress_bar.progress(60)

            df, name2id = run_flip_scanner(mode)
            if 'price_data' not in st.session_state:
                st.session_state.price_data = get_real_time_prices()

            progress_bar.progress(100)
            status_text.text("✅ Ready!")
            st.session_state.initial_load_done = True

            # Clear progress after delay
            import time
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Error during initial load: {e}")
            return df, name2id
    else:
        # Quick load for subsequent visits
        df, name2id = run_flip_scanner(mode)
        if 'price_data' not in st.session_state:
            st.session_state.price_data = get_real_time_prices()

    return df, name2id


def create_debug_section(MIN_MARGIN, MIN_VOLUME, MIN_UTILITY, show_all):
    """Create the debug information expander"""

    with st.expander("🔧 Debug Information"):
        st.write("**Current Configuration:**")
        st.write(f"- Min Margin: {MIN_MARGIN:,} gp")
        st.write(f"- Min Volume: {MIN_VOLUME:,}/hr")
        st.write(f"- Min Utility: {MIN_UTILITY:,}")
        st.write(f"- Show All: {show_all}")

        if st.button("🧪 Test API Connections"):
            from data_fetchers import get_item_mapping, get_real_time_prices, get_hourly_prices

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
            import os
            import json
            from utils import get_buy_limits

            # Create ge_limits.json if it doesn't exist
            if not os.path.exists('ge_limits.json'):
                default_limits = get_buy_limits()
                try:
                    with open('ge_limits.json', 'w') as f:
                        json.dump(default_limits, f, indent=2)
                    st.success("✅ Created ge_limits.json with default buy limits")
                except Exception as e:
                    st.error(f"❌ Failed to create ge_limits.json: {e}")
            else:
                st.info("ge_limits.json already exists")
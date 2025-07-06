"""
Data Loading Component
Handles all data fetching and caching logic
"""

import streamlit as st
import pandas as pd
import time
from data_fetchers import get_real_time_prices
from filters import run_flip_scanner


def load_flip_data(mode, force_refresh=False):
    """
    Load flip opportunity data with advanced caching and performance tracking
    """
    from src.utils.cache_optimizer import get_cached_market_data, get_performance_stats

    # Initialize defaults
    df = pd.DataFrame()
    name2id = {}

    # Handle forced refresh (bypass cache)
    if force_refresh:
        with st.spinner("🔄 Fetching fresh data..."):
            # Clear cache and fetch new data
            st.cache_data.clear()
            from filters import run_flip_scanner
            df, name2id = run_flip_scanner(mode)

            if 'price_data' not in st.session_state:
                from data_fetchers import get_real_time_prices
                st.session_state.price_data = get_real_time_prices()
        return df, name2id

    # Use cached data for better performance
    if 'initial_load_done' not in st.session_state:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("🚀 Starting OSRS Flip Assistant...")
            progress_bar.progress(20)

            status_text.text("📊 Loading cached market data...")
            progress_bar.progress(40)

            # Use performance-optimized cached data
            df, name2id = get_cached_market_data(mode)
            progress_bar.progress(70)

            status_text.text("⚡ Optimizing performance...")
            if 'price_data' not in st.session_state:
                from data_fetchers import get_real_time_prices
                st.session_state.price_data = get_real_time_prices()
            progress_bar.progress(90)

            # Show performance stats
            perf_stats = get_performance_stats()
            status_text.text(f"✅ Ready! (Cache hit rate: {perf_stats['hit_rate']:.1f}%)")
            progress_bar.progress(100)

            time.sleep(0.5)  # Brief pause to show completion
            progress_bar.empty()
            status_text.empty()

            st.session_state.initial_load_done = True

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Data loading failed: {e}")
            return pd.DataFrame(), {}

    else:
        # Subsequent loads use cache
        df, name2id = get_cached_market_data(mode)

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
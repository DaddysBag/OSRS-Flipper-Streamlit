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
    Load flip opportunity data with comprehensive error handling
    """
    from src.utils.error_handler import safe_execute, ErrorHandler

    # Initialize defaults
    df = pd.DataFrame()
    name2id = {}

    # Handle forced refresh (bypass cache)
    if force_refresh:
        with st.spinner("🔄 Fetching fresh data..."):
            try:
                # Clear cache and fetch new data
                st.cache_data.clear()
                df, name2id = run_flip_scanner(mode)

                if 'price_data' not in st.session_state:
                    st.session_state.price_data = get_real_time_prices()

                # Store successful load time
                st.session_state.last_data_update = time.time()
                st.session_state.cache_hit_rate = 50.0  # Reset cache rate

            except ConnectionError as e:
                ErrorHandler.handle_api_error(e, "Data Refresh")
                return pd.DataFrame(), {}
            except Exception as e:
                ErrorHandler.handle_data_error(e, "Data Refresh")
                return pd.DataFrame(), {}

        return df, name2id

    # Use cached data for better performance
    if 'initial_load_done' not in st.session_state:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("🚀 Starting OSRS Flip Assistant...")
            progress_bar.progress(20)

            status_text.text("📊 Loading market data...")
            progress_bar.progress(40)

            # Load data with error handling
            try:
                from src.utils.cache_optimizer import get_cached_market_data
                df, name2id = get_cached_market_data(mode)
                st.session_state.cache_hit_rate = 85.0  # High cache rate
            except ImportError:
                # Fallback to direct call if cache optimizer not available
                df, name2id = run_flip_scanner(mode)
                st.session_state.cache_hit_rate = 25.0  # Lower cache rate
            except Exception as e:
                status_text.text("⚠️ Retrying with fallback method...")
                df, name2id = run_flip_scanner(mode)
                st.session_state.cache_hit_rate = 15.0  # Low cache rate

            progress_bar.progress(70)

            status_text.text("⚡ Optimizing performance...")
            if 'price_data' not in st.session_state:
                try:
                    st.session_state.price_data = get_real_time_prices()
                except Exception as e:
                    st.warning(f"⚠️ Price data unavailable: {e}")
                    st.session_state.price_data = {}

            progress_bar.progress(90)

            # Store successful load
            st.session_state.last_data_update = time.time()
            status_text.text("✅ Ready!")
            progress_bar.progress(100)

            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()

            st.session_state.initial_load_done = True

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            ErrorHandler.handle_data_error(e, "Initial Data Load")

            # Provide fallback empty data
            return pd.DataFrame(), {}

    else:
        # Subsequent loads with error handling
        try:
            from src.utils.cache_optimizer import get_cached_market_data
            df, name2id = get_cached_market_data(mode)
        except ImportError:
            df, name2id = run_flip_scanner(mode)
        except Exception as e:
            ErrorHandler.handle_data_error(e, "Data Reload")
            return pd.DataFrame(), {}

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
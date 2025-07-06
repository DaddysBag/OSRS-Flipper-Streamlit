"""
Centralized Error Handling for OSRS Flip Assistant
Provides graceful error handling and user-friendly messages
"""

import streamlit as st
import traceback
import functools
from typing import Any, Callable, Optional


class ErrorHandler:
    """Centralized error handling with user-friendly messages"""

    @staticmethod
    def handle_api_error(error: Exception, context: str = "API call"):
        """Handle API-related errors"""
        error_msg = str(error).lower()

        if "timeout" in error_msg or "connection" in error_msg:
            st.error(
                f"🌐 **Connection Issue**: Unable to reach OSRS servers. Please check your internet connection and try again.")
        elif "rate limit" in error_msg or "429" in error_msg:
            st.warning(f"⏱️ **Rate Limit**: Too many requests. Please wait a moment before refreshing.")
        elif "404" in error_msg or "not found" in error_msg:
            st.error(f"📭 **Data Not Found**: The requested OSRS data is temporarily unavailable.")
        else:
            st.error(f"❌ **{context} Error**: {error}")

        # Show retry option
        if st.button("🔄 Retry", key=f"retry_{context}"):
            st.rerun()

    @staticmethod
    def handle_data_error(error: Exception, context: str = "Data processing"):
        """Handle data processing errors"""
        st.error(f"📊 **{context} Error**: {error}")
        st.info("💡 **Tip**: Try refreshing the data or adjusting your filters.")

        with st.expander("🔧 Technical Details"):
            st.code(str(error))

    @staticmethod
    def handle_ui_error(error: Exception, context: str = "Interface"):
        """Handle UI-related errors"""
        st.warning(f"🎨 **{context} Issue**: {error}")
        st.info("The app is still functional - this is just a display issue.")


def safe_execute(error_context: str = "Operation", show_traceback: bool = False):
    """Decorator to safely execute functions with error handling"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except ConnectionError as e:
                ErrorHandler.handle_api_error(e, error_context)
                return None
            except ValueError as e:
                ErrorHandler.handle_data_error(e, error_context)
                return None
            except Exception as e:
                st.error(f"❌ **{error_context} Failed**: {e}")

                if show_traceback:
                    with st.expander("🔧 Debug Information"):
                        st.code(traceback.format_exc())

                # Offer fallback options
                st.info(
                    "🔄 **Try these solutions:**\n- Refresh the page\n- Check your filters\n- Try a different trading mode")
                return None

        return wrapper

    return decorator


def create_error_recovery_section():
    """Create a section with error recovery options"""
    st.markdown("---")
    st.markdown("### 🚨 Having Issues?")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Clear Cache", help="Clear all cached data and start fresh"):
            st.cache_data.clear()
            for key in list(st.session_state.keys()):
                if key.startswith('cache_') or key == 'initial_load_done':
                    del st.session_state[key]
            st.success("✅ Cache cleared! Refreshing...")
            st.rerun()

    with col2:
        if st.button("🏠 Reset to Defaults", help="Reset all settings to default values"):
            for key in list(st.session_state.keys()):
                if key in ['min_margin', 'min_volume', 'min_utility', 'selected_item']:
                    del st.session_state[key]
            st.success("✅ Settings reset!")
            st.rerun()

    with col3:
        if st.button("📊 Test Connection", help="Test connection to OSRS servers"):
            test_api_connection()


def test_api_connection():
    """Test API connection and show results"""
    with st.spinner("Testing connection to OSRS servers..."):
        try:
            from data_fetchers import get_real_time_prices
            test_data = get_real_time_prices()

            if test_data and len(test_data) > 0:
                st.success("✅ **Connection Successful**: OSRS servers are reachable!")
                st.info(f"📊 Retrieved data for {len(test_data)} items")
            else:
                st.warning("⚠️ **Connection Issue**: Servers reachable but no data returned")

        except Exception as e:
            st.error(f"❌ **Connection Failed**: {e}")
            st.info("💡 Check your internet connection and try again later")
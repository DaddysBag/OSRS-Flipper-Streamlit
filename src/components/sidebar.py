"""
OSRS Flip Assistant - Sidebar Component
Contains all filtering controls, strategy selection, and cache management
"""

import streamlit as st
from cache_manager import cache_manager


def create_trading_strategy_selector():
    """Create the trading strategy selection interface"""

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
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    return mode


def create_custom_filters(mode, default_margin, default_volume, default_utility):
    """Create custom filter controls when in Custom mode"""

    if mode != "Custom":
        return default_margin, default_volume, default_utility

    st.sidebar.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.sidebar.markdown("### 💰 Profit Filters")

    # Filter controls with better formatting
    new_min_margin = st.sidebar.slider(
        "Min Net Margin (gp)",
        0, 5000,
        st.session_state.get('min_margin', default_margin),
        50,
        help="Minimum profit after GE tax"
    )
    if new_min_margin != st.session_state.get('min_margin', default_margin):
        st.session_state['min_margin'] = new_min_margin

    new_min_volume = st.sidebar.slider(
        "Min Volume/hr",
        0, 20000,
        st.session_state.get('min_volume', default_volume),
        100,
        help="Minimum hourly trading volume"
    )
    if new_min_volume != st.session_state.get('min_volume', default_volume):
        st.session_state['min_volume'] = new_min_volume

    new_min_utility = st.sidebar.slider(
        "Min Utility Score",
        0, 50000,
        st.session_state.get('min_utility', default_utility),
        500,
        help="Minimum utility score (profit × volume)"
    )
    if new_min_utility != st.session_state.get('min_utility', default_utility):
        st.session_state['min_utility'] = new_min_utility

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

    return (st.session_state.get('min_margin', default_margin),
            st.session_state.get('min_volume', default_volume),
            st.session_state.get('min_utility', default_utility))


def create_risk_management_controls():
    """Create risk management filter controls"""

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


def create_preset_management():
    """Create preset save/load functionality"""

    st.sidebar.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.sidebar.markdown("### 📋 Preset Management")

    # Initialize presets if not exists
    if 'presets' not in st.session_state:
        st.session_state.presets = {}

    # Preset load/save with better UI
    preset_options = [''] + list(st.session_state.presets.keys())
    ps = st.sidebar.selectbox(
        "Load Saved Preset",
        preset_options,
        help="Load previously saved filter configurations"
    )

    if ps:
        m, v, u, season = st.session_state.presets[ps]
        st.session_state['min_margin'] = m
        st.session_state['min_volume'] = v
        st.session_state['min_utility'] = u
        st.session_state['season_th'] = season
        st.sidebar.success(f"✅ Loaded preset: {ps}")

    # Save new preset
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        name_in = st.text_input("Preset Name", placeholder="Enter name...", label_visibility="collapsed")
    with col2:
        if st.button("💾 Save", help="Save current settings as preset") and name_in:
            st.session_state.presets[name_in] = (
                st.session_state.get('min_margin', 500),
                st.session_state.get('min_volume', 500),
                st.session_state.get('min_utility', 10000),
                st.session_state.get('season_th', 0)
            )
            st.sidebar.success(f"💾 Saved: {name_in}")

    st.sidebar.markdown('</div>', unsafe_allow_html=True)


def create_display_options():
    """Create display and UI option controls"""

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
        value=st.session_state.get('mobile_view', False),
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

    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    return show_all


def create_keyboard_shortcuts_info():
    """Display keyboard shortcuts information"""

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


def show_cache_stats():
    """Display cache statistics for debugging"""

    stats = cache_manager.get_stats()

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ Cache Performance")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        st.metric("Hit Rate", f"{stats['hit_rate']:.1f}%")
        st.metric("Cache Size", stats['cache_size'])

    with col2:
        st.metric("Total Requests", stats['total_requests'])
        if st.button("🗑️ Clear Cache", key="clear_cache_btn"):
            cleared = cache_manager.clear_cache()
            st.success(f"Cleared {cleared} entries")
            st.rerun()

    # Show cached functions
    if stats['cached_functions']:
        st.sidebar.write("**Cached Functions:**")
        for func, count in stats['cached_functions'].items():
            st.sidebar.write(f"• {func}: {count} entries")


def get_mode_values(mode):
    """Get default values for each trading mode"""

    mode_values = {
        "Low-Risk": (200, 1000, 2000),
        "High-ROI": (1000, 500, 5000),
        "Passive Overnight": (300, 200, 1000),
        "High Volume": (100, 1000, 1000),
        "Custom": (500, 500, 10000)  # defaults
    }

    return mode_values.get(mode, (500, 500, 10000))


def create_complete_sidebar():
    """Create the complete sidebar with all components"""

    # Strategy selection
    mode = create_trading_strategy_selector()

    # Get mode-specific values
    default_margin, default_volume, default_utility = get_mode_values(mode)

    # Custom filters (only shown for Custom mode)
    min_margin, min_volume, min_utility = create_custom_filters(
        mode, default_margin, default_volume, default_utility
    )

    # Apply mode values if not Custom
    if mode != "Custom":
        min_margin, min_volume, min_utility = default_margin, default_volume, default_utility
        # Update session state
        st.session_state['min_margin'] = min_margin
        st.session_state['min_volume'] = min_volume
        st.session_state['min_utility'] = min_utility

    # Risk management (always shown)
    create_risk_management_controls()

    # Preset management
    create_preset_management()

    # Display options
    show_all = create_display_options()

    # Keyboard shortcuts info
    create_keyboard_shortcuts_info()

    # Cache stats
    show_cache_stats()

    return mode, min_margin, min_volume, min_utility, show_all
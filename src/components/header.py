"""
OSRS Flip Assistant - Header Component
SURGICAL CHANGES: Only modify the create_enhanced_header function
Keep all other functions and imports unchanged
"""

import streamlit as st
import datetime
from cache_manager import cache_manager
from src.components.ui_components import create_hero_section, create_quick_stats_row, create_metric_card
from src.components.performance_metrics import create_performance_dashboard, create_performance_badge_advanced
from src.utils.mobile_utils import is_mobile, create_mobile_friendly_metric, get_mobile_columns


def create_enhanced_header():
    """SIMPLIFIED VERSION: Clean header focused on user needs"""

    # Use existing hero section (keep your current styling)
    create_hero_section()

    # Replace the complex 4-metric system with simple 2-metric system
    create_simple_status_indicators()


def create_simple_status_indicators():
    """Simple 2-column status instead of complex 4-column technical metrics"""

    # Calculate time since last update (keep existing logic)
    current_time = datetime.datetime.now()
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = current_time

    time_diff = current_time - st.session_state.last_update_time
    minutes_ago = int(time_diff.total_seconds() / 60)

    # Simple 2-column layout instead of complex 4-column
    col1, col2 = st.columns(2)

    with col1:
        # Data freshness - users actually care about this
        if minutes_ago < 5:
            data_status = "🟢 Data Fresh"
            data_delta = "Recently updated"
        elif minutes_ago < 15:
            data_status = "🟡 Data Recent"
            data_delta = f"Updated {minutes_ago}m ago"
        else:
            data_status = "🔴 Needs refresh"
            data_delta = f"Last update: {minutes_ago}m ago"

        # Use your existing create_metric_card function
        create_metric_card("Data Status", data_status, delta=data_delta, icon="📊")

    with col2:
        # System mode - simplified from alert system complexity
        alert_active = not st.session_state.get('show_all_table', False)

        if alert_active:
            system_status = "🔔 Alert Mode"
            system_delta = "Monitoring opportunities"
        else:
            system_status = "📋 Browse Mode"
            system_delta = "Showing all items"

        # Use your existing create_metric_card function
        create_metric_card("System Mode", system_status, delta=system_delta, icon="⚙️")


# KEEP ALL YOUR EXISTING FUNCTIONS UNCHANGED:
# - create_navigation()
# - create_page_title()
# - create_performance_badge()
# (Don't modify these - they work fine)

def create_navigation():
    """Create navigation breadcrumbs and page selector"""

    # Navigation pages
    pages = {
        "🔍 Opportunities": "opportunities",
        "📊 Item Charts": "charts"
    }

    if 'page' not in st.session_state:
        st.session_state.page = 'opportunities'

    # Breadcrumb navigation
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # Show current location
        if st.session_state.page == 'opportunities':
            st.markdown("📍 **Home** > Opportunities")
        elif st.session_state.page == 'charts':
            selected_item = st.session_state.get('selected_item', 'Unknown Item')
            st.markdown(f"📍 **Home** > Opportunities > Charts > {selected_item}")

    with col2:
        # Page selector
        selected_page = st.selectbox("Go to:", list(pages.keys()),
                                     index=list(pages.values()).index(st.session_state.page),
                                     key="main_nav")
        if pages[selected_page] != st.session_state.page:
            st.session_state.page = pages[selected_page]
            st.rerun()

    with col3:
        # Quick actions
        if st.session_state.page == 'charts':
            if st.button("⬅️ Back to Opportunities", type="secondary"):
                st.session_state.page = 'opportunities'
                st.rerun()

def create_page_title(page_name, item_name=None):
    """Create dynamic page titles based on current page"""

    if page_name == 'opportunities':
        # Already handled in create_enhanced_header
        pass
    elif page_name == 'charts' and item_name:
        st.markdown(f"""
        <h2 style="color: #4CAF50; margin-top: 20px; font-weight: 600;">
        📊 {item_name} - Price Chart Analysis
        </h2>
        """, unsafe_allow_html=True)


def create_performance_badge():
    """SIMPLIFIED: Remove technical details users don't need"""
    # We'll remove the call to this function from main app instead
    # Keep the function here in case other parts of code use it
    pass
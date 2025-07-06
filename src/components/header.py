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
    """Clean status line with refresh button inline on the right"""

    # Calculate time since last update (keep existing logic)
    current_time = datetime.datetime.now()
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = current_time

    time_diff = current_time - st.session_state.last_update_time
    minutes_ago = int(time_diff.total_seconds() / 60)

    # Determine status
    if minutes_ago < 5:
        data_status = "🟢 Data Fresh"
        data_detail = "Recently updated"
    elif minutes_ago < 15:
        data_status = "🟡 Data Recent"
        data_detail = f"Updated {minutes_ago}m ago"
    else:
        data_status = "🔴 Needs refresh"
        data_detail = f"Last update: {minutes_ago}m ago"

    # System mode
    alert_active = not st.session_state.get('show_all_table', False)
    if alert_active:
        system_status = "🔔 Alert Mode"
        system_detail = "Monitoring opportunities"
    else:
        system_status = "📋 Browse Mode"
        system_detail = "Showing all items"

    # Layout: Status indicators on left, refresh button on right
    col1, col2 = st.columns([3, 1])

    with col1:
        # Status indicators
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 24px;
            padding: 12px 20px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            font-size: 0.9rem;
            margin: 8px 0;
        ">
            <span><strong>{data_status}</strong> <span style="color: #B0B8C5;">({data_detail})</span></span>
            <span><strong>{system_status}</strong> <span style="color: #B0B8C5;">({system_detail})</span></span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Refresh button aligned to the right
        if st.button("🔄 Refresh Data", key="header_refresh", type="secondary"):
            st.session_state.last_update_time = current_time
            st.session_state['force_data_refresh'] = True
            st.rerun()

def create_navigation():
    """Create clean navigation layout"""

    # Navigation pages
    pages = {
        "🔍 Opportunities": "opportunities",
        "📊 Item Charts": "charts"
    }

    if 'page' not in st.session_state:
        st.session_state.page = 'opportunities'

    # Clean layout: Breadcrumb left, Page selector right
    col1, col2 = st.columns([3, 1])

    with col1:
        # Breadcrumb navigation (left side)
        if st.session_state.page == 'opportunities':
            st.markdown("📍 **Home** > Opportunities")
        elif st.session_state.page == 'charts':
            selected_item = st.session_state.get('selected_item', 'Unknown Item')
            st.markdown(f"📍 **Home** > Opportunities > Charts > {selected_item}")

    with col2:
        # Page selector (right-aligned)
        selected_page = st.selectbox(
            "Go to:",
            list(pages.keys()),
            index=list(pages.values()).index(st.session_state.page),
            key="main_nav",
            label_visibility="collapsed"
        )
        if pages[selected_page] != st.session_state.page:
            st.session_state.page = pages[selected_page]
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
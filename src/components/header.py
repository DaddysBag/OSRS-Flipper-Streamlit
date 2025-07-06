"""
OSRS Flip Assistant - Header Component
Contains the main header, navigation, and status indicators
"""

import streamlit as st
import datetime
from cache_manager import cache_manager
from src.components.ui_components import create_hero_section, create_quick_stats_row, create_metric_card

def create_enhanced_header():
    """Create the modern enhanced header with OSRS theming"""

    from src.components.ui_components import create_hero_section, create_quick_stats_row, create_metric_card

    # Get cache stats for status bar
    cache_stats = cache_manager.get_stats()

    # Calculate time since last update
    current_time = datetime.datetime.now()
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = current_time

    time_diff = current_time - st.session_state.last_update_time
    minutes_ago = int(time_diff.total_seconds() / 60)

    # Modern hero section
    create_hero_section()

    # Quick stats row with modern styling
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        api_status = "Connected" if cache_stats['hit_rate'] > 0 else "Disconnected"
        status_delta = "✅ Online" if cache_stats['hit_rate'] > 0 else "❌ Offline"
        create_metric_card("API Status", api_status, delta=status_delta, icon="🌐")

    with col2:
        cache_performance = f"{cache_stats['hit_rate']:.1f}%"
        cache_delta = "Optimized" if cache_stats['hit_rate'] > 70 else "Needs improvement"
        create_metric_card("Cache Performance", cache_performance, delta=cache_delta, icon="⚡")

    with col3:
        data_age = f"{minutes_ago}m ago"
        freshness_delta = "Fresh" if minutes_ago < 5 else "Recent" if minutes_ago < 15 else "Stale"
        create_metric_card("Data Freshness", data_age, delta=freshness_delta, icon="⏰")

    with col4:
        alert_value = "Active" if not st.session_state.get('show_all_table', False) else "Disabled"
        alert_delta = "Ready" if alert_value == "Active" else "Disabled"
        create_metric_card("Alert System", alert_value, delta=alert_delta, icon="🔔")

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
            st.markdown(f"📍 **Home** > [Opportunities](?) > Charts > {selected_item}")

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
    """Create a performance monitoring badge"""

    # Get current performance metrics
    cache_stats = cache_manager.get_stats()

    # Calculate performance score
    hit_rate = cache_stats.get('hit_rate', 0)
    if hit_rate >= 80:
        performance_status = "🚀 Excellent"
        performance_color = "#27ae60"
    elif hit_rate >= 60:
        performance_status = "⚡ Good"
        performance_color = "#f39c12"
    else:
        performance_status = "🐌 Slow"
        performance_color = "#e74c3c"

    st.markdown(f"""
    <div style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: {performance_color};
        color: white;
        padding: 8px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        z-index: 1000;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    ">
        {performance_status} ({hit_rate:.0f}%)
    </div>
    """, unsafe_allow_html=True)
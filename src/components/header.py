"""
OSRS Flip Assistant - Header Component
Contains the main header, navigation, and status indicators
"""

import streamlit as st
import datetime
from cache_manager import cache_manager


def create_enhanced_header():
    """Create the enhanced header with status indicators"""

    # Get cache stats for status bar
    cache_stats = cache_manager.get_stats()

    # Calculate time since last update
    current_time = datetime.datetime.now()
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = current_time

    time_diff = current_time - st.session_state.last_update_time
    minutes_ago = int(time_diff.total_seconds() / 60)

    # Main header
    st.markdown("""
    <h1 style="color: #ffd700; font-size: 2.5rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);">
    💸 OSRS GE Flipping Assistant
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p style="color: #bbb; font-size: 1.1rem; margin-bottom: 20px;">
    Real-time Grand Exchange opportunity scanner with advanced analytics
    </p>
    """, unsafe_allow_html=True)

    # Status indicators using columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.success("✅ API Connected")

    with col2:
        st.info(f"📊 Cache Hit Rate: {cache_stats['hit_rate']:.1f}%")

    with col3:
        st.info(f"⏰ Last Update: {minutes_ago} min ago")

    with col4:
        alert_status = "🔔 Active" if not st.session_state.get('show_all_table', False) else "🚫 Disabled"
        if "Active" in alert_status:
            st.success(alert_status)
        else:
            st.warning(alert_status)


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
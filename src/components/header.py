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
    """Clean status line with minimal padding"""

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

    # Minimal layout with reduced spacing
    col1, col2 = st.columns([3, 1])

    with col1:
        # Status indicators with minimal padding
        st.markdown(f"""
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 24px;
                    padding: 12px 20px;
                    background: linear-gradient(135deg, 
                        rgba(255, 255, 255, 0.08), 
                        rgba(255, 215, 0, 0.04),
                        rgba(74, 144, 226, 0.03)
                    );
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 215, 0, 0.15);
                    border-radius: 16px;
                    font-size: 0.9rem;
                    margin: 8px 0;
                    box-shadow: 
                        0 8px 32px rgba(0, 0, 0, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.1),
                        0 1px 3px rgba(255, 215, 0, 0.1);
                    position: relative;
                    overflow: hidden;
                ">
                    <div style="
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        height: 1px;
                        background: linear-gradient(90deg, 
                            transparent, 
                            rgba(255, 215, 0, 0.4), 
                            transparent
                        );
                    "></div>

                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        position: relative;
                    ">
                        <div class="status-pulse" style="
                            width: 8px;
                            height: 8px;
                            border-radius: 50%;
                            background: {get_status_color(data_status)};
                            box-shadow: 0 0 8px {get_status_color(data_status)};
                            animation: pulse 2s infinite;
                        "></div>
                        <span style="
                            font-weight: 600;
                            color: #FFFFFF;
                            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
                        ">{data_status}</span>
                        <span style="
                            color: rgba(176, 184, 197, 0.9);
                            font-size: 0.85rem;
                        ">({data_detail})</span>
                    </div>

                    <div style="
                        width: 1px;
                        height: 20px;
                        background: linear-gradient(180deg, 
                            transparent, 
                            rgba(255, 255, 255, 0.1), 
                            transparent
                        );
                    "></div>

                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        position: relative;
                    ">
                        <div style="
                            width: 8px;
                            height: 8px;
                            border-radius: 50%;
                            background: {get_system_status_color(system_status)};
                            box-shadow: 0 0 8px {get_system_status_color(system_status)};
                        "></div>
                        <span style="
                            font-weight: 600;
                            color: #FFFFFF;
                            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
                        ">{system_status}</span>
                        <span style="
                            color: rgba(176, 184, 197, 0.9);
                            font-size: 0.85rem;
                        ">({system_detail})</span>
                    </div>
                </div>

                <style>
                @keyframes pulse {{
                    0%, 100% {{ 
                        opacity: 1; 
                        transform: scale(1); 
                    }}
                    50% {{ 
                        opacity: 0.7; 
                        transform: scale(1.1); 
                    }}
                }}
                </style>
                """, unsafe_allow_html=True)

    with col2:
        # Refresh button with minimal styling
        if st.button("🔄 Refresh", key="header_refresh", type="secondary"):
            st.session_state.last_update_time = current_time
            st.session_state['force_data_refresh'] = True
            st.rerun()

def get_status_color(status):
    """Get color for data status indicator"""
    if "🟢" in status:
        return "#4CAF50"
    elif "🟡" in status:
        return "#FFC107"
    else:
        return "#F44336"

def get_system_status_color(status):
    """Get color for system status indicator"""
    if "🔔" in status:
        return "#FF9800"
    else:
        return "#74C0FC"

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
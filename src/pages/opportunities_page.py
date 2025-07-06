"""
Opportunities Page Controller
Handles the main opportunities page flow and coordination
"""

import streamlit as st
from src.components.sidebar import create_complete_sidebar
from src.components.data_loader import load_flip_data, create_debug_section
from src.components.page_sections import (
    create_results_section,
    create_tools_section,
    create_navigation_section,
    create_management_section,
    create_status_section,
    create_no_results_section
)


def show_opportunities_page():
    """Clean, organized opportunities page using section-based components"""

    # Initialize page state
    page_state = initialize_page_state()

    # Create sidebar and get filters
    filters = create_sidebar_with_filters(page_state)

    # Load data with progress
    df, name2id = load_data_with_progress(filters)

    # Render appropriate content
    if not df.empty:
        render_results_content(df, filters)
    else:
        render_no_results_content(filters)

    from src.utils.error_handler import create_error_recovery_section
    create_error_recovery_section()


def initialize_page_state():
    """Initialize session state for opportunities page"""
    return {
        'min_margin': st.session_state.get('min_margin', 500),
        'min_volume': st.session_state.get('min_volume', 500),
        'min_utility': st.session_state.get('min_utility', 10000)
    }


def create_sidebar_with_filters(page_state):
    """Create sidebar and return filter values"""
    try:
        mode, margin, volume, utility, show_all = create_complete_sidebar()

        # Store in session state
        st.session_state.update({
            'min_margin': margin,
            'min_volume': volume,
            'min_utility': utility
        })

        return {
            'mode': mode,
            'margin': margin,
            'volume': volume,
            'utility': utility,
            'show_all': show_all
        }
    except Exception as e:
        st.error(f"❌ Sidebar creation failed: {e}")
        return create_fallback_filters(page_state)


def create_fallback_filters(page_state):
    """Create fallback filter values if sidebar fails"""
    return {
        'mode': "Custom",
        'margin': page_state['min_margin'],
        'volume': page_state['min_volume'],
        'utility': page_state['min_utility'],
        'show_all': False
    }


def load_data_with_progress(filters):
    """Load flip data with progress indicators"""
    force_refresh = st.button("🔄 Refresh Data", type="primary")

    df, name2id = load_flip_data(filters['mode'], force_refresh)
    create_debug_section(filters['margin'], filters['volume'], filters['utility'], filters['show_all'])

    return df, name2id


def render_results_content(df, filters):
    """Render the main results content sections"""
    create_results_section(df)
    create_tools_section(df)
    create_navigation_section(df)
    create_management_section(df)
    create_status_section(df, filters['show_all'])


def render_no_results_content(filters):
    """Render content when no results found"""
    create_no_results_section(filters)
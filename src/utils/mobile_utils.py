"""
Mobile Optimization Utilities
Handles mobile detection and responsive layout adjustments
"""

import streamlit as st


def inject_mobile_detection():
    """Inject JavaScript to detect mobile devices and screen size"""

    st.markdown("""
    <script>
        // Mobile detection and responsive utilities
        function detectMobile() {
            const isMobile = window.innerWidth <= 768;
            const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
            const isDesktop = window.innerWidth > 1024;

            // Store in sessionStorage for access across components
            sessionStorage.setItem('isMobile', isMobile);
            sessionStorage.setItem('isTablet', isTablet);
            sessionStorage.setItem('isDesktop', isDesktop);
            sessionStorage.setItem('screenWidth', window.innerWidth);

            // Add CSS classes to body for responsive styling
            document.body.classList.remove('mobile', 'tablet', 'desktop');
            if (isMobile) document.body.classList.add('mobile');
            if (isTablet) document.body.classList.add('tablet');
            if (isDesktop) document.body.classList.add('desktop');

            return { isMobile, isTablet, isDesktop, width: window.innerWidth };
        }

        // Run on load and resize
        detectMobile();
        window.addEventListener('resize', detectMobile);

        // Optimize touch interactions for mobile
        if (window.innerWidth <= 768) {
            document.addEventListener('touchstart', function() {}, {passive: true});
        }
    </script>
    """, unsafe_allow_html=True)


def get_mobile_columns(desktop_cols, tablet_cols, mobile_cols):
    """Return appropriate column count based on device type"""

    # Default to desktop layout
    return mobile_cols if is_mobile() else tablet_cols if is_tablet() else desktop_cols


def is_mobile():
    """Check if user is on mobile device (basic server-side detection)"""

    # Simple heuristic - can be enhanced with user agent detection
    return st.session_state.get('mobile_detected', False)


def is_tablet():
    """Check if user is on tablet device"""

    return st.session_state.get('tablet_detected', False)


def create_mobile_friendly_metric(label, value, delta=None, icon="📊"):
    """Create mobile-optimized metric cards"""

    if is_mobile():
        # Compact mobile layout
        st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            text-align: center;
        ">
            <div style="font-size: 1.1rem; font-weight: 600; color: #4CAF50;">
                {icon} {value}
            </div>
            <div style="font-size: 0.85rem; color: #bbb; margin-top: 4px;">
                {label}
            </div>
            {f'<div style="font-size: 0.75rem; color: #FFD700; margin-top: 2px;">{delta}</div>' if delta else ''}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Regular desktop metric
        st.metric(label, value, delta=delta)


def create_mobile_table_card(item_data, index):
    """Create mobile-friendly card for table items"""

    profit_color = "#4CAF50" if item_data.get('Net Margin', 0) >= 1000 else "#FFA726" if item_data.get('Net Margin',
                                                                                                       0) >= 500 else "#FF7043"

    st.markdown(f"""
    <div style="
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        position: relative;
    ">
        <!-- Item Header -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h4 style="color: #4CAF50; margin: 0; font-size: 1.1rem; font-weight: 600;">
                {item_data.get('Item', 'Unknown Item')}
            </h4>
            <div style="background: {profit_color}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">
                {item_data.get('Net Margin', 0):,} gp
            </div>
        </div>

        <!-- Price Row -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
            <div>
                <div style="color: #bbb; font-size: 0.8rem;">Buy Price</div>
                <div style="color: #4CAF50; font-weight: 600;">{item_data.get('Buy Price', 0):,} gp</div>
            </div>
            <div>
                <div style="color: #bbb; font-size: 0.8rem;">Sell Price</div>
                <div style="color: #4CAF50; font-weight: 600;">{item_data.get('Sell Price', 0):,} gp</div>
            </div>
        </div>

        <!-- Stats Row -->
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 12px;">
            <div style="text-align: center;">
                <div style="color: #bbb; font-size: 0.75rem;">ROI</div>
                <div style="color: #FFD700; font-weight: 600;">{item_data.get('ROI (%)', 0):.1f}%</div>
            </div>
            <div style="text-align: center;">
                <div style="color: #bbb; font-size: 0.75rem;">Volume</div>
                <div style="color: #4A90E2; font-weight: 600;">{item_data.get('1h Volume', 0):,}</div>
            </div>
            <div style="text-align: center;">
                <div style="color: #bbb; font-size: 0.75rem;">Risk</div>
                <div style="color: #FFA726; font-weight: 600;">{'🟢' if item_data.get('ROI (%)', 0) >= 3 else '🟡' if item_data.get('ROI (%)', 0) >= 1 else '🔴'}</div>
            </div>
        </div>

        <!-- Action Button -->
        <div style="text-align: center;">
            <button onclick="viewChart('{item_data.get('Item', '')}')" style="
                background: linear-gradient(135deg, #4CAF50, #45a049);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                transition: all 0.3s ease;
            ">
                📊 View Chart & Details
            </button>
        </div>
    </div>

    <script>
        function viewChart(itemName) {{
            // This would trigger the chart view in Streamlit
            // For now, just show an alert
            alert('Chart for ' + itemName + ' (Feature in development)');
        }}
    </script>
    """, unsafe_allow_html=True)


def inject_mobile_styles():
    """Inject mobile-specific CSS optimizations"""

    st.markdown("""
    <style>
        /* Mobile-specific styles */
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 1rem !important;
                max-width: 100% !important;
            }

            /* Make buttons touch-friendly */
            .stButton button {
                min-height: 44px !important;
                font-size: 0.9rem !important;
                padding: 12px 16px !important;
            }

            /* Optimize metric cards for mobile */
            [data-testid="metric-container"] {
                background: rgba(255, 255, 255, 0.05) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 8px !important;
                padding: 12px !important;
                margin: 8px 0 !important;
            }

            /* Make expandable sections mobile-friendly */
            .streamlit-expanderHeader {
                font-size: 1rem !important;
                padding: 12px !important;
            }

            /* Optimize table for mobile scrolling */
            .stDataFrame {
                font-size: 0.8rem !important;
            }

            /* Hide some desktop-only elements */
            .desktop-only {
                display: none !important;
            }
        }

        /* Tablet optimizations */
        @media (min-width: 769px) and (max-width: 1024px) {
            .main .block-container {
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }
        }

        /* Touch-friendly improvements */
        .mobile button, .mobile .stSelectbox, .mobile .stTextInput input {
            min-height: 44px !important;
            font-size: 16px !important; /* Prevents zoom on iOS */
        }

        /* Performance badge mobile positioning */
        @media (max-width: 768px) {
            [style*="position: fixed"][style*="bottom: 20px"] {
                bottom: 60px !important;
                right: 10px !important;
                font-size: 0.75rem !important;
                padding: 6px 10px !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)
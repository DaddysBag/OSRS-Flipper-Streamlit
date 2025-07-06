"""
Modern Results Table Component
Redesigned table that's easy to scan and mobile-friendly
"""

import streamlit as st
import pandas as pd
from utils import calculate_ge_tax, get_buy_limits


def create_modern_results_table(df, items_per_page=20):
    """Create a modern, scannable results table"""

    if df.empty:
        display_no_results()
        return

    # Process and display the table
    display_df = prepare_table_data(df)
    display_paginated_modern_table(display_df, items_per_page)


def prepare_table_data(df):
    """Prepare and enhance data for modern table display"""

    display_df = df.copy()

    # Create profit tiers for better visual grouping
    def get_profit_tier(margin):
        if margin >= 5000:
            return "🏆 EXCEPTIONAL"
        elif margin >= 2000:
            return "🥇 EXCELLENT"
        elif margin >= 1000:
            return "🥈 GOOD"
        elif margin >= 500:
            return "🥉 DECENT"
        else:
            return "⚠️ LOW"

    display_df['Profit Tier'] = display_df['Net Margin'].apply(get_profit_tier)

    # Create risk ratings
    def get_risk_rating(row):
        if 'Manipulation Score' in row and 'Volatility Score' in row:
            manip = row['Manipulation Score']
            vol = row['Volatility Score']

            if manip <= 3 and vol <= 4:
                return "🟢 SAFE"
            elif manip <= 5 and vol <= 6:
                return "🟡 MODERATE"
            else:
                return "🔴 HIGH RISK"
        else:
            # Fallback based on ROI and data age
            roi = row['ROI (%)']
            age = row['Data Age (min)']

            if roi >= 3 and age <= 3:
                return "🟢 SAFE"
            elif roi >= 1 and age <= 10:
                return "🟡 MODERATE"
            else:
                return "🔴 HIGH RISK"

    display_df['Risk Rating'] = display_df.apply(get_risk_rating, axis=1)

    # Create liquidity indicators
    def get_liquidity_level(volume):
        if volume >= 5000:
            return "🌊 HIGH"
        elif volume >= 1000:
            return "💧 MEDIUM"
        elif volume >= 500:
            return "💧 LOW"
        else:
            return "🏜️ VERY LOW"

    display_df['Liquidity'] = display_df['1h Volume'].apply(get_liquidity_level)

    # Format prices for readability
    display_df['Buy Price Formatted'] = display_df['Buy Price'].apply(lambda x: format_price(x))
    display_df['Sell Price Formatted'] = display_df['Sell Price'].apply(lambda x: format_price(x))
    display_df['Margin Formatted'] = display_df['Net Margin'].apply(lambda x: format_price(x))

    return display_df


def format_price(price):
    """Format prices for better readability"""
    if price >= 1_000_000:
        return f"{price / 1_000_000:.1f}M"
    elif price >= 1_000:
        return f"{price / 1_000:.0f}K"
    else:
        return f"{price:,.0f}"


def display_paginated_modern_table(df, items_per_page):
    """Display the modern table with pagination"""

    total_items = len(df)

    # Initialize pagination
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    total_pages = (total_items + items_per_page - 1) // items_per_page
    start_idx = st.session_state.current_page * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)

    # Table header with summary
    create_modern_table_header(total_items, df)

    # View options
    create_view_options()

    # Main table
    current_page_items = df.iloc[start_idx:end_idx]
    display_modern_table_cards(current_page_items)

    # Pagination
    create_modern_pagination(total_pages, total_items, start_idx, end_idx)


def create_modern_table_header(total_items, df):
    """Create modern table header with key insights"""

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(74, 144, 226, 0.1));
        border: 1px solid rgba(255, 215, 0, 0.3);
        border-radius: 16px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    ">
        <h2 style="color: #FFD700; margin-bottom: 10px;">🎯 Flip Opportunities</h2>
        <p style="color: #B0B8C5; margin-bottom: 15px;">
            Found <strong style="color: #FFD700;">{}</strong> profitable opportunities
        </p>
    </div>
    """.format(total_items), unsafe_allow_html=True)

    # Quick insights
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        exceptional_count = len(df[df['Net Margin'] >= 5000])
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: rgba(255, 215, 0, 0.1); border-radius: 12px; border: 1px solid rgba(255, 215, 0, 0.3);">
            <div style="font-size: 1.5rem;">🏆</div>
            <div style="color: #FFD700; font-weight: 600;">{exceptional_count}</div>
            <div style="color: #B0B8C5; font-size: 0.8rem;">EXCEPTIONAL</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        safe_count = len(df[df['Risk Rating'] == "🟢 SAFE"])
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: rgba(50, 205, 50, 0.1); border-radius: 12px; border: 1px solid rgba(50, 205, 50, 0.3);">
            <div style="font-size: 1.5rem;">🛡️</div>
            <div style="color: #32CD32; font-weight: 600;">{safe_count}</div>
            <div style="color: #B0B8C5; font-size: 0.8rem;">SAFE TRADES</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        avg_margin = df['Net Margin'].mean()
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: rgba(74, 144, 226, 0.1); border-radius: 12px; border: 1px solid rgba(74, 144, 226, 0.3);">
            <div style="font-size: 1.5rem;">💰</div>
            <div style="color: #4A90E2; font-weight: 600;">{format_price(avg_margin)}</div>
            <div style="color: #B0B8C5; font-size: 0.8rem;">AVG MARGIN</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        high_liquidity = len(df[df['Liquidity'].str.contains("HIGH")])
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: rgba(255, 140, 0, 0.1); border-radius: 12px; border: 1px solid rgba(255, 140, 0, 0.3);">
            <div style="font-size: 1.5rem;">🌊</div>
            <div style="color: #FF8C00; font-weight: 600;">{high_liquidity}</div>
            <div style="color: #B0B8C5; font-size: 0.8rem;">HIGH LIQUID</div>
        </div>
        """, unsafe_allow_html=True)


def create_view_options():
    """Create view and sorting options"""

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_term = st.text_input("🔍 Search items...", placeholder="Type item name", key="table_search")

    with col2:
        sort_by = st.selectbox("Sort by", ["Profit Margin", "ROI %", "Volume", "Risk Level"], key="table_sort")

    with col3:
        view_mode = st.selectbox("View", ["Cards", "Compact"], key="table_view")

    return search_term, sort_by, view_mode


def display_modern_table_cards(df):
    """Display items as modern cards instead of traditional table"""

    st.markdown('<div style="margin: 20px 0;">', unsafe_allow_html=True)

    for idx, (_, row) in enumerate(df.iterrows()):
        create_item_card(row, idx)

    st.markdown('</div>', unsafe_allow_html=True)


def create_item_card(row, idx):
    """Create a modern card for each item"""

    # Determine card accent color based on profit tier
    tier_colors = {
        "🏆 EXCEPTIONAL": "#FFD700",
        "🥇 EXCELLENT": "#32CD32",
        "🥈 GOOD": "#4A90E2",
        "🥉 DECENT": "#FF8C00",
        "⚠️ LOW": "#FF6B6B"
    }

    accent_color = tier_colors.get(row['Profit Tier'], "#4A90E2")

    # Create the card
    st.markdown(f"""
    <div style="
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-left: 4px solid {accent_color};
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        transition: all 0.3s ease;
        cursor: pointer;
    " onmouseover="this.style.background='rgba(255, 255, 255, 0.1)'; this.style.transform='translateY(-2px)'"
       onmouseout="this.style.background='rgba(255, 255, 255, 0.06)'; this.style.transform='translateY(0)'">

        <!-- Header Row -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <h3 style="color: #FFD700; margin: 0; font-size: 1.1rem; font-weight: 600;">
                    {row['Item']}
                </h3>
                <span style="
                    background: rgba(255, 215, 0, 0.2);
                    color: #FFD700;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 0.7rem;
                    font-weight: 500;
                ">
                    {row['Profit Tier']}
                </span>
            </div>
            <div style="display: flex; gap: 8px;">
                <span style="font-size: 0.8rem;">{row['Risk Rating']}</span>
                <span style="font-size: 0.8rem;">{row['Liquidity']}</span>
            </div>
        </div>

        <!-- Main Info Row -->
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px; margin-bottom: 15px;">
            <div>
                <div style="color: #B0B8C5; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Buy Price</div>
                <div style="color: #32CD32; font-weight: 600; font-size: 1rem;">{row['Buy Price Formatted']}</div>
            </div>
            <div>
                <div style="color: #B0B8C5; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Sell Price</div>
                <div style="color: #FF6B6B; font-weight: 600; font-size: 1rem;">{row['Sell Price Formatted']}</div>
            </div>
            <div>
                <div style="color: #B0B8C5; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Profit</div>
                <div style="color: {accent_color}; font-weight: 700; font-size: 1.1rem;">{row['Margin Formatted']}</div>
            </div>
            <div>
                <div style="color: #B0B8C5; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">ROI</div>
                <div style="color: #4A90E2; font-weight: 600; font-size: 1rem;">{row['ROI (%)']:.1f}%</div>
            </div>
        </div>

        <!-- Actions Row -->
        <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
            <div style="display: flex; gap: 10px; font-size: 0.8rem; color: #B0B8C5;">
                <span>Vol: {row['1h Volume']:,}</span>
                <span>•</span>
                <span>Age: {row['Data Age (min)']:.0f}m</span>
            </div>
            <div style="display: flex; gap: 8px;">
                <button style="
                    background: linear-gradient(135deg, #4A90E2, #357ABD);
                    border: none;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 8px;
                    font-size: 0.8rem;
                    cursor: pointer;
                    font-weight: 500;
                " onclick="selectItemForChart('{row['Item']}')">
                    📊 Chart
                </button>
                <button style="
                    background: linear-gradient(135deg, #FFD700, #B8860B);
                    border: none;
                    color: #1A1A2E;
                    padding: 6px 12px;
                    border-radius: 8px;
                    font-size: 0.8rem;
                    cursor: pointer;
                    font-weight: 500;
                " onclick="addToWatchlist('{row['Item']}')">
                    ⭐ Watch
                </button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_modern_pagination(total_pages, total_items, start_idx, end_idx):
    """Create modern pagination controls"""

    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⏮️ First", disabled=st.session_state.current_page == 0):
            st.session_state.current_page = 0
            st.rerun()

    with col2:
        if st.button("⬅️ Prev", disabled=st.session_state.current_page == 0):
            st.session_state.current_page = max(0, st.session_state.current_page - 1)
            st.rerun()

    with col3:
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 10px;
            background: rgba(255, 215, 0, 0.1);
            border-radius: 8px;
            border: 1px solid rgba(255, 215, 0, 0.3);
        ">
            <span style="color: #FFD700; font-weight: 600;">
                Page {st.session_state.current_page + 1} of {total_pages}
            </span>
            <br>
            <span style="color: #B0B8C5; font-size: 0.8rem;">
                Showing {start_idx + 1}-{end_idx} of {total_items} items
            </span>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        if st.button("➡️ Next", disabled=st.session_state.current_page >= total_pages - 1):
            st.session_state.current_page = min(total_pages - 1, st.session_state.current_page + 1)
            st.rerun()

    with col5:
        if st.button("⏭️ Last", disabled=st.session_state.current_page >= total_pages - 1):
            st.session_state.current_page = total_pages - 1
            st.rerun()


def display_no_results():
    """Display message when no results found"""

    st.markdown("""
    <div style="
        text-align: center;
        padding: 60px 20px;
        background: rgba(255, 255, 255, 0.03);
        border: 2px dashed rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        margin: 40px 0;
    ">
        <div style="font-size: 4rem; margin-bottom: 20px; opacity: 0.6;">🔍</div>
        <h3 style="color: #FFD700; margin-bottom: 15px;">No Opportunities Found</h3>
        <p style="color: #B0B8C5; margin-bottom: 25px; max-width: 400px; margin-left: auto; margin-right: auto;">
            Try adjusting your filters or enabling "Show All" to see more items
        </p>
        <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
            <div style="background: rgba(74, 144, 226, 0.1); padding: 10px 15px; border-radius: 8px; font-size: 0.9rem; color: #4A90E2;">
                💡 Lower minimum margin
            </div>
            <div style="background: rgba(74, 144, 226, 0.1); padding: 10px 15px; border-radius: 8px; font-size: 0.9rem; color: #4A90E2;">
                💡 Increase volume range
            </div>
            <div style="background: rgba(74, 144, 226, 0.1); padding: 10px 15px; border-radius: 8px; font-size: 0.9rem; color: #4A90E2;">
                💡 Try different time of day
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# JavaScript for interactive buttons (optional enhancement)
def inject_table_javascript():
    """Inject JavaScript for table interactions"""

    st.markdown("""
    <script>
    function selectItemForChart(itemName) {
        // This would integrate with Streamlit's session state
        console.log('Chart requested for:', itemName);
        // You can add Streamlit callbacks here
    }

    function addToWatchlist(itemName) {
        console.log('Add to watchlist:', itemName);
        // You can add Streamlit callbacks here
    }
    </script>
    """, unsafe_allow_html=True)
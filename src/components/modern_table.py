"""
Modern Results Table Component
Redesigned table that's easy to scan and mobile-friendly
"""

import streamlit as st
import pandas as pd

# Use relative imports to avoid issues
try:
    from utils import calculate_ge_tax, get_buy_limits
except ImportError:
    # Fallback for import issues
    def calculate_ge_tax(price):
        return min(int(price * 0.02), 5000000)

    def get_buy_limits():
        return {}


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
        return f"{price/1_000_000:.1f}M"
    elif price >= 1_000:
        return f"{price/1_000:.0f}K"
    else:
        return f"{price:,.0f}"


def display_paginated_modern_table(df, default_items_per_page=20):
    """Display the modern table with pagination"""

    total_items = len(df)

    # Initialize pagination
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    # Table header with summary
    create_modern_table_header(total_items, df)

    # View options (now returns items_per_page from user selection)
    search_term, sort_by, view_mode, items_per_page = create_view_options()

    # Apply search filter if provided
    if search_term:
        df = df[df['Item'].str.contains(search_term, case=False, na=False)]
        total_items = len(df)  # Update count after filtering

    total_pages = (total_items + items_per_page - 1) // items_per_page
    start_idx = st.session_state.current_page * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)

    # Reset page if we're beyond available pages after filtering
    if st.session_state.current_page >= total_pages and total_pages > 0:
        st.session_state.current_page = 0
        start_idx = 0
        end_idx = min(items_per_page, total_items)

        # Small visual separator
        st.markdown("<div style='margin: 8px 0; border-top: 1px solid rgba(255,255,255,0.1);'></div>",
                    unsafe_allow_html=True)

    # Main table
    current_page_items = df.iloc[start_idx:end_idx]
    display_modern_table_cards(current_page_items, start_idx)

    # Pagination
    create_modern_pagination(total_pages, total_items, start_idx, end_idx)


def create_modern_table_header(total_items, df):
    """Create compact table header with essential info"""

    # Compact single-line header with key stats
    exceptional_count = len(df[df['Net Margin'] >= 5000])
    safe_count = len(df[df['Risk Rating'] == "🟢 SAFE"]) if 'Risk Rating' in df.columns else 0
    avg_margin = df['Net Margin'].mean()
    high_liquidity = len(df[df['Liquidity'].str.contains("HIGH")]) if 'Liquidity' in df.columns else 0

    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, rgba(255, 215, 0, 0.08), rgba(74, 144, 226, 0.08));
        border: 1px solid rgba(255, 215, 0, 0.2);
        border-radius: 12px;
        padding: 16px 24px;
        margin: 16px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    ">
        <div style="color: #FFD700; font-weight: 600; font-size: 1.1rem;">
            🎯 {total_items} Opportunities
        </div>
        <div style="display: flex; gap: 24px; color: #B0B8C5; font-size: 0.9rem;">
            <span>🏆 {exceptional_count} Exceptional</span>
            <span>🛡️ {safe_count} Safe</span>
            <span>💰 {format_price(avg_margin)} Avg</span>
            <span>🌊 {high_liquidity} High Vol</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_view_options():
    """Create compact view and sorting options"""

    # Single row with all controls - more space efficient
    col1, col2, col3, col4 = st.columns([3, 1.5, 1, 1])

    with col1:
        search_term = st.text_input(
            "🔍 Search items...",
            placeholder="Type item name",
            key="table_search",
            label_visibility="collapsed"
        )

    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Profit Margin", "ROI %", "Volume", "Risk Level"],
            key="table_sort",
            label_visibility="collapsed"
        )

    with col3:
        view_mode = st.selectbox(
            "View",
            ["Cards", "Compact"],
            key="table_view",
            label_visibility="collapsed"
        )

    with col4:
        # Add items per page selector for better control
        items_per_page = st.selectbox(
            "Per Page",
            [10, 20, 30, 50],
            index=1,  # Default to 20
            key="items_per_page",
            label_visibility="collapsed"
        )

    return search_term, sort_by, view_mode, items_per_page


def display_modern_table_cards(df, start_idx):
    """Display items as cards or compact table based on view mode"""

    # Check view mode from session state (set by create_view_options)
    view_mode = st.session_state.get('table_view', 'Cards')

    if view_mode == 'Compact':
        display_compact_table(df, start_idx)
    else:
        # Original card view
        st.markdown("### 💎 Opportunities")
        for idx, (_, row) in enumerate(df.iterrows()):
            create_item_card(row, start_idx + idx)


def create_item_card(row, idx):
    """Create a simple, leak-proof card for each item"""

    # Determine card accent color based on profit tier
    tier_colors = {
        "🏆 EXCEPTIONAL": "#FFD700",
        "🥇 EXCELLENT": "#32CD32",
        "🥈 GOOD": "#4A90E2",
        "🥉 DECENT": "#FF8C00",
        "⚠️ LOW": "#FF6B6B"
    }

    accent_color = tier_colors.get(row['Profit Tier'], "#4A90E2")

    # Use Streamlit containers and columns for layout
    with st.container():
        # Card border with color
        st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-left: 4px solid {accent_color};
            border-radius: 12px;
            padding: 20px;
            margin: 12px 0;
        ">
        """, unsafe_allow_html=True)

        # Header row with item name and tier
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**🎯 {row['Item']}**")
        with col2:
            st.markdown(f"<span style='color: {accent_color}; font-size: 0.8rem;'>{row['Profit Tier']}</span>",
                       unsafe_allow_html=True)

        # Main info row using Streamlit metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Buy", row['Buy Price Formatted'])
        with col2:
            st.metric("Sell", row['Sell Price Formatted'])
        with col3:
            st.metric("Profit", row['Margin Formatted'], f"{row['ROI (%)']:.1f}%")
        with col4:
            st.metric("Volume", f"{row['1h Volume']:,}")

        # Action buttons row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("📊 Chart", key=f"chart_{idx}_{row['Item']}", help=f"View {row['Item']} chart"):
                st.session_state['selected_item'] = row['Item']
                st.session_state.page = 'charts'
                st.rerun()
        with col2:
            if st.button("⭐ Watch", key=f"watch_{idx}_{row['Item']}", help=f"Add {row['Item']} to watchlist"):
                if 'watchlist' not in st.session_state:
                    st.session_state.watchlist = []
                if row['Item'] not in st.session_state.watchlist:
                    st.session_state.watchlist.append(row['Item'])
                    st.success(f"Added {row['Item']} to watchlist!")
        with col3:
            st.write(f"**Age:** {row['Data Age (min)']:.0f}m")
        with col4:
            st.write(f"**Risk:** {row['Risk Rating']}")

        # Close the card div
        st.markdown("</div>", unsafe_allow_html=True)


def display_compact_table(df, start_idx):
    """Display items in a compact, dense table format"""

    st.markdown("### 📊 Trading Opportunities (Compact View)")

    # Create a streamlined dataframe for display
    display_data = []

    for idx, (_, row) in enumerate(df.iterrows()):
        # Format the data for compact display
        display_data.append({
            '🎯 Item': row['Item'],
            '💰 Buy': row['Buy Price Formatted'],
            '💰 Sell': row['Sell Price Formatted'],
            '📈 Profit': f"{row['Margin Formatted']} ({row['ROI (%)']:.1f}%)",
            '📊 Volume': f"{row['1h Volume']:,}",
            '⚡ Risk': row['Risk Rating'],
            '📋 Actions': f"chart_{start_idx + idx}|watch_{start_idx + idx}|{row['Item']}"
        })

    # Convert to dataframe for streamlit display
    compact_df = pd.DataFrame(display_data)

    # Display as streamlit dataframe with custom configuration
    st.dataframe(
        compact_df,
        use_container_width=True,
        hide_index=True,
        height=400,  # Fixed height for scrolling
        column_config={
            "📋 Actions": st.column_config.TextColumn(
                "Actions",
                help="Click to chart or watch items",
                width="medium"
            )
        }
    )

    # Add action buttons below table for selected items
    create_compact_action_buttons(df, start_idx)


def create_compact_action_buttons(df, start_idx):
    """Create action buttons for compact view"""

    st.markdown("#### ⚡ Quick Actions")

    # Item selector for actions
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_item = st.selectbox(
            "Select item for actions:",
            options=df['Item'].tolist(),
            key=f"compact_item_selector_{start_idx}"
        )

    with col2:
        if st.button("📊 Chart", key=f"compact_chart_{start_idx}"):
            if selected_item:
                st.session_state['selected_item'] = selected_item
                st.session_state.page = 'charts'
                st.rerun()

    with col3:
        if st.button("⭐ Watch", key=f"compact_watch_{start_idx}"):
            if selected_item:
                if 'watchlist' not in st.session_state:
                    st.session_state.watchlist = []
                if selected_item not in st.session_state.watchlist:
                    st.session_state.watchlist.append(selected_item)
                    st.success(f"Added {selected_item} to watchlist!")

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
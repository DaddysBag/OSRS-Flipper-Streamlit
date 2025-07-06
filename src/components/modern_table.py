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
            ["Compact", "Cards"],
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
    """Display enhanced professional table with sorting and better UX"""

    # Initialize sort and expansion state
    if 'table_sort_column' not in st.session_state:
        st.session_state.table_sort_column = 'Net Margin'
    if 'table_sort_direction' not in st.session_state:
        st.session_state.table_sort_direction = 'desc'
    if 'expanded_items' not in st.session_state:
        st.session_state.expanded_items = set()

    # Apply sorting
    sort_column = st.session_state.table_sort_column
    ascending = st.session_state.table_sort_direction == 'asc'

    # Map display names to column names
    sort_mapping = {
        'Item': 'Item',
        'Buy Price': 'Buy Price',
        'Sell Price': 'Sell Price',
        'Profit': 'Net Margin',
        'ROI': 'ROI (%)',
        'Volume': '1h Volume',
        'Risk': 'Risk Rating'
    }

    if sort_column in sort_mapping:
        try:
            df = df.sort_values(sort_mapping[sort_column], ascending=ascending)
        except:
            pass  # Fallback if sorting fails

    # Enhanced professional table header
    st.markdown("### 📊 Trading Opportunities (Professional View)")

    # Sort controls
    create_professional_sort_controls()

    # Professional table with glassmorphism
    create_professional_table_structure()

    # Table header
    create_professional_table_header()

    # Table rows
    for idx, (_, row) in enumerate(df.iterrows()):
        item_key = f"{start_idx}_{idx}_{row['Item']}"
        is_expanded = item_key in st.session_state.expanded_items
        create_professional_table_row(row, item_key, idx, is_expanded, start_idx)

    # Close table structure
    st.markdown("</div></div>", unsafe_allow_html=True)


def create_professional_sort_controls():
    """Create sorting controls matching Option 1 design"""

    st.markdown("""
    <div style="
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
        align-items: center;
        padding: 16px;
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
    ">
        <span style="color: #ccc; font-weight: 600; margin-right: 8px;">Sort by:</span>
    """, unsafe_allow_html=True)

    # Create sorting buttons with Option 1 styling
    sort_cols = st.columns([1, 1, 1, 1, 1, 1, 1])
    sort_options = ['Item', 'Buy Price', 'Sell Price', 'Profit', 'ROI', 'Volume', 'Risk']

    for i, option in enumerate(sort_options):
        with sort_cols[i]:
            is_active = st.session_state.table_sort_column == option
            direction = '↓' if st.session_state.table_sort_direction == 'desc' else '↑'

            # Apply Option 1 button styling
            button_style = """
            <style>
            .sort-btn {
                background: rgba(255,255,255,0.1) !important;
                border: 1px solid rgba(255,255,255,0.2) !important;
                border-radius: 6px !important;
                color: white !important;
                padding: 8px 16px !important;
                font-size: 0.85rem !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
                width: 100% !important;
            }
            .sort-btn:hover, .sort-btn.active {
                background: rgba(76,175,80,0.2) !important;
                border-color: rgba(76,175,80,0.4) !important;
            }
            </style>
            """
            st.markdown(button_style, unsafe_allow_html=True)

            if st.button(
                    f"{option} {direction if is_active else ''}",
                    key=f"sort_{option}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
            ):
                if st.session_state.table_sort_column == option:
                    # Toggle direction
                    st.session_state.table_sort_direction = 'asc' if st.session_state.table_sort_direction == 'desc' else 'desc'
                else:
                    # New column, default to desc for profit-related, asc for others
                    st.session_state.table_sort_column = option
                    st.session_state.table_sort_direction = 'desc' if option in ['Profit', 'ROI', 'Volume'] else 'asc'
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def create_professional_table_structure():
    """Create the main table structure matching Option 1 design"""

    st.markdown("""
    <style>
    .professional-table-container {
        background: rgba(0,0,0,0.3) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        border-collapse: collapse !important;
        width: 100% !important;
        margin: 16px 0 !important;
    }
    .professional-table-container .stColumns {
        background: transparent !important;
    }
    .professional-row:hover {
        background: rgba(255,255,255,0.03) !important;
        transition: all 0.2s ease !important;
    }
    </style>
    <div class="professional-table-container">
    """, unsafe_allow_html=True)


def create_professional_table_header():
    """Create the professional table header matching Option 1 design"""

    # Header with Option 1 styling
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(76,175,80,0.2), rgba(76,175,80,0.1));
        border-bottom: 2px solid rgba(76,175,80,0.3);
        padding: 12px 0;
        position: sticky;
        top: 0;
        z-index: 10;
    ">
    """, unsafe_allow_html=True)

    # Header columns with Option 1 styling
    header_cols = st.columns([2.5, 1.2, 1.2, 1.8, 1.3, 1.2, 1.5])
    headers = ['🎯 Item', '💰 Buy Price', '💸 Sell Price', '📈 Profit (ROI%)', '📊 Volume', '⚖️ Risk', 'Actions']

    for i, header in enumerate(headers):
        with header_cols[i]:
            st.markdown(f"""
            <div style="
                color: #fff;
                font-weight: 600;
                font-size: 0.95rem;
                text-align: left;
                padding: 0 16px;
                cursor: pointer;
                transition: all 0.2s ease;
            " 
            onmouseover="this.style.background='rgba(76,175,80,0.3)'"
            onmouseout="this.style.background='transparent'">
                {header}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def create_professional_table_row(row, item_key, idx, is_expanded, start_idx):
    """Create a professional table row matching Option 1 design"""

    # Determine profit-based styling for Option 1
    margin = row['Net Margin']
    if margin >= 5000:
        profit_color = "#FFD700"
        profit_class = "exceptional"
    elif margin >= 2000:
        profit_color = "#4CAF50"
        profit_class = "excellent"
    elif margin >= 1000:
        profit_color = "#2196F3"
        profit_class = "good"
    else:
        profit_color = "#FFA726"
        profit_class = "decent"

    # Row container with Option 1 styling
    st.markdown(f"""
    <div style="
        background: transparent;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        padding: 14px 0;
        transition: all 0.2s ease;
    " 
    onmouseover="this.style.background='rgba(255, 255, 255, 0.03)'"
    onmouseout="this.style.background='transparent'"
    class="professional-row profit-{profit_class}">
    """, unsafe_allow_html=True)

    # Table columns with Option 1 spacing
    row_cols = st.columns([2.5, 1.2, 1.2, 1.8, 1.3, 1.2, 1.5])

    # Item name - Option 1 styling
    with row_cols[0]:
        st.markdown(f"""
        <div style="
            color: #FFD700;
            font-weight: 600;
            font-size: 1rem;
            padding: 0 16px;
            text-align: left;
        ">
            {row['Item']}
        </div>
        """, unsafe_allow_html=True)

    # Buy price - Option 1 styling
    with row_cols[1]:
        st.markdown(f"""
        <div style="
            color: #4CAF50;
            font-weight: 500;
            font-size: 0.95rem;
            text-align: left;
            padding: 0 16px;
        ">
            {format_price(row['Buy Price'])}
        </div>
        """, unsafe_allow_html=True)

    # Sell price - Option 1 styling
    with row_cols[2]:
        st.markdown(f"""
        <div style="
            color: #FF6B6B;
            font-weight: 500;
            font-size: 0.95rem;
            text-align: left;
            padding: 0 16px;
        ">
            {format_price(row['Sell Price'])}
        </div>
        """, unsafe_allow_html=True)

    # Profit and ROI - Option 1 styling
    with row_cols[3]:
        st.markdown(f"""
        <div style="
            color: {profit_color};
            font-weight: 600;
            font-size: 0.95rem;
            text-align: left;
            padding: 0 16px;
        ">
            {format_price(margin)} ({row['ROI (%)']:.1f}%)
        </div>
        """, unsafe_allow_html=True)

    # Volume - Option 1 styling
    with row_cols[4]:
        st.markdown(f"""
        <div style="
            color: #81C784;
            font-weight: 400;
            font-size: 0.95rem;
            text-align: left;
            padding: 0 16px;
        ">
            {format_price(row['1h Volume'])}
        </div>
        """, unsafe_allow_html=True)

    # Risk - Option 1 badge styling
    with row_cols[5]:
        risk_rating = str(row.get('Risk Rating', 'N/A'))
        if "SAFE" in risk_rating:
            badge_bg = "linear-gradient(135deg, #4CAF50, #388E3C)"
            risk_text = "SAFE"
        elif "HIGH RISK" in risk_rating:
            badge_bg = "linear-gradient(135deg, #FF6B6B, #E53935)"
            risk_text = "HIGH RISK"
        else:
            badge_bg = "linear-gradient(135deg, #FF9800, #F57C00)"
            risk_text = "MODERATE"

        st.markdown(f"""
        <div style="
            background: {badge_bg};
            color: white;
            font-weight: 600;
            font-size: 0.8rem;
            text-align: center;
            padding: 4px 8px;
            border-radius: 12px;
            margin: 0 16px;
            display: inline-block;
            min-width: 60px;
        ">
            {risk_text}
        </div>
        """, unsafe_allow_html=True)

    # Actions - Option 1 button styling
    with row_cols[6]:
        action_cols = st.columns([1, 1])

        with action_cols[0]:
            # Chart button with Option 1 styling
            st.markdown("""
            <style>
            .chart-btn {
                background: linear-gradient(135deg, #2196F3, #1976D2) !important;
                color: white !important;
                border: none !important;
                border-radius: 6px !important;
                padding: 6px 12px !important;
                font-size: 0.85rem !important;
                font-weight: 500 !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
            }
            .chart-btn:hover {
                background: linear-gradient(135deg, #1976D2, #1565C0) !important;
                transform: translateY(-1px) !important;
            }
            </style>
            """, unsafe_allow_html=True)

            if st.button("📊 Chart", key=f"prof_chart_{item_key}", help="View Chart", use_container_width=True):
                st.session_state['selected_item'] = row['Item']
                st.session_state.page = 'charts'
                st.rerun()

        with action_cols[1]:
            # Expand button with Option 1 styling
            st.markdown("""
            <style>
            .expand-btn {
                background: linear-gradient(135deg, #9C27B0, #7B1FA2) !important;
                color: white !important;
                border: none !important;
                border-radius: 6px !important;
                padding: 6px 12px !important;
                font-size: 0.85rem !important;
                font-weight: 500 !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
            }
            .expand-btn:hover {
                background: linear-gradient(135deg, #7B1FA2, #6A1B9A) !important;
                transform: translateY(-1px) !important;
            }
            </style>
            """, unsafe_allow_html=True)

            expand_label = "📋 Details"
            if st.button(expand_label, key=f"prof_expand_{item_key}", help="Toggle Details", use_container_width=True):
                if is_expanded:
                    st.session_state.expanded_items.discard(item_key)
                else:
                    st.session_state.expanded_items.add(item_key)
                st.rerun()

    # Close row container
    st.markdown("</div>", unsafe_allow_html=True)

    # Show expanded details if needed
    if is_expanded:
        create_professional_row_expansion(row, item_key)


def create_professional_row_expansion(row, item_key):
    """Create professional expanded row details"""

    st.markdown(f"""
    <div style="
        background: rgba(0, 0, 0, 0.2);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        margin: 0;
    ">
    """, unsafe_allow_html=True)

    # Expanded details in columns
    detail_cols = st.columns([1, 1, 1, 1])

    with detail_cols[0]:
        st.markdown("**📊 Market Data**")
        if 'Data Age (min)' in row:
            st.write(f"Age: {row['Data Age (min)']:.0f}m")
        if 'Momentum (%)' in row:
            st.write(f"Momentum: {row['Momentum (%)']:.1f}%")

    with detail_cols[1]:
        st.markdown("**💰 Profit Analysis**")
        ge_tax = calculate_ge_tax(row['Sell Price']) if 'calculate_ge_tax' in globals() else 0
        net_after_tax = row['Net Margin'] - ge_tax
        st.write(f"Before Tax: {format_price(row['Net Margin'])}")
        st.write(f"After Tax: {format_price(net_after_tax)}")

    with detail_cols[2]:
        st.markdown("**⚖️ Risk Factors**")
        if 'Manipulation Score' in row:
            st.write(f"Manipulation: {row['Manipulation Score']}/10")
        if 'Volatility Score' in row:
            st.write(f"Volatility: {row['Volatility Score']}/10")

    with detail_cols[3]:
        st.markdown("**🎯 Trading Info**")
        if 'Season Ratio' in row:
            st.write(f"Season Ratio: {row['Season Ratio']:.2f}")
        if 'Utility' in row:
            st.write(f"Utility: {row['Utility']:,.0f}")

    st.markdown("</div>", unsafe_allow_html=True)


def get_profit_tier_class(margin):
    """Get profit tier class for CSS styling"""
    if margin >= 5000:
        return "exceptional"
    elif margin >= 2000:
        return "excellent"
    elif margin >= 1000:
        return "good"
    elif margin >= 500:
        return "decent"
    else:
        return "low"


def create_integrated_chart_actions(df, start_idx):
    """Create integrated chart actions below the table"""

    st.markdown("#### 📊 Quick Chart Access")

    # Create columns for quick chart buttons (3 items per row)
    items_per_row = 3
    item_list = df['Item'].tolist()

    for i in range(0, len(item_list), items_per_row):
        cols = st.columns(items_per_row)

        for j, col in enumerate(cols):
            if i + j < len(item_list):
                item_name = item_list[i + j]
                with col:
                    if st.button(
                            f"📊 {item_name[:15]}{'...' if len(item_name) > 15 else ''}",
                            key=f"chart_{start_idx}_{i + j}_{item_name}",
                            help=f"View {item_name} chart",
                            use_container_width=True
                    ):
                        st.session_state['selected_item'] = item_name
                        st.session_state.page = 'charts'
                        st.rerun()


def create_expandable_row_details():
    """Create expandable details section for selected table row"""

    st.markdown("---")
    st.markdown("#### 🔍 Item Details")

    # Initialize selected item in session state
    if 'selected_table_item' not in st.session_state:
        st.session_state.selected_table_item = None

    # Item selector
    col1, col2 = st.columns([3, 1])

    with col1:
        # Get current dataframe from session state if available
        if 'current_table_df' in st.session_state and not st.session_state.current_table_df.empty:
            df = st.session_state.current_table_df

            selected_item = st.selectbox(
                "Select item for detailed view:",
                options=['None'] + df['Item'].tolist(),
                key="expandable_item_selector",
                help="Choose an item to see detailed information"
            )

            if selected_item and selected_item != 'None':
                st.session_state.selected_table_item = selected_item

                # Get item details
                item_row = df[df['Item'] == selected_item].iloc[0]

                # Create expandable details
                with st.expander(f"📋 Detailed Analysis: {selected_item}", expanded=True):
                    create_detailed_item_view(item_row)

    with col2:
        if st.session_state.selected_table_item:
            if st.button("📊 View Chart", key="detail_chart_btn", type="primary"):
                st.session_state['selected_item'] = st.session_state.selected_table_item
                st.session_state.page = 'charts'
                st.rerun()


def create_detailed_item_view(item_row):
    """Create detailed view for selected item"""

    # Trading metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Buy Price", f"{item_row['Buy Price']:,} gp")
        st.metric("Sell Price", f"{item_row['Sell Price']:,} gp")

    with col2:
        st.metric("Net Profit", f"{item_row['Net Margin']:,} gp")
        st.metric("ROI", f"{item_row['ROI (%)']:.1f}%")

    with col3:
        st.metric("1h Volume", f"{item_row['1h Volume']:,}")
        if 'Data Age (min)' in item_row:
            st.metric("Data Age", f"{item_row['Data Age (min)']:.0f}m")

    # Risk assessment
    st.markdown("**🔍 Risk Analysis:**")
    risk_cols = st.columns(2)

    with risk_cols[0]:
        if 'Manipulation Score' in item_row:
            st.write(f"🔬 Manipulation Score: {item_row['Manipulation Score']}/10")
        if 'Volatility Score' in item_row:
            st.write(f"📊 Volatility Score: {item_row['Volatility Score']}/10")

    with risk_cols[1]:
        if 'Season Ratio' in item_row:
            st.write(f"🗓️ Season Ratio: {item_row['Season Ratio']:.2f}")
        if 'Utility' in item_row:
            st.write(f"⚡ Utility Score: {item_row['Utility']:,.0f}")


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
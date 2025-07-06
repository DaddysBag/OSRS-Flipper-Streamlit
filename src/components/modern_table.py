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
    """Display custom HTML table that mimics st.dataframe with expandable rows"""

    st.markdown("### 📊 Trading Opportunities (Compact View)")

    # Create the custom expandable table
    create_expandable_html_table(df, start_idx)


def create_expandable_html_table(df, start_idx):
    """Create custom HTML table with inline expandable rows"""

    # Generate unique table ID
    table_id = f"trading_table_{start_idx}"

    # Build table HTML
    table_html = f"""
    <div style="
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        overflow: hidden;
        max-height: 400px;
        overflow-y: auto;
        background: rgba(255, 255, 255, 0.04);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    ">
        <table id="{table_id}" style="
            width: 100%;
            border-collapse: collapse;
            font-family: 'Inter', sans-serif;
            background: transparent;
        ">
            <thead style="position: sticky; top: 0; z-index: 10;">
                <tr style="
                    background: rgba(255, 215, 0, 0.1);
                    color: #FFD700;
                    font-weight: 700;
                    font-size: 0.85rem;
                    text-transform: uppercase;
                    border-bottom: 2px solid rgba(255, 215, 0, 0.3);
                ">
                    <th style="padding: 16px 12px; text-align: left; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);">🎯 Item</th>
                    <th style="padding: 16px 12px; text-align: left; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);">💰 Buy</th>
                    <th style="padding: 16px 12px; text-align: left; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);">💸 Sell</th>
                    <th style="padding: 16px 12px; text-align: left; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);">📈 Profit</th>
                    <th style="padding: 16px 12px; text-align: left; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);">📊 Volume</th>
                    <th style="padding: 16px 12px; text-align: left; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);">⚖️ Risk</th>
                    <th style="padding: 16px 12px; text-align: center; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);">📊</th>
                    <th style="padding: 16px 12px; text-align: center; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);">▼</th>
                </tr>
            </thead>
            <tbody>
    """

    # Add rows
    for idx, (_, row) in enumerate(df.iterrows()):
        row_id = f"row_{start_idx}_{idx}"
        expanded_id = f"expanded_{start_idx}_{idx}"

        # Determine profit-based styling
        profit = row['Net Margin']
        if profit >= 5000:
            bg_color = "rgba(255, 215, 0, 0.12)"
            border_color = "#FFD700"
        elif profit >= 2000:
            bg_color = "rgba(76, 175, 80, 0.1)"
            border_color = "#4CAF50"
        elif profit >= 1000:
            bg_color = "rgba(74, 144, 226, 0.08)"
            border_color = "#4A90E2"
        else:
            bg_color = "rgba(255, 255, 255, 0.02)"
            border_color = "rgba(255, 255, 255, 0.1)"

        # Risk color
        risk_text = row['Risk Rating']
        if "SAFE" in risk_text:
            risk_color = "#4CAF50"
        elif "HIGH RISK" in risk_text:
            risk_color = "#FF6B6B"
        else:
            risk_color = "#FFC107"

        # Main row
        table_html += f"""
                <tr id="{row_id}" style="
                    background: {bg_color};
                    border-left: 3px solid {border_color};
                    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                    transition: all 0.2s ease;
                    cursor: pointer;
                " onmouseover="this.style.background='rgba(255, 215, 0, 0.08)'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 2px 8px rgba(255, 215, 0, 0.15)'"
                   onmouseout="this.style.background='{bg_color}'; this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                    <td style="padding: 14px 12px; color: #FFFFFF; font-weight: 600; font-size: 0.9rem; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);">{row['Item']}</td>
                    <td style="padding: 14px 12px; color: var(--text-primary); font-size: 0.9rem;">{row['Buy Price Formatted']}</td>
                    <td style="padding: 14px 12px; color: var(--text-primary); font-size: 0.9rem;">{row['Sell Price Formatted']}</td>
                    <td style="padding: 14px 12px; color: #FFD700; font-weight: 700; font-size: 0.9rem; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);">{row['Margin Formatted']} ({row['ROI (%)']:.1f}%)</td>
                    <td style="padding: 14px 12px; color: var(--text-primary); font-size: 0.9rem; font-family: 'JetBrains Mono', monospace; font-weight: 600;">{row['1h Volume']:,}</td>
                    <td style="padding: 14px 12px; color: {risk_color}; font-weight: 600; font-size: 0.9rem; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);">{risk_text}</td>
                    <td style="padding: 14px 12px; text-align: center;">
                        <button onclick="openChart('{row['Item']}')" style="
                            background: linear-gradient(135deg, #4A90E2, #74C0FC);
                            border: none;
                            border-radius: 6px;
                            color: white;
                            padding: 6px 10px;
                            font-size: 0.8rem;
                            cursor: pointer;
                            transition: all 0.2s ease;
                            font-weight: 600;
                        " onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 4px 12px rgba(74, 144, 226, 0.3)'"
                           onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none'">📊</button>
                    </td>
                    <td style="padding: 14px 12px; text-align: center;">
                        <button onclick="toggleRow('{expanded_id}', this)" style="
                            background: rgba(255, 255, 255, 0.1);
                            border: 1px solid rgba(255, 255, 255, 0.2);
                            border-radius: 6px;
                            color: #FFD700;
                            padding: 6px 10px;
                            font-size: 0.8rem;
                            cursor: pointer;
                            transition: all 0.2s ease;
                            font-weight: 600;
                        " onmouseover="this.style.background='rgba(255, 215, 0, 0.2)'"
                           onmouseout="this.style.background='rgba(255, 255, 255, 0.1)'">▼</button>
                    </td>
                </tr>
        """

        # Expanded row (hidden by default)
        table_html += f"""
                <tr id="{expanded_id}" style="display: none;">
                    <td colspan="8" style="
                        padding: 0;
                        background: rgba(255, 255, 255, 0.05);
                        border-left: 3px solid {border_color};
                    ">
                        <div style="
                            padding: 20px;
                            background: linear-gradient(135deg, {bg_color}, rgba(255, 255, 255, 0.02));
                            border: 1px solid rgba(255, 215, 0, 0.1);
                            margin: 8px;
                            border-radius: 8px;
                        ">
                            <h4 style="color: #FFD700; margin: 0 0 16px 0; font-size: 1rem;">🔍 {row['Item']} - Detailed Analysis</h4>

                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px;">
                                <div style="text-align: center; padding: 12px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;">
                                    <div style="color: #4CAF50; font-weight: 700; font-size: 1.2rem;">{row['Buy Price']:,}</div>
                                    <div style="color: #B0B8C5; font-size: 0.8rem;">💰 Buy Price</div>
                                </div>
                                <div style="text-align: center; padding: 12px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;">
                                    <div style="color: #4CAF50; font-weight: 700; font-size: 1.2rem;">{row['Sell Price']:,}</div>
                                    <div style="color: #B0B8C5; font-size: 0.8rem;">💸 Sell Price</div>
                                </div>
                                <div style="text-align: center; padding: 12px; background: rgba(255, 215, 0, 0.1); border-radius: 8px;">
                                    <div style="color: #FFD700; font-weight: 700; font-size: 1.2rem;">{row['Net Margin']:,}</div>
                                    <div style="color: #B0B8C5; font-size: 0.8rem;">📈 Net Profit</div>
                                </div>
                                <div style="text-align: center; padding: 12px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;">
                                    <div style="color: #74C0FC; font-weight: 700; font-size: 1.2rem;">{row['ROI (%)']:.1f}%</div>
                                    <div style="color: #B0B8C5; font-size: 0.8rem;">📊 ROI</div>
                                </div>
                            </div>

                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; color: #E0E0E0; font-size: 0.9rem;">
                                <div>
                                    <div style="margin-bottom: 8px;"><strong>📊 Volume/Hour:</strong> {row['1h Volume']:,}</div>
                                    <div style="margin-bottom: 8px;"><strong>⚖️ Risk Level:</strong> <span style="color: {risk_color};">{risk_text}</span></div>
                                    {f'<div style="margin-bottom: 8px;"><strong>⏰ Data Age:</strong> {row["Data Age (min)"]:.0f} minutes</div>' if 'Data Age (min)' in row else ''}
                                </div>
                                <div>
                                    {f'<div style="margin-bottom: 8px;"><strong>🔬 Manipulation Score:</strong> {row["Manipulation Score"]}/10</div>' if 'Manipulation Score' in row else ''}
                                    {f'<div style="margin-bottom: 8px;"><strong>📈 Volatility Score:</strong> {row["Volatility Score"]}/10</div>' if 'Volatility Score' in row else ''}
                                    {f'<div style="margin-bottom: 8px;"><strong>⚡ Utility Score:</strong> {row["Utility"]:,.0f}</div>' if 'Utility' in row else ''}
                                </div>
                            </div>

                            <div style="margin-top: 16px; text-align: center;">
                                <button onclick="addToWatchlist('{row['Item']}')" style="
                                    background: linear-gradient(135deg, #FF8C00, #FFB84D);
                                    border: none;
                                    border-radius: 8px;
                                    color: white;
                                    padding: 10px 20px;
                                    font-size: 0.9rem;
                                    cursor: pointer;
                                    font-weight: 600;
                                    margin: 0 8px;
                                    transition: all 0.2s ease;
                                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(255, 140, 0, 0.3)'"
                                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">⭐ Add to Watchlist</button>
                            </div>
                        </div>
                    </td>
                </tr>
        """

    table_html += """
            </tbody>
        </table>
    </div>

    <script>
        function toggleRow(expandedId, button) {
            const expandedRow = document.getElementById(expandedId);
            if (expandedRow.style.display === 'none') {
                expandedRow.style.display = 'table-row';
                button.innerHTML = '▲';
                button.style.background = 'rgba(255, 215, 0, 0.2)';
            } else {
                expandedRow.style.display = 'none';
                button.innerHTML = '▼';
                button.style.background = 'rgba(255, 255, 255, 0.1)';
            }
        }

        function openChart(itemName) {
            // This will be handled by Streamlit's session state
            window.parent.postMessage({
                type: 'streamlit:componentReady',
                data: {
                    action: 'chart',
                    item: itemName
                }
            }, '*');
        }

        function addToWatchlist(itemName) {
            // This will be handled by Streamlit's session state
            window.parent.postMessage({
                type: 'streamlit:componentReady', 
                data: {
                    action: 'watchlist',
                    item: itemName
                }
            }, '*');
        }
    </script>
    """

    # Display the custom table
    st.markdown(table_html, unsafe_allow_html=True)

    # Handle chart and watchlist actions via form submission
    create_action_handlers(df, start_idx)


def create_action_handlers(df, start_idx):
    """Create hidden form handlers for chart and watchlist actions"""

    # Chart action handler
    with st.form(key=f"chart_handler_{start_idx}", clear_on_submit=True):
        chart_item = st.selectbox(
            "Chart Item",
            options=[''] + df['Item'].tolist(),
            key=f"chart_item_{start_idx}",
            label_visibility="collapsed"
        )
        chart_submitted = st.form_submit_button("Open Chart", style={"display": "none"})

        if chart_submitted and chart_item:
            st.session_state['selected_item'] = chart_item
            st.session_state.page = 'charts'
            st.rerun()

    # Watchlist action handler
    with st.form(key=f"watchlist_handler_{start_idx}", clear_on_submit=True):
        watch_item = st.selectbox(
            "Watchlist Item",
            options=[''] + df['Item'].tolist(),
            key=f"watch_item_{start_idx}",
            label_visibility="collapsed"
        )
        watch_submitted = st.form_submit_button("Add to Watchlist", style={"display": "none"})

        if watch_submitted and watch_item:
            if 'watchlist' not in st.session_state:
                st.session_state.watchlist = []
            if watch_item not in st.session_state.watchlist:
                st.session_state.watchlist.append(watch_item)
                st.success(f"✅ Added {watch_item} to watchlist!")


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
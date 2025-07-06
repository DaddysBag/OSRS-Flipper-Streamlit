"""
Interactive Tools Component
Contains profit calculator, export options, and other utility tools
"""

import streamlit as st
import pandas as pd
import datetime
import json
from utils import calculate_ge_tax


def create_profit_calculator():
    """Create a real-time profit calculator"""

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    ">
        <h3 style="color: #4CAF50; margin-bottom: 15px;">💰 Real-Time Profit Calculator</h3>
    </div>
    """, unsafe_allow_html=True)

    # Calculator inputs
    col1, col2, col3 = st.columns(3)

    with col1:
        buy_price = st.number_input("Buy Price (gp)", min_value=1, value=1000, step=1, key="calc_buy")

    with col2:
        sell_price = st.number_input("Sell Price (gp)", min_value=1, value=1100, step=1, key="calc_sell")

    with col3:
        quantity = st.number_input("Quantity", min_value=1, value=100, step=1, key="calc_qty")

    # Calculate results
    tax = calculate_ge_tax(sell_price)
    net_profit_per_item = sell_price - buy_price - tax
    total_profit = net_profit_per_item * quantity
    roi = (net_profit_per_item / buy_price) * 100 if buy_price > 0 else 0

    # Display results
    st.markdown("**💰 Results:**")
    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.metric("Net Profit/Item", f"{net_profit_per_item:,} gp")
    with col_b:
        st.metric("Total Profit", f"{total_profit:,} gp")
    with col_c:
        st.metric("ROI", f"{roi:.1f}%")
    with col_d:
        st.metric("GE Tax", f"{tax:,} gp")

    # Assessment with styling
    if roi >= 5:
        st.markdown(f"""
        <div style="background: rgba(40, 167, 69, 0.1); border: 1px solid rgba(40, 167, 69, 0.3);
                    border-radius: 8px; padding: 15px; margin: 10px 0; color: #28a745;
                    text-align: center; font-weight: 500;">
            🟢 <strong>Excellent opportunity!</strong> {roi:.1f}% ROI
        </div>
        """, unsafe_allow_html=True)
    elif roi >= 2:
        st.markdown(f"""
        <div style="background: rgba(255, 193, 7, 0.1); border: 1px solid rgba(255, 193, 7, 0.3);
                    border-radius: 8px; padding: 15px; margin: 10px 0; color: #ffc107;
                    text-align: center; font-weight: 500;">
            🟡 <strong>Good opportunity!</strong> {roi:.1f}% ROI
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: rgba(220, 53, 69, 0.1); border: 1px solid rgba(220, 53, 69, 0.3);
                    border-radius: 8px; padding: 15px; margin: 10px 0; color: #dc3545;
                    text-align: center; font-weight: 500;">
            🔴 <strong>Low profit margin</strong> - {roi:.1f}% ROI
        </div>
        """, unsafe_allow_html=True)


def create_export_options(df):
    """Create advanced export options"""

    if df.empty:
        return

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    ">
        <h3 style="color: #4CAF50; margin-bottom: 15px;">📥 Export Options</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # CSV Export
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📊 Export CSV",
            data=csv_data,
            file_name=f"osrs_opportunities_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            help="Download as Excel-compatible CSV",
            use_container_width=True
        )

    with col2:
        # JSON Export
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            label="📋 Export JSON",
            data=json_data,
            file_name=f"osrs_opportunities_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            help="Download as JSON for API use",
            use_container_width=True
        )

    with col3:
        # Top 10 Export
        top_10 = df.head(10)
        top_10_csv = top_10.to_csv(index=False)
        st.download_button(
            label="🏆 Top 10 CSV",
            data=top_10_csv,
            file_name=f"osrs_top_10_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            help="Download top 10 opportunities",
            use_container_width=True
        )

    with col4:
        # Watchlist Export
        if st.session_state.get('watchlist'):
            watchlist_df = df[df['Item'].isin(st.session_state.watchlist)]
            if not watchlist_df.empty:
                watchlist_csv = watchlist_df.to_csv(index=False)
                st.download_button(
                    label="⭐ Watchlist CSV",
                    data=watchlist_csv,
                    file_name=f"osrs_watchlist_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    help="Download watchlist items",
                    use_container_width=True
                )
            else:
                st.button("⭐ Watchlist CSV", disabled=True, help="No watchlist items in current results")
        else:
            st.button("⭐ Watchlist CSV", disabled=True, help="Watchlist is empty")


def create_watchlist_manager():
    """Create advanced watchlist management"""

    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    ">
        <h3 style="color: #4CAF50; margin-bottom: 15px;">⭐ Watchlist Manager</h3>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.watchlist:
        st.write(f"**📋 Watching {len(st.session_state.watchlist)} items:**")

        # Display watchlist in a nice format
        for i, item in enumerate(st.session_state.watchlist):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {item}")
            with col2:
                if st.button("❌", key=f"remove_watch_{i}", help=f"Remove {item}"):
                    st.session_state.watchlist.remove(item)
                    st.rerun()

        # Clear all button
        if st.button("🗑️ Clear All Watchlist", type="secondary"):
            st.session_state.watchlist = []
            show_success_message("Watchlist cleared!")
            st.rerun()
    else:
        st.info("📝 No items in watchlist. Click ⭐ Watch buttons to add items!")

    return st.session_state.watchlist


def create_quick_chart_access(df):
    """Create quick chart access interface"""

    st.subheader("📊 Quick Chart Access")

    # Create a user-friendly interface with search
    col1, col2 = st.columns([3, 1])

    with col1:
        # Add search functionality
        search_term = st.text_input("🔍 Search for item to chart:",
                                    placeholder="Type item name...",
                                    key="chart_search")

        # Filter items based on search
        if search_term:
            filtered_items = [item for item in df['Item'].tolist()
                              if search_term.lower() in item.lower()]
        else:
            filtered_items = df['Item'].tolist()

        # Show filtered selection
        if filtered_items:
            selected_item = st.selectbox(
                f"Select from {len(filtered_items)} items:",
                options=filtered_items,
                key="enhanced_item_selector",
                help="Select an item to view its detailed price chart"
            )
        else:
            st.warning("No items match your search")
            selected_item = None

    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        if selected_item:
            if st.button(f"📈 Chart {selected_item}", type="primary", use_container_width=True):
                st.session_state['selected_item'] = selected_item
                st.session_state.page = 'charts'
                st.rerun()

    # Quick access buttons for top items
    if len(df) > 0:
        st.write("**🚀 Quick Access - Top Opportunities:**")

        # Show top 5 items as quick buttons
        top_items = df.head(5)['Item'].tolist()

        # Create columns for buttons
        button_cols = st.columns(min(len(top_items), 5))

        for i, item in enumerate(top_items):
            with button_cols[i]:
                if st.button(f"📊 {item[:15]}{'...' if len(item) > 15 else ''}",
                             key=f"quick_chart_{i}_{item}",
                             help=f"View chart for {item}",
                             use_container_width=True):
                    st.session_state['selected_item'] = item
                    st.session_state.page = 'charts'
                    st.rerun()


def show_success_message(message, icon="✅"):
    """Show a beautiful success message"""
    st.markdown(f"""
    <div style="background: rgba(40, 167, 69, 0.1); border: 1px solid rgba(40, 167, 69, 0.3);
                border-radius: 8px; padding: 15px; margin: 10px 0; color: #28a745;
                text-align: center; font-weight: 500;">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)


def show_warning_message(message, icon="⚠️"):
    """Show a beautiful warning message"""
    st.markdown(f"""
    <div style="background: rgba(255, 193, 7, 0.1); border: 1px solid rgba(255, 193, 7, 0.3);
                border-radius: 8px; padding: 15px; margin: 10px 0; color: #ffc107;
                text-align: center; font-weight: 500;">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)
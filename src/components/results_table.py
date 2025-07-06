"""
Results Table Component
Handles the display of flip opportunities in a table format
"""

import streamlit as st
import pandas as pd
from utils import calculate_ge_tax, get_buy_limits
from src.utils.error_handler import safe_execute, ErrorHandler


def create_table_header(total_items, avg_margin, avg_risk_util):
    """Create enhanced table header with summary info"""

    st.markdown("""
    <div class="results-container">
        <div class="table-header">
            <h2>🔍 Top Flip Opportunities</h2>
            <p>Real-time market analysis with risk assessment</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Items", total_items)

    with col2:
        st.metric("Avg Margin", f"{avg_margin:,.0f} gp")

    with col3:
        st.metric("Avg Risk Adj. Utility", f"{avg_risk_util:,.0f}")

    with col4:
        safe_items = "📊 Processing..."
        st.metric("Analysis", safe_items)


def process_dataframe_for_display(df):
    """Process the dataframe to add display columns and formatting"""

    if df.empty:
        return df

    display_df = df.copy()
    limits = get_buy_limits()

    # Add color coding based on ROI and data age
    def get_enhanced_color_code(row):
        roi, data_age, volume = row['ROI (%)'], row['Data Age (min)'], row['1h Volume']

        # Check if enhanced columns exist
        if 'Manipulation Score' in row and 'Volatility Score' in row:
            manipulation, volatility = row['Manipulation Score'], row['Volatility Score']

            # Enhanced status with detailed categories
            if manipulation >= 7 or volatility >= 8:
                return "🔴 High Risk"
            elif data_age > 5:
                return "🔴 Stale Data"
            elif data_age > 2:
                return "🟡 Aging Data"
            elif roi >= 5 and volume >= 1000 and manipulation <= 3 and volatility <= 4:
                return "🟢 Excellent"
            elif roi >= 2 and volume >= 500:
                return "🟡 Good"
            else:
                return "🔴 Caution"
        else:
            # Fall back to original logic if enhanced columns don't exist
            if data_age > 5:
                return "🔴 Stale Data"
            elif data_age > 2:
                return "🟡 Aging Data"
            elif roi >= 5 and volume >= 1000:
                return "🟢 Excellent"
            elif roi >= 2 and volume >= 500:
                return "🟡 Good"
            else:
                return "🔴 Caution"

    # Apply enhanced status badges
    def create_status_badge(row):
        status = get_enhanced_color_code(row)
        if "Excellent" in status:
            return "🟢 EXCELLENT"
        elif "Good" in status:
            return "🟡 GOOD"
        else:
            return "🔴 CAUTION"

    display_df['Status'] = display_df.apply(create_status_badge, axis=1)

    # Enhanced data freshness indicators
    def format_price_with_freshness(price, age_minutes):
        if age_minutes <= 1:
            freshness_icon = "🟢"
        elif age_minutes <= 3:
            freshness_icon = "🟡"
        else:
            freshness_icon = "🔴"
        return f'{freshness_icon} {price:,} gp <small>({age_minutes:.1f}m ago)</small>'

    display_df['Approx. Offer Price'] = display_df.apply(
        lambda row: format_price_with_freshness(row['Buy Price'], row['Low Age (min)']),
        axis=1)
    display_df['Approx. Sell Price'] = display_df.apply(
        lambda row: format_price_with_freshness(row['Sell Price'], row['High Age (min)']),
        axis=1)
    display_df['Tax'] = display_df['Sell Price'].apply(lambda x: f"{calculate_ge_tax(x):,}")
    display_df['GE Limit'] = display_df['Item'].apply(
        lambda x: f"{limits.get(x, 'N/A'):,}" if limits.get(x) else "N/A")

    # Add Chart column
    display_df['Quick Actions'] = display_df['Item'].apply(lambda x: "📊 Chart | ⭐ Watch | 📋 Copy")

    return display_df

def display_paginated_table(df, items_per_page=25):
    """Display results using the new modern table design with error handling"""

    try:
        # Check if we have valid data first
        if df is None:
            st.error("📊 **Table Error**: No data provided")
            return

        if df.empty:
            st.info("📭 **No Results**: No flip opportunities found with current filters")
            st.markdown("💡 **Try:** Lowering your filter requirements or enabling 'Show All'")
            return

        # Import the new modern table
        from src.components.modern_table import create_modern_results_table

        # Use the new modern table with error handling
        create_modern_results_table(df, items_per_page)

    except ImportError as e:
        st.error(f"📊 **Table Component Error**: {e}")
        st.info("💡 **Fallback**: Showing basic table instead")

        # Fallback to simple table display
        try:
            st.dataframe(df.head(items_per_page), use_container_width=True)
        except Exception as fallback_error:
            st.error(f"❌ **Display Failed**: {fallback_error}")

    except Exception as e:
        ErrorHandler.handle_ui_error(e, "Table Display")

        # Show basic fallback table
        st.markdown("### 📊 Basic Results Table")
        try:
            # Show just essential columns if full table fails
            essential_cols = ['Item', 'Buy Price', 'Sell Price', 'Net Margin', 'ROI (%)']
            available_cols = [col for col in essential_cols if col in df.columns]

            if available_cols:
                st.dataframe(df[available_cols].head(items_per_page), use_container_width=True)
            else:
                st.dataframe(df.head(items_per_page), use_container_width=True)

        except Exception as final_error:
            st.error(f"❌ **Critical Table Error**: {final_error}")
            st.info("🔄 Please refresh the page or clear cache to resolve this issue")


def display_full_table(df):
    """Display the full table in scrollable format with error handling"""

    try:
        if df is None or df.empty:
            st.warning("📭 No data available for full table view")
            return

        st.markdown("---")
        st.subheader("📊 All Items - Scrollable Table")

        column_config = create_column_config()

        st.dataframe(
            df,
            use_container_width=True,
            key="all_items_table",
            height=600,
            hide_index=True,
            column_config=column_config
        )

        # Quick chart access
        st.markdown("---")
        st.subheader("📈 Quick Chart Access")

        search_item = st.text_input("🔍 Search for item to chart:",
                                    placeholder="Type exact item name...",
                                    key="full_table_search")

        if search_item:
            try:
                matching_items = df[df['Item'].str.contains(search_item, case=False, na=False)]
                if not matching_items.empty:
                    for _, row in matching_items.head(5).iterrows():
                        if st.button(f"📊 {row['Item']}", key=f"full_search_{row['Item']}"):
                            st.session_state['selected_item'] = row['Item']
                            st.session_state.page = 'charts'
                            st.rerun()
                else:
                    st.warning("No items found matching your search.")
            except Exception as search_error:
                st.error(f"🔍 Search error: {search_error}")

        # Back to paginated view
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📄 ⬅️ Back to Paginated View", type="primary", use_container_width=True):
                st.session_state['show_all_table'] = False
                st.rerun()

    except Exception as e:
        ErrorHandler.handle_ui_error(e, "Full Table Display")
        st.info("💡 Try using the paginated view instead")


def display_table_page(df, start_idx, end_idx, total_pages, total_items):
    """Display a single page of the table"""

    current_page_items = df.iloc[start_idx:end_idx]

    # Table headers
    header_cols = st.columns([0.4, 2, 1, 1, 1.2, 1, 1, 1.5, 1.2, 1.2, 1.2, 1.2])
    headers = ['Status', 'Item Name', 'Buy Price', 'Sell Price', 'Net Margin', 'ROI (%)',
               '1h Volume', 'Risk Adj. Utility', 'Manip. Risk', 'Volatility', 'Tax', 'GE Limit']

    for i, header in enumerate(headers):
        if i < len(header_cols):
            header_cols[i].markdown(f"**{header}**")

    st.markdown("---")

    # Display table rows
    for idx, (_, row) in enumerate(current_page_items.iterrows()):
        with st.container():
            cols = st.columns([0.4, 2, 1, 1, 1.2, 1, 1, 1.5, 1.2, 1.2, 1.2, 1.2])

            cols[0].write(row['Status'])

            # Clickable item name
            with cols[1]:
                if st.button(
                        row['Item'],
                        key=f"item_page_{st.session_state.current_page}_idx_{idx}_{hash(row['Item'])}",
                        help=f"Click to view {row['Item']} chart",
                        use_container_width=True
                ):
                    st.session_state['selected_item'] = row['Item']
                    st.session_state.page = 'charts'
                    st.rerun()

            # Display other columns
            cols[2].write(f"{row['Buy Price']:,}")
            cols[3].write(f"{row['Sell Price']:,}")
            cols[4].write(f"**{row['Net Margin']:,}**")

            roi_color = "🟢" if row['ROI (%)'] >= 5 else "🟡" if row['ROI (%)'] >= 2 else "🔴"
            cols[5].write(f"{roi_color} {row['ROI (%)']:.1f}%")

            cols[6].write(f"{row['1h Volume']:,}")
            cols[7].write(f"{row['Risk Adjusted Utility']:,.0f}")

            risk = row.get('Manipulation Risk', 'N/A')
            risk_color = "🟢" if risk == "Normal" else "🟡" if risk == "Low" else "🔴"
            cols[8].write(f"{risk_color} {risk}")

            vol = row.get('Volatility Level', 'N/A')
            vol_color = "🟢" if "Low" in str(vol) else "🟡" if "Medium" in str(vol) else "🔴"
            cols[9].write(f"{vol_color} {vol}")

            cols[10].write(row['Tax'])
            cols[11].write(row['GE Limit'])

    # Pagination controls
    display_pagination_controls(total_pages, total_items, start_idx, end_idx)


def display_pagination_controls(total_pages, total_items, start_idx, end_idx):
    """Display pagination controls"""

    st.markdown("---")
    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])

    with col1:
        if st.button("⬅️ Prev", disabled=st.session_state.current_page == 0):
            st.session_state.current_page = max(0, st.session_state.current_page - 1)
            st.rerun()

    with col2:
        if st.button("➡️ Next", disabled=st.session_state.current_page >= total_pages - 1):
            st.session_state.current_page = min(total_pages - 1, st.session_state.current_page + 1)
            st.rerun()

    with col3:
        st.markdown(f"""
        <div style="text-align: center; color: #4CAF50; font-weight: 500; padding: 8px;">
        📄 Page {st.session_state.current_page + 1} of {total_pages} 
        <span style="color: #bbb;">({start_idx + 1}-{end_idx} of {total_items} items)</span>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("⏮️ First", disabled=st.session_state.current_page == 0):
                st.session_state.current_page = 0
                st.rerun()
        with col_b:
            if st.button("⏭️ Last", disabled=st.session_state.current_page >= total_pages - 1):
                st.session_state.current_page = total_pages - 1
                st.rerun()


def create_column_config():
    """Create column configuration for dataframe display with error handling"""

    try:
        return {
            'Buy Price': st.column_config.NumberColumn(
                'Buy Price',
                help='Current buy price',
                format='%d gp'
            ),
            'Sell Price': st.column_config.NumberColumn(
                'Sell Price',
                help='Current sell price',
                format='%d gp'
            ),
            'Net Margin': st.column_config.NumberColumn(
                'Net Margin',
                help='Profit after GE tax',
                format='%d gp'
            ),
            'ROI (%)': st.column_config.NumberColumn(
                'ROI (%)',
                help='Return on investment',
                format='%.1f%%'
            ),
            '1h Volume': st.column_config.NumberColumn(
                '1h Volume',
                help='Trading volume per hour',
                format='%d'
            ),
            'Risk Adjusted Utility': st.column_config.NumberColumn(
                'Risk Adj. Utility',
                help='Risk-adjusted utility score',
                format='%.0f'
            )
        }
    except Exception as e:
        # Return empty config if there's an error
        st.warning(f"⚠️ Column formatting unavailable: {e}")
        return {}
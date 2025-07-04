"""
OSRS Charts Module
Chart creation functions for price visualization
"""

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd


def create_enhanced_chart(ts, item_name, chart_type, height, width,
                          color_high, color_low, color_volume,
                          line_width, show_grid, show_volume, volume_opacity):
    """Create enhanced matplotlib chart with dark theme"""
    plt.style.use('dark_background')
    fig, axes = (plt.subplots(2, 1, figsize=(width / 100, height / 100),
                              gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
                 if show_volume else
                 (plt.subplots(figsize=(width / 100, height / 100))))
    if show_volume:
        ax1, ax2 = axes
        ax2.set_facecolor('#2b2b2b')
    else:
        ax1 = axes
    fig.patch.set_facecolor('#1f1f1f')
    ax1.set_facecolor('#2b2b2b')

    # Price lines with markers
    ax1.plot(ts['timestamp'], ts['high'], marker='o', markersize=4,
             label='Sell', color=color_high, linewidth=line_width)
    ax1.plot(ts['timestamp'], ts['low'], marker='o', markersize=4,
             label='Buy', color=color_low, linewidth=line_width)

    # Rolling-average trend
    ts['mid'] = (ts['high'] + ts['low']) / 2
    trend = ts['mid'].rolling(window=10, min_periods=1).mean()
    ax1.plot(ts['timestamp'], trend, linestyle='--', linewidth=1,
             color='#bdc3c7', alpha=0.7, label='Trend')

    # Volume bars
    if show_volume:
        ax2.bar(
            ts['timestamp'],
            ts['volume'],
            alpha=volume_opacity,
            color=color_volume,
            width=0.02,
            label='Volume'
        )

    # Styling
    for ax in (ax1, ax2) if show_volume else (ax1,):
        if show_grid:
            ax.grid(True, linestyle='--', alpha=0.3)
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('#444')

    ax1.set_ylabel('Price (gp)', color='white', fontsize=12)
    if show_volume:
        ax2.set_ylabel('Volume', color='white', fontsize=10)
        ax2.set_xlabel('Time', color='white')
    else:
        ax1.set_xlabel('Time', color='white')

    ax1.legend(loc='upper left', frameon=False)
    if show_volume:
        ax2.legend(loc='upper right', frameon=False)

    # Date formatting
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    fig.autofmt_xdate()

    # Title & layout
    ax1.set_title(f'{item_name}', color='white', pad=12)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def create_interactive_chart(ts: pd.DataFrame,
                             item_name: str,
                             width: int = 800,
                             height: int = 500,
                             show_time_controls: bool = True,
                             current_timestep: str = "1h"):
    """Create enhanced interactive Plotly chart with time period controls"""

    # Time period controls at the top
    if show_time_controls:
        st.subheader("📅 Time Period Selection")

        # Create time period buttons
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])

        time_periods = {
            "Day": {"timestep": "5m", "emoji": "📊", "desc": "5-minute intervals"},
            "Week": {"timestep": "1h", "emoji": "📈", "desc": "Hourly intervals"},
            "Month": {"timestep": "6h", "emoji": "📉", "desc": "6-hour intervals"},
            "Year": {"timestep": "24h", "emoji": "📋", "desc": "Daily intervals"}
        }

        # Track which button was clicked
        selected_period = None

        with col1:
            if st.button(f"{time_periods['Day']['emoji']} Day",
                         type="primary" if current_timestep == "5m" else "secondary",
                         help=time_periods['Day']['desc'],
                         use_container_width=True):
                selected_period = "Day"

        with col2:
            if st.button(f"{time_periods['Week']['emoji']} Week",
                         type="primary" if current_timestep == "1h" else "secondary",
                         help=time_periods['Week']['desc'],
                         use_container_width=True):
                selected_period = "Week"

        with col3:
            if st.button(f"{time_periods['Month']['emoji']} Month",
                         type="primary" if current_timestep == "6h" else "secondary",
                         help=time_periods['Month']['desc'],
                         use_container_width=True):
                selected_period = "Month"

        with col4:
            if st.button(f"{time_periods['Year']['emoji']} Year",
                         type="primary" if current_timestep == "24h" else "secondary",
                         help=time_periods['Year']['desc'],
                         use_container_width=True):
                selected_period = "Year"

        with col5:
            # Show current selection info
            current_desc = next((info['desc'] for period, info in time_periods.items()
                                 if info['timestep'] == current_timestep), "Unknown")
            st.info(f"📍 Current: {current_desc}")

        # Handle time period changes
        if selected_period:
            new_timestep = time_periods[selected_period]['timestep']
            if new_timestep != current_timestep:
                st.session_state['chart_timestep'] = new_timestep
                st.session_state['chart_reload_needed'] = True
                st.rerun()

    # Data validation
    if ts is None or ts.empty:
        st.error("📊 No chart data available")
        return

    # Ensure timestamp column is datetime
    ts['timestamp'] = pd.to_datetime(ts['timestamp'])

    # Create enhanced chart
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],  # Price chart takes 75%, volume takes 25%
        vertical_spacing=0.02,
        subplot_titles=['Price Chart', 'Volume']
    )

    # Professional Price Traces - GE Tracker Colors
    fig.add_trace(
        go.Scatter(
            x=ts['timestamp'],
            y=ts['high'],
            mode='lines+markers',
            name='Sell Price',
            line=dict(
                color='#ff6b6b',  # Professional red
                width=2.5,
                shape='spline',  # Smooth curves
                smoothing=0.3
            ),
            marker=dict(
                size=4,
                color='#ff6b6b',
                symbol='circle',
                line=dict(width=1, color='#ffffff')
            ),
            hovertemplate='<b>🔴 Sell Price</b><br>' +
                          'Price: <b>%{y:,.0f} gp</b><br>' +
                          'Time: %{x|%b %d, %H:%M}<br>' +
                          '<extra></extra>'
        ), row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=ts['timestamp'],
            y=ts['low'],
            mode='lines+markers',
            name='Buy Price',
            line=dict(
                color='#51cf66',  # Professional green
                width=2.5,
                shape='spline',
                smoothing=0.3
            ),
            marker=dict(
                size=4,
                color='#51cf66',
                symbol='circle',
                line=dict(width=1, color='#ffffff')
            ),
            hovertemplate='<b>🟢 Buy Price</b><br>' +
                          'Price: <b>%{y:,.0f} gp</b><br>' +
                          'Time: %{x|%b %d, %H:%M}<br>' +
                          '<extra></extra>'
        ), row=1, col=1
    )

    # Enhanced Price Fill Areas - Multiple zones for better visualization
    if not ts.empty and len(ts) > 1:
        from utils import calculate_ge_tax

        # Calculate profitability for each time period
        profitable_periods = []
        unprofitable_periods = []

        for i in range(len(ts)):
            high_price = ts['high'].iloc[i]
            low_price = ts['low'].iloc[i]
            ge_tax = calculate_ge_tax(high_price)
            net_profit = high_price - low_price - ge_tax

            timestamp = ts['timestamp'].iloc[i]

            if net_profit > 0:
                profitable_periods.append({
                    'timestamp': timestamp,
                    'high': high_price,
                    'low': low_price,
                    'profit': net_profit
                })
            else:
                unprofitable_periods.append({
                    'timestamp': timestamp,
                    'high': high_price,
                    'low': low_price,
                    'loss': abs(net_profit)
                })

        # Create profitable fill areas (green gradient)
        if profitable_periods:
            profit_timestamps = [p['timestamp'] for p in profitable_periods]
            profit_highs = [p['high'] for p in profitable_periods]
            profit_lows = [p['low'] for p in profitable_periods]

            # Main profitable area
            fig.add_trace(
                go.Scatter(
                    x=profit_timestamps + profit_timestamps[::-1],
                    y=profit_highs + profit_lows[::-1],
                    fill='toself',
                    fillcolor='rgba(46, 204, 113, 0.15)',  # Green with transparency
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Profitable Spread',
                    hovertemplate='<b>Profitable Period</b><br>' +
                                  'Potential profit after tax<br>' +
                                  '<extra></extra>',
                    showlegend=False
                ), row=1, col=1
            )

            # Add profit intensity overlay (darker green for higher profits)
            max_profit = max(p['profit'] for p in profitable_periods) if profitable_periods else 0
            if max_profit > 0:
                # Create intensity-based fills
                high_profit_periods = [p for p in profitable_periods if p['profit'] >= max_profit * 0.7]

                if high_profit_periods:
                    hp_timestamps = [p['timestamp'] for p in high_profit_periods]
                    hp_highs = [p['high'] for p in high_profit_periods]
                    hp_lows = [p['low'] for p in high_profit_periods]

                    fig.add_trace(
                        go.Scatter(
                            x=hp_timestamps + hp_timestamps[::-1],
                            y=hp_highs + hp_lows[::-1],
                            fill='toself',
                            fillcolor='rgba(39, 174, 96, 0.25)',  # Darker green for high profit
                            line=dict(color='rgba(255,255,255,0)'),
                            name='High Profit Zone',
                            hovertemplate='<b>High Profit Period</b><br>' +
                                          'Excellent profit opportunity<br>' +
                                          '<extra></extra>',
                            showlegend=False
                        ), row=1, col=1
                    )

        # Create unprofitable fill areas (red/orange gradient)
        if unprofitable_periods:
            loss_timestamps = [p['timestamp'] for p in unprofitable_periods]
            loss_highs = [p['high'] for p in unprofitable_periods]
            loss_lows = [p['low'] for p in unprofitable_periods]

            fig.add_trace(
                go.Scatter(
                    x=loss_timestamps + loss_timestamps[::-1],
                    y=loss_highs + loss_lows[::-1],
                    fill='toself',
                    fillcolor='rgba(231, 76, 60, 0.12)',  # Light red with transparency
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Unprofitable Spread',
                    hovertemplate='<b>Unprofitable Period</b><br>' +
                                  'Loss after GE tax<br>' +
                                  '<extra></extra>',
                    showlegend=False
                ), row=1, col=1
            )

        # Add break-even zone (yellow/orange for marginal profits)
        marginal_periods = []
        for i in range(len(ts)):
            high_price = ts['high'].iloc[i]
            low_price = ts['low'].iloc[i]
            ge_tax = calculate_ge_tax(high_price)
            net_profit = high_price - low_price - ge_tax

            # Marginal = small profit (0-500 gp)
            if 0 < net_profit <= 500:
                marginal_periods.append({
                    'timestamp': ts['timestamp'].iloc[i],
                    'high': high_price,
                    'low': low_price
                })

        if marginal_periods:
            marg_timestamps = [p['timestamp'] for p in marginal_periods]
            marg_highs = [p['high'] for p in marginal_periods]
            marg_lows = [p['low'] for p in marginal_periods]

            fig.add_trace(
                go.Scatter(
                    x=marg_timestamps + marg_timestamps[::-1],
                    y=marg_highs + marg_lows[::-1],
                    fill='toself',
                    fillcolor='rgba(241, 196, 15, 0.15)',  # Yellow/orange for marginal
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Marginal Profit Zone',
                    hovertemplate='<b>Marginal Profit Period</b><br>' +
                                  'Small profit (0-500 gp)<br>' +
                                  '<extra></extra>',
                    showlegend=False
                ), row=1, col=1
            )

            # Add dynamic fill area legend
            fill_legend_traces = []

            # Count different zones
            profitable_count = len([p for p in profitable_periods]) if 'profitable_periods' in locals() else 0
            unprofitable_count = len([p for p in unprofitable_periods]) if 'unprofitable_periods' in locals() else 0
            marginal_count = len([p for p in marginal_periods]) if 'marginal_periods' in locals() else 0

            # Add invisible traces for legend
            if profitable_count > 0:
                fig.add_trace(
                    go.Scatter(
                        x=[ts['timestamp'].iloc[0]],
                        y=[ts['high'].iloc[0]],
                        mode='markers',
                        marker=dict(color='rgba(46, 204, 113, 0.8)', size=10, symbol='square'),
                        name=f'Profitable Periods ({profitable_count})',
                        showlegend=True,
                        hoverinfo='skip'
                    ), row=1, col=1
                )

            if marginal_count > 0:
                fig.add_trace(
                    go.Scatter(
                        x=[ts['timestamp'].iloc[0]],
                        y=[ts['high'].iloc[0]],
                        mode='markers',
                        marker=dict(color='rgba(241, 196, 15, 0.8)', size=10, symbol='square'),
                        name=f'Marginal Periods ({marginal_count})',
                        showlegend=True,
                        hoverinfo='skip'
                    ), row=1, col=1
                )

            if unprofitable_count > 0:
                fig.add_trace(
                    go.Scatter(
                        x=[ts['timestamp'].iloc[0]],
                        y=[ts['high'].iloc[0]],
                        mode='markers',
                        marker=dict(color='rgba(231, 76, 60, 0.8)', size=10, symbol='square'),
                        name=f'Unprofitable Periods ({unprofitable_count})',
                        showlegend=True,
                        hoverinfo='skip'
                    ), row=1, col=1
                )

    # Enhanced trend line
    if len(ts) >= 5:
        # Calculate moving average
        window_size = max(3, len(ts) // 10)  # Adaptive window size
        ts['trend'] = ts[['high', 'low']].mean(axis=1).rolling(window=window_size, min_periods=1).mean()

        fig.add_trace(
            go.Scatter(
                x=ts['timestamp'],
                y=ts['trend'],
                mode='lines',
                name='Trend',
                line=dict(color='#f39c12', width=2, dash='dash'),
                opacity=0.8,
                hovertemplate='<b>Trend</b><br>' +
                              'Price: %{y:,.0f} gp<br>' +
                              'Time: %{x|%b %d, %H:%M}<br>' +
                              '<extra></extra>'
            ), row=1, col=1
        )

    # Reference Lines - Current Market Prices
    if not ts.empty:
        # Get current prices (most recent data point)
        current_high = ts['high'].iloc[-1]  # Current sell price
        current_low = ts['low'].iloc[-1]  # Current buy price

        # Calculate break-even price (buy price + GE tax)
        from utils import calculate_ge_tax
        ge_tax = calculate_ge_tax(current_high)
        break_even_price = current_low + ge_tax

        # Add reference lines across the entire time range
        time_range = [ts['timestamp'].min(), ts['timestamp'].max()]

        # Current Sell Price Line (Red)
        fig.add_trace(
            go.Scatter(
                x=time_range,
                y=[current_high, current_high],
                mode='lines',
                name=f'Current Sell: {current_high:,.0f} gp',
                line=dict(color='#e74c3c', width=2, dash='dot'),
                opacity=0.8,
                hovertemplate=f'<b>Current Sell Price</b><br>{current_high:,.0f} gp<extra></extra>',
                showlegend=True
            ), row=1, col=1
        )

        # Current Buy Price Line (Green)
        fig.add_trace(
            go.Scatter(
                x=time_range,
                y=[current_low, current_low],
                mode='lines',
                name=f'Current Buy: {current_low:,.0f} gp',
                line=dict(color='#27ae60', width=2, dash='dot'),
                opacity=0.8,
                hovertemplate=f'<b>Current Buy Price</b><br>{current_low:,.0f} gp<extra></extra>',
                showlegend=True
            ), row=1, col=1
        )

        # Break-Even Price Line (Orange/Yellow)
        fig.add_trace(
            go.Scatter(
                x=time_range,
                y=[break_even_price, break_even_price],
                mode='lines',
                name=f'Break-Even: {break_even_price:,.0f} gp',
                line=dict(color='#f39c12', width=2, dash='dashdot'),
                opacity=0.7,
                hovertemplate=f'<b>Break-Even Price</b><br>{break_even_price:,.0f} gp<br>(Buy + Tax)<extra></extra>',
                showlegend=True
            ), row=1, col=1
        )

        # Add profit zone fill (between buy and sell)
        fig.add_trace(
            go.Scatter(
                x=time_range + time_range[::-1],
                y=[current_low, current_low, current_high, current_high],
                fill='toself',
                fillcolor='rgba(46, 204, 113, 0.1)',  # Light green profit zone
                line=dict(color='rgba(255,255,255,0)'),
                name='Profit Zone',
                showlegend=False,
                hoverinfo='skip'
            ), row=1, col=1
        )

        # Add annotations for reference lines
        annotations = [
            dict(
                x=ts['timestamp'].iloc[-1],
                y=current_high,
                text=f"Sell: {current_high:,.0f} gp",
                showarrow=True,
                arrowhead=2,
                arrowcolor='#e74c3c',
                arrowwidth=2,
                bgcolor='rgba(231, 76, 60, 0.8)',
                bordercolor='#e74c3c',
                font=dict(color='white', size=10),
                xanchor='left'
            ),
            dict(
                x=ts['timestamp'].iloc[-1],
                y=current_low,
                text=f"Buy: {current_low:,.0f} gp",
                showarrow=True,
                arrowhead=2,
                arrowcolor='#27ae60',
                arrowwidth=2,
                bgcolor='rgba(39, 174, 96, 0.8)',
                bordercolor='#27ae60',
                font=dict(color='white', size=10),
                xanchor='left'
            ),
            dict(
                x=ts['timestamp'].iloc[len(ts) // 2],  # Middle of chart
                y=break_even_price,
                text=f"Break-Even: {break_even_price:,.0f} gp",
                showarrow=True,
                arrowhead=2,
                arrowcolor='#f39c12',
                arrowwidth=2,
                bgcolor='rgba(243, 156, 18, 0.8)',
                bordercolor='#f39c12',
                font=dict(color='white', size=10),
                xanchor='center'
            )
        ]

    # Enhanced Volume Visualization
    if not ts.empty:
        # Calculate volume statistics for better color coding
        volume_stats = {
            'min': ts['volume'].min(),
            'max': ts['volume'].max(),
            'mean': ts['volume'].mean(),
            'median': ts['volume'].median(),
            'q75': ts['volume'].quantile(0.75),
            'q25': ts['volume'].quantile(0.25)
        }

        # Create sophisticated color mapping
        volume_colors = []
        volume_intensities = []
        volume_labels = []

        for vol in ts['volume']:
            # Calculate volume intensity (0-1 scale)
            if volume_stats['max'] > volume_stats['min']:
                intensity = (vol - volume_stats['min']) / (volume_stats['max'] - volume_stats['min'])
            else:
                intensity = 0.5

            # Color coding based on volume levels
            if vol >= volume_stats['q75']:
                if vol >= volume_stats['max'] * 0.8:
                    color = '#c0392b'  # Very high - dark red
                    label = 'Very High'
                else:
                    color = '#e74c3c'  # High - red
                    label = 'High'
            elif vol >= volume_stats['median']:
                color = '#f39c12'  # Above median - orange
                label = 'Above Average'
            elif vol >= volume_stats['q25']:
                color = '#3498db'  # Normal - blue
                label = 'Normal'
            else:
                color = '#95a5a6'  # Low - gray
                label = 'Low'

            volume_colors.append(color)
            volume_intensities.append(intensity)
            volume_labels.append(label)

        # Add volume percentage indicators
        volume_percentages = []
        if volume_stats['max'] > 0:
            volume_percentages = [(vol / volume_stats['max']) * 100 for vol in ts['volume']]

        # Enhanced volume bars with better styling
        fig.add_trace(
            go.Bar(
                x=ts['timestamp'],
                y=ts['volume'],
                name='Trading Volume',
                marker=dict(
                    color=volume_colors,
                    opacity=0.8,
                    line=dict(width=0.5, color='rgba(255,255,255,0.1)')
                ),
                customdata=list(zip(volume_labels, volume_percentages)),
                hovertemplate='<b>Trading Volume</b><br>' +
                              'Volume: %{y:,.0f}<br>' +
                              'Level: %{customdata[0]}<br>' +
                              'Relative: %{customdata[1]:.1f}% of max<br>' +
                              'Time: %{x|%b %d, %H:%M}<br>' +
                              '<extra></extra>',
                width=None  # Auto-width based on data density
            ), row=2, col=1
        )

        # Add volume trend line
        if len(ts) >= 5:
            volume_trend_window = max(3, len(ts) // 8)
            volume_trend = ts['volume'].rolling(window=volume_trend_window, min_periods=1).mean()

            fig.add_trace(
                go.Scatter(
                    x=ts['timestamp'],
                    y=volume_trend,
                    mode='lines',
                    name='Volume Trend',
                    line=dict(color='#9b59b6', width=2, dash='dash'),
                    opacity=0.8,
                    hovertemplate='<b>Volume Trend</b><br>' +
                                  'Avg Volume: %{y:,.0f}<br>' +
                                  'Time: %{x|%b %d, %H:%M}<br>' +
                                  '<extra></extra>'
                ), row=2, col=1
            )

        # Add volume threshold lines
        fig.add_trace(
            go.Scatter(
                x=[ts['timestamp'].min(), ts['timestamp'].max()],
                y=[volume_stats['mean'], volume_stats['mean']],
                mode='lines',
                name=f"Avg Volume: {volume_stats['mean']:,.0f}",
                line=dict(color='rgba(155, 89, 182, 0.5)', width=1, dash='dot'),
                hovertemplate=f"Average Volume: {volume_stats['mean']:,.0f}<extra></extra>",
                showlegend=False
            ), row=2, col=1
        )

    # Enhanced Professional Styling
    fig.update_layout(
        template='plotly_dark',
        title=dict(
            text=f'<b>{item_name}</b> - Real-Time Price Analysis',
            x=0.5,
            font=dict(size=22, color='#ffffff', family='Arial Black'),
            pad=dict(t=20, b=10)
        ),
        height=height,
        width=width,
        hovermode='x unified',
        margin=dict(t=90, b=60, l=60, r=60),

        # Enhanced legend styling
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(30, 30, 30, 0.9)',
            bordercolor='rgba(100, 200, 100, 0.3)',
            borderwidth=2,
            font=dict(size=11, color='#ffffff'),
            itemsizing='constant',
            itemwidth=40
        ),

        # Professional dark theme colors
        plot_bgcolor='#0d1117',  # GitHub dark theme background
        paper_bgcolor='#0d1117',

        # Enhanced hover styling
        hoverlabel=dict(
            bgcolor='rgba(20, 20, 20, 0.9)',
            bordercolor='rgba(100, 200, 100, 0.8)',
            font=dict(size=12, color='white', family='Consolas'),
            align='left'
        ),

        # Professional font styling
        font=dict(
            family='Segoe UI, Arial, sans-serif',
            size=11,
            color='#e6edf3'
        ),

        # Animation settings for smooth interactions
        transition=dict(
            duration=300,
            easing='cubic-in-out'
        )
    )

    # Advanced Interactivity Configuration
    fig.update_layout(
        # Enhanced zoom and pan
        dragmode='zoom',
        selectdirection='d',

        # Crosshair cursor configuration
        hovermode='x unified',
        spikedistance=1000,
        hoverdistance=100,

        # Interactive features
        showlegend=True,
        legend_itemclick="toggleothers",
        legend_itemdoubleclick="toggle",

        # Enhanced selection tools
        newshape=dict(
            line_color='rgba(100, 200, 100, 0.8)',
            line_width=2,
            opacity=0.8
        ),

        # Modebar configuration
        modebar=dict(
            bgcolor='rgba(30, 30, 30, 0.8)',
            color='rgba(255, 255, 255, 0.7)',
            activecolor='rgba(100, 200, 100, 1)',
            orientation='h',
            remove=['lasso2d', 'select2d']  # Remove confusing tools
        )
    )

    # Enhanced axis interactions
    fig.update_xaxes(
        showspikes=True,
        spikecolor='rgba(100, 200, 100, 0.6)',
        spikesnap='cursor',
        spikemode='across',
        spikethickness=1,
        spikedash='solid'
    )

    fig.update_yaxes(
        showspikes=True,
        spikecolor='rgba(100, 200, 100, 0.6)',
        spikesnap='cursor',
        spikemode='across',
        spikethickness=1,
        spikedash='solid',
        row=1, col=1
    )

    # Interactive Price Display JavaScript
    interactive_js = f"""
    <script>
    function updatePriceDisplay(eventdata) {{
        if (eventdata && eventdata.points && eventdata.points.length > 0) {{
            var point = eventdata.points[0];
            var timestamp = point.x;
            var price = point.y;
            var trace_name = point.data.name;

            // Update display element if it exists
            var display = document.getElementById('price-display-{item_name.replace(" ", "-")}');
            if (display) {{
                display.innerHTML = '<b>' + trace_name + '</b>: ' + 
                                  price.toLocaleString() + ' gp<br>' +
                                  '<small>' + new Date(timestamp).toLocaleString() + '</small>';
            }}
        }}
    }}

    // Add event listener when chart is ready
    document.addEventListener('DOMContentLoaded', function() {{
        var plotDiv = document.querySelector('[data-testid="stPlotlyChart"]');
        if (plotDiv) {{
            plotDiv.on('plotly_hover', updatePriceDisplay);
        }}
    }});
    </script>

    <div id="price-display-{item_name.replace(' ', '-')}" 
         style="position: fixed; top: 100px; right: 20px; 
                background: rgba(30, 30, 30, 0.9); 
                color: white; padding: 10px; 
                border-radius: 5px; border: 1px solid rgba(100, 200, 100, 0.5);
                z-index: 1000; font-family: Consolas;
                display: none;">
        Hover over chart to see price details
    </div>
    """

    # Add the interactive JavaScript to Streamlit
    st.markdown(interactive_js, unsafe_allow_html=True)

    # Professional Grid and Axis Styling - GE Tracker inspired
    fig.update_xaxes(
        showgrid=True,
        gridcolor='rgba(139, 148, 158, 0.15)',  # Subtle grid
        gridwidth=1,
        tickfont=dict(color='#e6edf3', size=10, family='Consolas'),
        title_font=dict(color='#f0f6fc', size=11),
        showline=True,
        linecolor='rgba(139, 148, 158, 0.3)',
        linewidth=1,
        mirror=True,
        tickcolor='rgba(139, 148, 158, 0.5)',
        row=2, col=1
    )

    # Main price axis (top chart)
    fig.update_yaxes(
        title_text='Price (gp)',
        row=1, col=1,
        showgrid=True,
        gridcolor='rgba(139, 148, 158, 0.12)',
        gridwidth=1,
        tickfont=dict(color='#e6edf3', size=10, family='Consolas'),
        title_font=dict(color='#f0f6fc', size=12, family='Arial'),
        tickformat=',.0f',
        showline=True,
        linecolor='rgba(139, 148, 158, 0.3)',
        linewidth=1,
        mirror=True,
        tickcolor='rgba(139, 148, 158, 0.5)',
        zeroline=False,
        # Add price range indicators
        tickmode='auto',
        nticks=8
    )

    # Volume axis (bottom chart)
    fig.update_yaxes(
        title_text='Trading Volume',
        row=2, col=1,
        showgrid=True,
        gridcolor='rgba(139, 148, 158, 0.08)',
        gridwidth=1,
        tickfont=dict(color='#e6edf3', size=9, family='Consolas'),
        title_font=dict(color='#f0f6fc', size=11, family='Arial'),
        tickformat=',.0f',
        side='left',
        showline=True,
        linecolor='rgba(139, 148, 158, 0.3)',
        linewidth=1,
        mirror=True,
        tickcolor='rgba(139, 148, 158, 0.5)',
        autorange=True,
        tickmode='auto',
        nticks=4,
        zeroline=True,
        zerolinecolor='rgba(139, 148, 158, 0.2)',
        zerolinewidth=1
    )

    # Enhanced x-axis for main chart
    fig.update_xaxes(
        showgrid=True,
        gridcolor='rgba(139, 148, 158, 0.12)',
        gridwidth=1,
        tickfont=dict(color='#e6edf3', size=10, family='Consolas'),
        title_font=dict(color='#f0f6fc', size=11),
        showline=True,
        linecolor='rgba(139, 148, 158, 0.3)',
        linewidth=1,
        mirror=True,
        tickcolor='rgba(139, 148, 158, 0.5)',
        row=1, col=1
    )

    # Add secondary y-axis for volume percentage
    if not ts.empty and volume_stats['max'] > 0:
        # Add percentage scale on right side
        fig.add_trace(
            go.Scatter(
                x=[ts['timestamp'].min()],
                y=[0],
                mode='markers',
                marker=dict(opacity=0),
                showlegend=False,
                yaxis='y3'
            ), row=2, col=1
        )

        # Configure secondary volume axis
        fig.update_layout(
            yaxis3=dict(
                title='Volume %',
                title_font=dict(color='white', size=10),
                tickfont=dict(color='white', size=8),
                side='right',
                overlaying='y2',
                showgrid=False,
                range=[0, 100],
                ticksuffix='%',
                position=0.99
            )
        )

    # Professional Range Selector - GE Tracker Style
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(
                        count=1, label="1H", step="hour", stepmode="backward",
                        name="1h_button"
                    ),
                    dict(
                        count=6, label="6H", step="hour", stepmode="backward",
                        name="6h_button"
                    ),
                    dict(
                        count=1, label="1D", step="day", stepmode="backward",
                        name="1d_button"
                    ),
                    dict(
                        count=7, label="7D", step="day", stepmode="backward",
                        name="7d_button"
                    ),
                    dict(
                        step="all", label="ALL",
                        name="all_button"
                    )
                ]),
                bgcolor='rgba(33, 38, 45, 0.9)',
                activecolor='rgba(100, 200, 100, 0.8)',
                bordercolor='rgba(139, 148, 158, 0.3)',
                borderwidth=1,
                font=dict(color='#e6edf3', size=10, family='Consolas'),
                x=0.02,
                y=1.02,
                xanchor='left',
                yanchor='bottom'
            ),
            rangeslider=dict(visible=False),
            type="date",
            showspikes=True,
            spikecolor='rgba(100, 200, 100, 0.8)',
            spikethickness=1,
            spikedash='solid',
            spikemode='across'
        )
    )

    # Add the annotations to the layout
    fig.update_layout(annotations=annotations)

    # Display the enhanced interactive chart
    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"chart_{item_name}_{current_timestep}",
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': [
                'drawline',
                'drawopenpath',
                'drawclosedpath',
                'drawcircle',
                'drawrect',
                'eraseshape'
            ],
            'modeBarButtonsToRemove': [
                'lasso2d',
                'select2d'
            ],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': f'{item_name}_chart_{current_timestep}',
                'height': height,
                'width': width,
                'scale': 2
            },
            'scrollZoom': True,
            'doubleClick': 'reset+autosize',
            'showTips': True,
            'responsive': True
        }
    )

    # Add chart interaction controls
    show_chart_controls(ts, item_name, current_timestep)

    # Reference line information panel
    show_reference_info(ts, item_name)

    # Chart statistics and volume insights
    show_chart_statistics(ts, item_name, current_timestep)
    show_volume_insights(ts, item_name)
    show_fill_area_analysis(ts, item_name)


def show_chart_statistics(ts: pd.DataFrame, item_name: str, timestep: str):
    """Display chart statistics and analysis"""

    st.markdown("---")
    st.subheader("📊 Chart Statistics")

    # Calculate key metrics
    latest_high = ts['high'].iloc[-1]
    latest_low = ts['low'].iloc[-1]
    price_change = latest_high - ts['high'].iloc[0]
    price_change_pct = (price_change / ts['high'].iloc[0]) * 100 if ts['high'].iloc[0] > 0 else 0

    # Volume metrics
    total_volume = ts['volume'].sum()
    avg_volume = ts['volume'].mean()
    max_volume = ts['volume'].max()

    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 Current Spread",
            value=f"{latest_high - latest_low:,.0f} gp",
            delta=f"{((latest_high - latest_low) / latest_low * 100):+.1f}%" if latest_low > 0 else None
        )

    with col2:
        st.metric(
            label="📈 Price Change",
            value=f"{price_change:+,.0f} gp",
            delta=f"{price_change_pct:+.1f}%"
        )

    with col3:
        # Enhanced volume analysis
        volume_trend_direction = "📈" if ts['volume'].iloc[-1] > avg_volume else "📉"
        volume_change_pct = ((ts['volume'].iloc[-1] - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0

        st.metric(
            label="📊 Current Volume",
            value=f"{ts['volume'].iloc[-1]:,.0f}",
            delta=f"{volume_change_pct:+.1f}% vs avg",
            delta_color="normal" if volume_change_pct > 0 else "inverse"
        )

        # Volume level indicator
        if ts['volume'].iloc[-1] >= ts['volume'].quantile(0.75):
            st.caption("🔥 High Volume Period")
        elif ts['volume'].iloc[-1] >= ts['volume'].median():
            st.caption("📊 Normal Volume")
        else:
            st.caption("💤 Low Volume Period")

    with col4:
        volatility = (ts['high'].std() / ts['high'].mean()) * 100 if ts['high'].mean() > 0 else 0
        st.metric(
            label="⚡ Volatility",
            value=f"{volatility:.1f}%",
            delta="Lower = More Stable",
            delta_color="inverse"
        )

    # Time period information
    period_info = {
        "5m": "📊 5-minute intervals - Intraday trading view",
        "1h": "📈 Hourly intervals - Short-term trends",
        "6h": "📉 6-hour intervals - Medium-term patterns",
        "24h": "📋 Daily intervals - Long-term analysis"
    }

    st.info(f"🕒 **Current View:** {period_info.get(timestep, 'Unknown timeframe')}")


def show_reference_info(ts: pd.DataFrame, item_name: str):
    """Display reference line information and trading analysis"""

    if ts.empty:
        return

    # Calculate reference prices
    current_high = ts['high'].iloc[-1]
    current_low = ts['low'].iloc[-1]

    from utils import calculate_ge_tax
    ge_tax = calculate_ge_tax(current_high)
    break_even_price = current_low + ge_tax
    net_profit = current_high - break_even_price
    roi = (net_profit / current_low * 100) if current_low > 0 else 0

    st.markdown("---")
    st.subheader("📍 Reference Lines Explained")

    # Reference line info in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 🟢 Buy Price")
        st.metric(
            label="Current Buy Price",
            value=f"{current_low:,.0f} gp",
            help="Price to place buy orders at"
        )
        st.caption("🔹 Green dotted line on chart")

    with col2:
        st.markdown("### 🔴 Sell Price")
        st.metric(
            label="Current Sell Price",
            value=f"{current_high:,.0f} gp",
            help="Price to place sell orders at"
        )
        st.caption("🔹 Red dotted line on chart")

    with col3:
        st.markdown("### 🟡 Break-Even")
        st.metric(
            label="Break-Even Price",
            value=f"{break_even_price:,.0f} gp",
            delta=f"Tax: {ge_tax:,.0f} gp",
            help="Buy price + GE tax = minimum profitable sell price"
        )
        st.caption("🔹 Orange dash-dot line on chart")

    with col4:
        st.markdown("### 💰 Net Profit")
        st.metric(
            label="Potential Profit",
            value=f"{net_profit:,.0f} gp",
            delta=f"ROI: {roi:.1f}%",
            delta_color="normal" if roi > 0 else "inverse"
        )
        st.caption("🔹 Green shaded profit zone")

    # Trading analysis
    st.subheader("💡 Trading Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🎯 Entry Strategy:**")
        if roi >= 5:
            st.success("✅ **Excellent opportunity** - High ROI with good margin")
        elif roi >= 2:
            st.info("📊 **Good opportunity** - Decent profit potential")
        elif roi >= 0.5:
            st.warning("⚠️ **Marginal opportunity** - Low profit margin")
        else:
            st.error("❌ **Poor opportunity** - Unprofitable after tax")

        # Risk assessment
        spread_pct = ((current_high - current_low) / current_low * 100) if current_low > 0 else 0
        if spread_pct >= 10:
            st.info("📈 **Wide spread** - Higher volatility, higher potential")
        elif spread_pct >= 5:
            st.info("📊 **Normal spread** - Standard market conditions")
        else:
            st.warning("📉 **Narrow spread** - Low volatility, limited profit")

    with col2:
        st.markdown("**⚡ Quick Stats:**")
        st.write(f"• **Spread:** {current_high - current_low:,.0f} gp ({spread_pct:.1f}%)")
        st.write(f"• **GE Tax:** {ge_tax:,.0f} gp ({(ge_tax / current_high * 100):.1f}%)")
        st.write(f"• **Tax Rate:** {min(2.0, (ge_tax / current_high * 100)):.1f}% (max 2%)")

        # Price trend
        if len(ts) >= 2:
            price_change = current_high - ts['high'].iloc[0]
            trend_direction = "📈 Rising" if price_change > 0 else "📉 Falling" if price_change < 0 else "➡️ Stable"
            st.write(f"• **Price Trend:** {trend_direction}")

        # Volume analysis
        avg_volume = ts['volume'].mean()
        current_volume = ts['volume'].iloc[-1]
        vol_status = "🔥 High" if current_volume > avg_volume * 1.5 else "📊 Normal" if current_volume > avg_volume * 0.5 else "💤 Low"
        st.write(f"• **Volume Status:** {vol_status}")


def show_volume_insights(ts: pd.DataFrame, item_name: str):
    """Display detailed volume analysis and insights"""

    if ts.empty:
        return

    st.markdown("---")
    st.subheader("📊 Volume Analysis")

    # Calculate volume metrics
    volume_stats = {
        'current': ts['volume'].iloc[-1],
        'max': ts['volume'].max(),
        'min': ts['volume'].min(),
        'mean': ts['volume'].mean(),
        'median': ts['volume'].median(),
        'std': ts['volume'].std()
    }

    # Volume distribution analysis
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📈 Volume Levels**")

        # Volume percentile
        current_percentile = (ts['volume'] <= volume_stats['current']).mean() * 100

        if current_percentile >= 80:
            level_desc = "🔥 Very High"
            level_color = "red"
        elif current_percentile >= 60:
            level_desc = "📈 High"
            level_color = "orange"
        elif current_percentile >= 40:
            level_desc = "📊 Normal"
            level_color = "blue"
        else:
            level_desc = "💤 Low"
            level_color = "gray"

        st.metric("Current Level", level_desc)
        st.write(f"**Percentile:** {current_percentile:.0f}th")
        st.write(f"**vs Average:** {((volume_stats['current'] / volume_stats['mean'] - 1) * 100):+.1f}%")

    with col2:
        st.markdown("**⏰ Volume Patterns**")

        # Time-based volume analysis
        if len(ts) >= 24:  # If we have enough data points
            ts_hourly = ts.copy()
            ts_hourly['hour'] = ts_hourly['timestamp'].dt.hour
            hourly_avg = ts_hourly.groupby('hour')['volume'].mean()

            if not hourly_avg.empty:
                peak_hour = hourly_avg.idxmax()
                low_hour = hourly_avg.idxmin()

                st.write(f"**Peak Hour:** {peak_hour}:00")
                st.write(f"**Quiet Hour:** {low_hour}:00")
                st.write(f"**Peak Volume:** {hourly_avg.max():,.0f}")

        # Volume volatility
        cv = (volume_stats['std'] / volume_stats['mean']) if volume_stats['mean'] > 0 else 0
        vol_stability = "Stable" if cv < 0.5 else "Moderate" if cv < 1.0 else "Volatile"
        st.write(f"**Stability:** {vol_stability}")

    with col3:
        st.markdown("**💡 Trading Insights**")

        # Volume-based recommendations
        if volume_stats['current'] >= volume_stats['mean'] * 1.5:
            st.success("✅ High liquidity - Good for large trades")
        elif volume_stats['current'] >= volume_stats['mean'] * 0.5:
            st.info("📊 Normal liquidity - Standard trading")
        else:
            st.warning("⚠️ Low liquidity - Use smaller trade sizes")

        # Market activity assessment
        if volume_stats['current'] >= volume_stats['max'] * 0.8:
            st.info("🚨 Exceptional activity - Possible news/events")
        elif volume_stats['current'] <= volume_stats['min'] * 1.2:
            st.info("😴 Very quiet period - Limited trading")


def show_fill_area_analysis(ts: pd.DataFrame, item_name: str):
    """Display analysis of the price fill areas and profitability periods"""

    if ts.empty:
        return

    st.markdown("---")
    st.subheader("🎨 Price Fill Area Analysis")

    # Calculate profitability statistics
    from utils import calculate_ge_tax

    profitable_periods = 0
    unprofitable_periods = 0
    marginal_periods = 0
    total_profit = 0
    total_loss = 0

    for i in range(len(ts)):
        high_price = ts['high'].iloc[i]
        low_price = ts['low'].iloc[i]
        ge_tax = calculate_ge_tax(high_price)
        net_profit = high_price - low_price - ge_tax

        if net_profit > 500:
            profitable_periods += 1
            total_profit += net_profit
        elif net_profit > 0:
            marginal_periods += 1
        else:
            unprofitable_periods += 1
            total_loss += abs(net_profit)

    total_periods = len(ts)

    # Display statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        profit_pct = (profitable_periods / total_periods * 100) if total_periods > 0 else 0
        st.metric(
            label="🟢 Profitable Periods",
            value=f"{profitable_periods}",
            delta=f"{profit_pct:.1f}% of time"
        )

    with col2:
        marginal_pct = (marginal_periods / total_periods * 100) if total_periods > 0 else 0
        st.metric(
            label="🟡 Marginal Periods",
            value=f"{marginal_periods}",
            delta=f"{marginal_pct:.1f}% of time"
        )

    with col3:
        loss_pct = (unprofitable_periods / total_periods * 100) if total_periods > 0 else 0
        st.metric(
            label="🔴 Unprofitable Periods",
            value=f"{unprofitable_periods}",
            delta=f"{loss_pct:.1f}% of time"
        )

    with col4:
        net_total = total_profit - total_loss
        st.metric(
            label="💰 Net Opportunity",
            value=f"{net_total:,.0f} gp",
            delta="Total potential" if net_total > 0 else "Net loss risk"
        )

    # Profitability insights
    st.subheader("💡 Fill Area Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🎯 Trading Strategy:**")

        profit_pct = (profitable_periods / total_periods * 100) if total_periods > 0 else 0

        if profit_pct >= 70:
            st.success("✅ **Excellent Item** - Profitable most of the time")
        elif profit_pct >= 50:
            st.info("📊 **Good Item** - More profitable than not")
        elif profit_pct >= 30:
            st.warning("⚠️ **Risky Item** - Mixed profitability")
        else:
            st.error("❌ **Avoid** - Usually unprofitable")

        # Time-based recommendation
        if profitable_periods > 0:
            avg_profit = total_profit / profitable_periods
            st.write(f"• **Avg profit when profitable:** {avg_profit:,.0f} gp")

        if unprofitable_periods > 0:
            avg_loss = total_loss / unprofitable_periods
            st.write(f"• **Avg loss when unprofitable:** {avg_loss:,.0f} gp")

    with col2:
        st.markdown("**📊 Fill Area Legend:**")
        st.write("🟢 **Green Areas** - Profitable after tax (>500 gp)")
        st.write("🟡 **Yellow Areas** - Marginal profit (0-500 gp)")
        st.write("🔴 **Red Areas** - Unprofitable (loss after tax)")
        st.write("🎨 **Color Intensity** - Darker = higher profit/loss")

        # Market timing advice
        if profitable_periods > 0 and unprofitable_periods > 0:
            st.info("💡 **Timing matters** - Look for green zones to trade")
        elif profitable_periods == 0:
            st.warning("⚠️ **High risk item** - Consider avoiding")
        else:
            st.success("✅ **Consistent performer** - Good for regular trading")


def show_chart_controls(ts: pd.DataFrame, item_name: str, current_timestep: str):
    """Display interactive chart controls and analysis tools"""

    st.markdown("---")
    st.subheader("🎮 Chart Interaction Controls")

    # Interactive controls in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**📊 Chart Tools:**")
        st.info("🖱️ **Mouse Controls:**\n"
                "• Drag to pan\n"
                "• Scroll to zoom\n"
                "• Double-click to reset\n"
                "• Hover for price details")

    with col2:
        st.markdown("**🔧 Drawing Tools:**")
        st.info("📝 **Available Tools:**\n"
                "• Draw trend lines\n"
                "• Add rectangles\n"
                "• Mark support/resistance\n"
                "• Erase drawings")

    with col3:
        st.markdown("**📥 Export Options:**")

        # Chart export button
        if st.button("📸 Export Chart Image", use_container_width=True):
            st.info("💡 Use the camera icon in the chart toolbar to download PNG")

        # Data export
        if st.button("📊 Export Chart Data", use_container_width=True):
            csv_data = ts.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV Data",
                data=csv_data,
                file_name=f"{item_name}_chart_data_{current_timestep}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col4:
        st.markdown("**🎯 Quick Analysis:**")

        # Price analysis buttons
        if st.button("📈 Analyze Trends", use_container_width=True):
            show_trend_analysis(ts, item_name)

        if st.button("⚡ Volatility Report", use_container_width=True):
            show_volatility_report(ts, item_name)


def show_trend_analysis(ts: pd.DataFrame, item_name: str):
    """Show detailed trend analysis"""

    if len(ts) < 5:
        st.warning("Need more data points for trend analysis")
        return

    st.subheader(f"📈 Trend Analysis: {item_name}")

    # Calculate various trend indicators
    ts_copy = ts.copy()

    # Moving averages
    ts_copy['ma_5'] = ts_copy['high'].rolling(window=5).mean()
    ts_copy['ma_10'] = ts_copy['high'].rolling(window=min(10, len(ts) // 2)).mean()

    # Price momentum
    ts_copy['price_change'] = ts_copy['high'].pct_change()
    ts_copy['momentum'] = ts_copy['price_change'].rolling(window=3).mean()

    # Support and resistance levels
    recent_highs = ts_copy['high'].tail(20)
    recent_lows = ts_copy['low'].tail(20)

    resistance = recent_highs.quantile(0.8)
    support = recent_lows.quantile(0.2)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🔺 Resistance Level", f"{resistance:,.0f} gp")
        st.metric("🔻 Support Level", f"{support:,.0f} gp")

    with col2:
        current_momentum = ts_copy['momentum'].iloc[-1]
        momentum_direction = "📈 Bullish" if current_momentum > 0 else "📉 Bearish"
        st.metric("⚡ Current Momentum", momentum_direction)

        # Trend strength
        ma_diff = ts_copy['ma_5'].iloc[-1] - ts_copy['ma_10'].iloc[-1]
        trend_strength = "Strong" if abs(ma_diff) > ts_copy['high'].iloc[-1] * 0.02 else "Weak"
        st.metric("💪 Trend Strength", trend_strength)

    with col3:
        # Price position
        current_price = ts_copy['high'].iloc[-1]
        price_position = "Near Resistance" if current_price > resistance * 0.95 else \
            "Near Support" if current_price < support * 1.05 else "Mid-Range"
        st.metric("📍 Price Position", price_position)

        # Trading recommendation
        if current_momentum > 0 and current_price < resistance * 0.9:
            recommendation = "🟢 Consider Buying"
        elif current_momentum < 0 and current_price > support * 1.1:
            recommendation = "🔴 Consider Selling"
        else:
            recommendation = "🟡 Hold/Wait"
        st.metric("💡 Recommendation", recommendation)


def show_volatility_report(ts: pd.DataFrame, item_name: str):
    """Show detailed volatility analysis"""

    st.subheader(f"⚡ Volatility Report: {item_name}")

    # Calculate volatility metrics
    price_returns = ts['high'].pct_change().dropna()
    volatility = price_returns.std() * 100  # Convert to percentage

    # Price range analysis
    price_ranges = ((ts['high'] - ts['low']) / ts['low'] * 100).dropna()
    avg_daily_range = price_ranges.mean()

    # Volume volatility
    volume_cv = ts['volume'].std() / ts['volume'].mean() if ts['volume'].mean() > 0 else 0

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📊 Price Volatility:**")

        if volatility < 2:
            vol_level = "🟢 Low"
            vol_desc = "Stable price movements"
        elif volatility < 5:
            vol_level = "🟡 Medium"
            vol_desc = "Moderate price swings"
        else:
            vol_level = "🔴 High"
            vol_desc = "Large price movements"

        st.metric("Volatility Level", vol_level)
        st.write(f"**Standard Deviation:** {volatility:.2f}%")
        st.write(f"**Average Daily Range:** {avg_daily_range:.2f}%")
        st.caption(vol_desc)

    with col2:
        st.markdown("**📈 Trading Implications:**")

        if volatility < 2:
            st.success("✅ **Good for:** Conservative trading, large positions")
            st.info("📝 **Strategy:** Buy and hold, tight stop losses")
        elif volatility < 5:
            st.info("📊 **Good for:** Active trading, medium positions")
            st.info("📝 **Strategy:** Swing trading, wider stops")
        else:
            st.warning("⚠️ **Good for:** Expert traders, small positions")
            st.info("📝 **Strategy:** Day trading, very tight management")

        # Risk assessment
        risk_score = min(10, volatility * 2)
        st.metric("🎯 Risk Score", f"{risk_score:.1f}/10")
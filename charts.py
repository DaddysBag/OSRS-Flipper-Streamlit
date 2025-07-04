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
                             height: int = 500):
    """Create interactive Plotly chart"""
    ts['timestamp'] = pd.to_datetime(ts['timestamp'])

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.02
    )

    # Price traces
    fig.add_trace(
        go.Scatter(
            x=ts['timestamp'], y=ts['high'],
            mode='lines+markers',
            name='Sell Price',
            marker=dict(size=4),
            line=dict(width=2),
            hovertemplate='Sell: %{y} gp<br>%{x|%b %d %H:%M}<extra></extra>'
        ), row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=ts['timestamp'], y=ts['low'],
            mode='lines+markers',
            name='Buy Price',
            marker=dict(size=4),
            line=dict(width=2),
            hovertemplate='Buy: %{y} gp<br>%{x|%b %d %H:%M}<extra></extra>'
        ), row=1, col=1
    )

    # Trend line
    ts['mid'] = (ts['high'] + ts['low']) / 2
    rolling = ts['mid'].rolling(window=10, min_periods=1).mean()
    fig.add_trace(
        go.Scatter(
            x=ts['timestamp'], y=rolling,
            mode='lines',
            name='Trend',
            line=dict(dash='dash', width=1, color='#999'),
            hoverinfo='skip'
        ), row=1, col=1
    )

    # Volume bars
    fig.add_trace(
        go.Bar(
            x=ts['timestamp'], y=ts['volume'],
            name='Volume',
            marker=dict(opacity=0.6),
            hovertemplate='Vol: %{y}<br>%{x|%b %d %H:%M}<extra></extra>'
        ), row=2, col=1
    )

    # Dark styling
    fig.update_layout(
        template='plotly_dark',
        title=dict(text=item_name, x=0.5, font_size=16),
        height=height, width=width,
        hovermode='x unified',
        margin=dict(t=50, b=40, l=40, r=40),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    fig.update_xaxes(showgrid=True, gridcolor='#444', tickfont=dict(color='white'))
    fig.update_yaxes(title_text='Price (gp)', row=1, col=1,
                     showgrid=True, gridcolor='#444', tickfont=dict(color='white'))
    fig.update_yaxes(title_text='Volume', row=2, col=1,
                     showgrid=False, tickfont=dict(color='white'))

    st.plotly_chart(fig, use_container_width=True)
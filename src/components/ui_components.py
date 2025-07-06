"""
Modern UI Components
Reusable UI components with OSRS theming
"""

import streamlit as st

def create_osrs_card(title, content, icon="📊", accent_color="var(--osrs-blue-light)"):
    """Create a modern OSRS-themed card"""

    st.markdown(f"""
    <div class="osrs-card" style="border-left: 4px solid {accent_color};">
        <div style="display: flex; align-items: center; margin-bottom: 16px;">
            <span style="font-size: 1.5rem; margin-right: 12px;">{icon}</span>
            <h3 style="margin: 0; color: {accent_color}; font-size: 1.25rem;">{title}</h3>
        </div>
        <div style="color: var(--text-primary);">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_status_badge(status, size="normal"):
    """Create modern status badges"""

    status_configs = {
        "🟢 EXCELLENT": {
            "bg": "rgba(34, 139, 34, 0.15)",
            "border": "rgba(34, 139, 34, 0.4)",
            "color": "var(--osrs-green-light)",
            "icon": "🟢"
        },
        "🟡 GOOD": {
            "bg": "rgba(255, 140, 0, 0.15)",
            "border": "rgba(255, 140, 0, 0.4)",
            "color": "var(--osrs-orange)",
            "icon": "🟡"
        },
        "🔴 CAUTION": {
            "bg": "rgba(220, 20, 60, 0.15)",
            "border": "rgba(220, 20, 60, 0.4)",
            "color": "var(--osrs-red-light)",
            "icon": "🔴"
        }
    }

    config = status_configs.get(status, status_configs["🔴 CAUTION"])
    padding = "6px 12px" if size == "normal" else "4px 8px"
    font_size = "0.875rem" if size == "normal" else "0.75rem"

    return f"""
    <span style="
        background: {config['bg']};
        border: 1px solid {config['border']};
        color: {config['color']};
        padding: {padding};
        border-radius: 20px;
        font-size: {font_size};
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    ">
        {config['icon']} {status.replace(config['icon'] + ' ', '')}
    </span>
    """

def create_metric_card(label, value, delta=None, icon="📊", color="#4A90E2"):
    """Create enhanced metric cards with leak-proof HTML"""

    # Determine delta color and clean text - NO HTML HERE
    delta_color = "#32CD32"  # Default green
    delta_text = ""

    if delta:
        # Clean the delta text of any HTML/CSS
        delta_text = str(delta).replace('<div', '').replace('</div>', '').replace('style=', '').replace('color:', '')

        # Color logic based on content
        if any(word in delta_text.lower() for word in ["fresh", "active", "ready", "optimized", "connected", "online"]):
            delta_color = "#32CD32"  # Green
        elif any(word in delta_text.lower() for word in ["stale", "disabled", "offline", "needs improvement"]):
            delta_color = "#FF6B6B"  # Red
        else:
            delta_color = "#FFD700"  # Gold

    # Build the HTML with all styling contained within - no external variables
    card_html = f"""
    <div style="
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-align: center;
    ">
        <div style="font-size: 1.5rem; margin-bottom: 12px;">{icon}</div>
        <div style="
            color: {color};
            font-size: 1.875rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 8px;
        ">
            {value}
        </div>
        <div style="
            color: #B0B8C5;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        ">
            {label}
        </div>"""

    # Add delta if it exists - all styling contained here
    if delta_text:
        card_html += f"""
        <div style="
            color: {delta_color};
            font-size: 0.75rem;
            font-weight: 500;
            padding: 4px 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            margin-top: 8px;
        ">
            {delta_text}
        </div>"""

    card_html += "</div>"

    # Render the complete HTML
    st.markdown(card_html, unsafe_allow_html=True)

def create_hero_section():
    """Create an engaging hero section"""

    st.markdown("""
    <div style="
        text-align: center;
        padding: 40px 20px;
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(74, 144, 226, 0.1) 100%);
        border-radius: 20px;
        margin: 20px 0;
        border: 1px solid var(--border-accent);
    ">
        <h1 style="
            font-size: 3rem;
            margin-bottom: 16px;
            background: linear-gradient(135deg, var(--osrs-gold), var(--osrs-blue-light));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        ">
            💰 OSRS GE Flip Assistant
        </h1>
        <p style="
            font-size: 1.25rem;
            color: var(--text-secondary);
            margin-bottom: 24px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        ">
            Real-time Grand Exchange analysis with advanced risk assessment and profit optimization
        </p>
        <div style="
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        ">
            <div class="osrs-card" style="display: inline-block; padding: 12px 20px;">
                <span style="color: var(--osrs-green-light); font-weight: 600;">⚡ Live Data</span>
            </div>
            <div class="osrs-card" style="display: inline-block; padding: 12px 20px;">
                <span style="color: var(--osrs-blue-light); font-weight: 600;">🛡️ Risk Analysis</span>
            </div>
            <div class="osrs-card" style="display: inline-block; padding: 12px 20px;">
                <span style="color: var(--osrs-orange); font-weight: 600;">📊 Smart Filtering</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_loading_state(message="Loading OSRS market data..."):
    """Create an engaging loading state"""

    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 40px;
        background: var(--bg-card);
        border-radius: 16px;
        border: 1px solid var(--border-primary);
        margin: 20px 0;
    ">
        <div style="
            font-size: 3rem;
            margin-bottom: 16px;
            animation: osrs-pulse 2s infinite;
        ">
            ⚔️
        </div>
        <h3 style="color: var(--text-accent); margin-bottom: 8px;">
            {message}
        </h3>
        <p style="color: var(--text-secondary); margin: 0;">
            Analyzing Grand Exchange opportunities...
        </p>
    </div>
    """, unsafe_allow_html=True)

def create_quick_stats_row(stats_data):
    """Create a row of quick statistics"""

    cols = st.columns(len(stats_data))

    for i, (label, value, icon, color) in enumerate(stats_data):
        with cols[i]:
            create_metric_card(label, value, icon=icon, color=color)

def create_feature_highlight(title, description, icon, color="var(--osrs-blue-light)"):
    """Create feature highlight cards"""

    st.markdown(f"""
    <div class="osrs-card" style="
        border-left: 4px solid {color};
        background: linear-gradient(135deg, var(--bg-card) 0%, rgba(255, 255, 255, 0.02) 100%);
    ">
        <div style="display: flex; align-items: flex-start; gap: 16px;">
            <div style="
                font-size: 2rem;
                padding: 12px;
                background: {color};
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                min-width: 60px;
                height: 60px;
            ">
                {icon}
            </div>
            <div style="flex: 1;">
                <h4 style="
                    color: {color};
                    margin: 0 0 8px 0;
                    font-size: 1.25rem;
                    font-weight: 600;
                ">
                    {title}
                </h4>
                <p style="
                    color: var(--text-secondary);
                    margin: 0;
                    line-height: 1.5;
                ">
                    {description}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_section_divider(title, icon="⚔️"):
    """Create styled section dividers"""

    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        margin: 40px 0 20px 0;
        gap: 16px;
    ">
        <div style="
            font-size: 1.5rem;
            padding: 12px;
            background: linear-gradient(135deg, var(--osrs-gold), var(--osrs-gold-dark));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            {icon}
        </div>
        <h2 style="
            margin: 0;
            color: var(--text-accent);
            font-size: 1.5rem;
            font-weight: 600;
        ">
            {title}
        </h2>
        <div style="
            flex: 1;
            height: 2px;
            background: linear-gradient(90deg, var(--border-accent), transparent);
            border-radius: 1px;
        "></div>
    </div>
    """, unsafe_allow_html=True)

def create_tooltip(text, tooltip_text):
    """Create tooltips for better UX"""

    return f"""
    <span style="
        position: relative;
        color: var(--text-accent);
        border-bottom: 1px dotted var(--text-accent);
        cursor: help;
    " title="{tooltip_text}">
        {text}
    </span>
    """

def create_progress_indicator(current_step, total_steps, step_name):
    """Create progress indicators for multi-step processes"""

    progress_percent = (current_step / total_steps) * 100

    st.markdown(f"""
    <div style="
        background: var(--bg-card);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid var(--border-primary);
        margin: 16px 0;
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        ">
            <span style="color: var(--text-primary); font-weight: 500;">
                {step_name}
            </span>
            <span style="color: var(--text-secondary); font-size: 0.875rem;">
                {current_step}/{total_steps}
            </span>
        </div>
        <div style="
            width: 100%;
            height: 8px;
            background: var(--bg-secondary);
            border-radius: 4px;
            overflow: hidden;
        ">
            <div style="
                width: {progress_percent}%;
                height: 100%;
                background: linear-gradient(90deg, var(--osrs-blue), var(--osrs-blue-light));
                border-radius: 4px;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
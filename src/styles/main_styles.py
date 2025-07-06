"""
Modern OSRS-Themed Styling System
Enhanced visual design for the OSRS Flip Assistant
"""

import streamlit as st


def inject_modern_osrs_styles():
    """Inject modern OSRS-themed CSS styles"""
    st.markdown("""
    <style>
        /* Import modern fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        /* OSRS Color Palette */
        :root {
            --osrs-gold: #FFD700;
            --osrs-gold-dark: #B8860B;
            --osrs-blue: #0066CC;
            --osrs-blue-light: #4A90E2;
            --osrs-green: #228B22;
            --osrs-green-light: #32CD32;
            --osrs-red: #DC143C;
            --osrs-red-light: #FF6B6B;
            --osrs-orange: #FF8C00;
            
            /* Modern Dark Theme */
            --bg-primary: #0F0F23;
            --bg-secondary: #1A1A2E;
            --bg-tertiary: #16213E;
            --bg-card: rgba(255, 255, 255, 0.06);
            --bg-card-hover: rgba(255, 255, 255, 0.1);
            
            /* Text Colors */
            --text-primary: #FFFFFF;
            --text-secondary: #B0B8C5;
            --text-muted: #8A94A6;
            --text-accent: var(--osrs-gold);
            
            /* Borders and Shadows */
            --border-primary: rgba(255, 255, 255, 0.12);
            --border-accent: rgba(255, 215, 0, 0.3);
            --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.4);
            --shadow-button: 0 4px 16px rgba(255, 215, 0, 0.2);
        }

        /* Global Styles */
        .stApp {
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 50%, var(--bg-tertiary) 100%) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            color: var(--text-primary) !important;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {visibility: hidden;}

        /* Enhanced Container Styling */
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1400px !important;
            background: transparent !important;
        }

        /* Modern Card Design */
        .osrs-card {
            background: var(--bg-card) !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid var(--border-primary) !important;
            border-radius: 16px !important;
            padding: 24px !important;
            margin: 16px 0 !important;
            box-shadow: var(--shadow-card) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        .osrs-card:hover {
            background: var(--bg-card-hover) !important;
            border-color: var(--border-accent) !important;
            transform: translateY(-4px) !important;
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5) !important;
        }

        /* Modern Headers */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            letter-spacing: -0.025em !important;
            margin-bottom: 1rem !important;
        }

        h1 {
            font-size: 2.5rem !important;
            background: linear-gradient(135deg, var(--osrs-gold), var(--osrs-gold-dark)) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
            text-shadow: none !important;
        }

        h2 {
            font-size: 1.875rem !important;
            color: var(--text-accent) !important;
        }

        h3 {
            font-size: 1.5rem !important;
            color: var(--osrs-blue-light) !important;
        }

        /* Premium Enhanced Buttons */
        .stButton > button {
            background: linear-gradient(135deg, 
                var(--osrs-blue) 0%, 
                var(--osrs-blue-light) 50%, 
                var(--osrs-blue) 100%) !important;
            border: 1px solid rgba(74, 144, 226, 0.3) !important;
            border-radius: 16px !important;
            color: white !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            padding: 12px 24px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 
                0 4px 16px rgba(74, 144, 226, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
            text-transform: none !important;
            letter-spacing: 0.025em !important;
            position: relative !important;
            overflow: hidden !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stButton > button::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(255, 255, 255, 0.2), 
                transparent) !important;
            transition: left 0.5s ease !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 
                0 12px 32px rgba(74, 144, 226, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
            background: linear-gradient(135deg, 
                var(--osrs-blue-light) 0%, 
                var(--osrs-blue) 50%, 
                var(--osrs-blue-light) 100%) !important;
            border-color: rgba(74, 144, 226, 0.6) !important;
        }
        
        .stButton > button:hover::before {
            left: 100% !important;
        }
        
        .stButton > button:active {
            transform: translateY(-1px) scale(1.01) !important;
            transition: all 0.1s ease !important;
        }
        
        /* Premium Primary Button Variant */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, 
                var(--osrs-gold) 0%, 
                var(--osrs-gold-dark) 50%, 
                var(--osrs-gold) 100%) !important;
            color: var(--bg-primary) !important;
            font-weight: 700 !important;
            border: 1px solid rgba(255, 215, 0, 0.4) !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
            box-shadow: 
                0 6px 20px rgba(255, 215, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
        }
        
        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, 
                var(--osrs-gold-dark) 0%, 
                var(--osrs-gold) 50%, 
                var(--osrs-gold-dark) 100%) !important;
            box-shadow: 
                0 16px 40px rgba(255, 215, 0, 0.5),
                inset 0 1px 0 rgba(255, 255, 255, 0.5) !important;
            border-color: rgba(255, 215, 0, 0.8) !important;
        }
        
        /* Secondary Button Styling (Refresh Button) */
        .stButton > button[kind="secondary"] {
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.1) 0%, 
                rgba(255, 255, 255, 0.05) 50%, 
                rgba(255, 255, 255, 0.1) 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: var(--text-primary) !important;
            backdrop-filter: blur(15px) !important;
            box-shadow: 
                0 4px 12px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
        }
        
        .stButton > button[kind="secondary"]:hover {
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.15) 0%, 
                rgba(255, 215, 0, 0.1) 50%, 
                rgba(255, 255, 255, 0.15) 100%) !important;
            border-color: rgba(255, 215, 0, 0.4) !important;
            box-shadow: 
                0 8px 24px rgba(255, 215, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
        }
        
        /* Enhanced Pagination Buttons */
        .stButton > button:contains("⏮️"), 
        .stButton > button:contains("⬅️"), 
        .stButton > button:contains("➡️"), 
        .stButton > button:contains("⏭️") {
            min-width: 60px !important;
            padding: 10px 16px !important;
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.08) 0%, 
                rgba(255, 215, 0, 0.05) 50%, 
                rgba(255, 255, 255, 0.08) 100%) !important;
            border: 1px solid rgba(255, 215, 0, 0.2) !important;
            font-size: 1rem !important;
        }
        
        .stButton > button:contains("⏮️"):hover, 
        .stButton > button:contains("⬅️"):hover, 
        .stButton > button:contains("➡️"):hover, 
        .stButton > button:contains("⏭️"):hover {
            background: linear-gradient(135deg, 
                rgba(255, 215, 0, 0.15) 0%, 
                rgba(255, 215, 0, 0.1) 50%, 
                rgba(255, 215, 0, 0.15) 100%) !important;
            border-color: rgba(255, 215, 0, 0.5) !important;
            transform: translateY(-2px) scale(1.05) !important;
        }
        
        /* Disabled Button States */
        .stButton > button:disabled {
            background: rgba(255, 255, 255, 0.03) !important;
            color: rgba(255, 255, 255, 0.3) !important;
            border-color: rgba(255, 255, 255, 0.1) !important;
            cursor: not-allowed !important;
            transform: none !important;
            box-shadow: none !important;
        }
        
        .stButton > button:disabled:hover {
            transform: none !important;
            box-shadow: none !important;
        }
        
        /* Enhanced Input Fields */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stNumberInput > div > div > input {
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.08) 0%, 
                rgba(255, 255, 255, 0.04) 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 12px !important;
            color: var(--text-primary) !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            padding: 12px 16px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stNumberInput > div > div > input:focus {
            border-color: var(--osrs-blue-light) !important;
            box-shadow: 
                0 0 0 3px rgba(74, 144, 226, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
            outline: none !important;
            background: linear-gradient(135deg, 
                rgba(74, 144, 226, 0.1) 0%, 
                rgba(255, 255, 255, 0.08) 100%) !important;
        }
        
        /* Enhanced Selectbox Dropdown */
        .stSelectbox > div > div {
            border-radius: 12px !important;
            backdrop-filter: blur(15px) !important;
        }
        
        /* Loading Button Animation */
        @keyframes button-loading {
            0% { opacity: 0.7; }
            50% { opacity: 1; }
            100% { opacity: 0.7; }
        }
        
        .stButton > button.loading {
            animation: button-loading 1.5s infinite !important;
            pointer-events: none !important;
        }

        /* Enhanced Metrics */
        [data-testid="metric-container"] {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-primary) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            backdrop-filter: blur(20px) !important;
            transition: all 0.3s ease !important;
            box-shadow: var(--shadow-card) !important;
        }

        [data-testid="metric-container"]:hover {
            background: var(--bg-card-hover) !important;
            border-color: var(--border-accent) !important;
            transform: translateY(-2px) !important;
        }

        [data-testid="metric-container"] > div > div > div:first-child {
            color: var(--text-accent) !important;
            font-size: 1.875rem !important;
            font-weight: 700 !important;
            font-family: 'JetBrains Mono', monospace !important;
        }

        [data-testid="metric-container"] > div > div > div:last-child {
            color: var(--text-secondary) !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
        }

        /* Premium Enhanced Sidebar */
        .css-1d391kg, .css-1cypcdb, .css-17eq0hr {
            background: linear-gradient(180deg, 
                var(--bg-secondary) 0%, 
                rgba(26, 26, 46, 0.95) 50%, 
                var(--bg-tertiary) 100%) !important;
            border-right: 1px solid var(--border-accent) !important;
            backdrop-filter: blur(25px) !important;
            box-shadow: 
                2px 0 20px rgba(0, 0, 0, 0.3),
                inset -1px 0 0 rgba(255, 215, 0, 0.1) !important;
        }

        /* Enhanced Sidebar Section Cards */
        .filter-section {
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.08) 0%, 
                rgba(255, 215, 0, 0.02) 50%, 
                rgba(255, 255, 255, 0.04) 100%) !important;
            border: 1px solid rgba(255, 215, 0, 0.15) !important;
            border-radius: 16px !important;
            padding: 20px !important;
            margin: 16px 0 !important;
            backdrop-filter: blur(15px) !important;
            box-shadow: 
                0 8px 25px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
            position: relative !important;
            overflow: hidden !important;
        }

        .filter-section::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            height: 2px !important;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(255, 215, 0, 0.5), 
                transparent) !important;
        }

        .filter-section:hover {
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.12) 0%, 
                rgba(255, 215, 0, 0.04) 50%, 
                rgba(255, 255, 255, 0.08) 100%) !important;
            border-color: rgba(255, 215, 0, 0.25) !important;
            transform: translateY(-2px) !important;
            box-shadow: 
                0 12px 35px rgba(0, 0, 0, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
        }

        /* Enhanced Sidebar Headers */
        .css-1d391kg h3 {
            color: var(--osrs-gold) !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            margin-bottom: 16px !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
        }

        .css-1d391kg h3::after {
            content: '' !important;
            flex: 1 !important;
            height: 1px !important;
            background: linear-gradient(90deg, 
                rgba(255, 215, 0, 0.3), 
                transparent) !important;
            margin-left: 12px !important;
        }

        /* Enhanced Sidebar Sliders */
        .css-1d391kg .stSlider {
            margin: 12px 0 !important;
        }

        .css-1d391kg .stSlider > div > div > div {
            background: linear-gradient(135deg, 
                var(--osrs-blue) 0%, 
                var(--osrs-blue-light) 100%) !important;
            border-radius: 8px !important;
            box-shadow: 
                0 2px 8px rgba(74, 144, 226, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        }

        .css-1d391kg .stSlider > div > div > div > div {
            background: linear-gradient(135deg, 
                var(--osrs-gold) 0%, 
                var(--osrs-gold-dark) 100%) !important;
            border: 2px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow: 
                0 4px 12px rgba(255, 215, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
            transition: all 0.3s ease !important;
        }

        .css-1d391kg .stSlider > div > div > div > div:hover {
            transform: scale(1.1) !important;
            box-shadow: 
                0 6px 16px rgba(255, 215, 0, 0.6),
                inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
        }

        /* Enhanced Sidebar Selectboxes */
        .css-1d391kg .stSelectbox > div > div {
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.1) 0%, 
                rgba(255, 215, 0, 0.03) 100%) !important;
            border: 1px solid rgba(255, 215, 0, 0.2) !important;
            border-radius: 12px !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: 
                0 4px 12px rgba(0, 0, 0, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
            transition: all 0.3s ease !important;
        }

        .css-1d391kg .stSelectbox > div > div:hover {
            border-color: rgba(255, 215, 0, 0.4) !important;
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.15) 0%, 
                rgba(255, 215, 0, 0.06) 100%) !important;
            box-shadow: 
                0 6px 16px rgba(255, 215, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
        }

        /* Enhanced Sidebar Text Inputs */
        .css-1d391kg .stTextInput > div > div > input {
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.08) 0%, 
                rgba(255, 215, 0, 0.02) 100%) !important;
            border: 1px solid rgba(255, 215, 0, 0.15) !important;
            border-radius: 10px !important;
            color: var(--text-primary) !important;
            font-weight: 500 !important;
            backdrop-filter: blur(8px) !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
            transition: all 0.3s ease !important;
        }

        .css-1d391kg .stTextInput > div > div > input:focus {
            border-color: var(--osrs-gold) !important;
            background: linear-gradient(135deg, 
                rgba(255, 215, 0, 0.08) 0%, 
                rgba(255, 255, 255, 0.06) 100%) !important;
            box-shadow: 
                0 0 0 3px rgba(255, 215, 0, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
        }

        /* Enhanced Sidebar Captions & Help Text */
        .css-1d391kg .caption,
        .css-1d391kg small,
        .css-1d391kg [data-testid="help-tooltip"] {
            color: rgba(176, 184, 197, 0.9) !important;
            font-size: 0.8rem !important;
            font-weight: 400 !important;
            line-height: 1.4 !important;
            margin-top: 4px !important;
        }

        /* Enhanced Input Fields */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stNumberInput > div > div > input {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-primary) !important;
            border-radius: 8px !important;
            color: var(--text-primary) !important;
            font-size: 0.875rem !important;
            transition: all 0.2s ease !important;
        }

        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stNumberInput > div > div > input:focus {
            border-color: var(--osrs-blue-light) !important;
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1) !important;
            outline: none !important;
        }
        
        /* Premium Table Visual Hierarchy & Profit Psychology */
        .stDataFrame {
            background: linear-gradient(145deg, 
                rgba(255, 255, 255, 0.08) 0%, 
                rgba(255, 215, 0, 0.02) 50%, 
                rgba(255, 255, 255, 0.04) 100%) !important;
            border: 1px solid rgba(255, 215, 0, 0.2) !important;
            border-radius: 20px !important;
            overflow: hidden !important;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                0 2px 8px rgba(255, 215, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(15px) !important;
            position: relative !important;
            margin: 20px 0 !important;
        }
        
        .stDataFrame::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            height: 3px !important;
            background: linear-gradient(90deg, 
                rgba(255, 215, 0, 0.8) 0%, 
                rgba(74, 144, 226, 0.6) 50%, 
                rgba(255, 215, 0, 0.8) 100%) !important;
            border-radius: 20px 20px 0 0 !important;
        }
        
        /* Premium Table Structure */
        .stDataFrame table {
            background: transparent !important;
            font-family: 'Inter', sans-serif !important;
            border-collapse: separate !important;
            border-spacing: 0 2px !important;
            width: 100% !important;
        }
        
        /* Enhanced Premium Headers */
        .stDataFrame th {
            background: linear-gradient(135deg, 
                rgba(255, 215, 0, 0.15) 0%, 
                rgba(74, 144, 226, 0.1) 50%, 
                rgba(255, 215, 0, 0.08) 100%) !important;
            color: var(--osrs-gold) !important;
            font-weight: 800 !important;
            font-size: 0.8rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
            border: none !important;
            padding: 18px 14px !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4) !important;
            position: relative !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stDataFrame th::after {
            content: '' !important;
            position: absolute !important;
            bottom: 0 !important;
            left: 10% !important;
            right: 10% !important;
            height: 2px !important;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(255, 215, 0, 0.6), 
                transparent) !important;
        }
        
        /* Profit-Based Row Psychology & Visual Hierarchy */
        .stDataFrame td {
            border: none !important;
            color: var(--text-primary) !important;
            padding: 16px 14px !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
            backdrop-filter: blur(5px) !important;
        }
        
        /* Exceptional Profit Rows (5000+ gp) - Gold Theme */
        .stDataFrame tr:has-text("🏆 EXCEPTIONAL") {
            background: linear-gradient(90deg, 
                rgba(255, 215, 0, 0.12) 0%, 
                rgba(255, 215, 0, 0.06) 50%, 
                rgba(255, 215, 0, 0.12) 100%) !important;
            border-left: 4px solid #FFD700 !important;
            box-shadow: 
                0 2px 8px rgba(255, 215, 0, 0.2),
                inset 0 1px 0 rgba(255, 215, 0, 0.3) !important;
        }
        
        .stDataFrame tr:has-text("🏆 EXCEPTIONAL") td {
            color: #FFFFFF !important;
            font-weight: 600 !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
        }
        
        .stDataFrame tr:has-text("🏆 EXCEPTIONAL"):hover {
            background: linear-gradient(90deg, 
                rgba(255, 215, 0, 0.2) 0%, 
                rgba(255, 215, 0, 0.1) 50%, 
                rgba(255, 215, 0, 0.2) 100%) !important;
            transform: translateY(-2px) scale(1.01) !important;
            box-shadow: 
                0 8px 25px rgba(255, 215, 0, 0.3),
                inset 0 1px 0 rgba(255, 215, 0, 0.4) !important;
        }
        
        /* Excellent Profit Rows (2000+ gp) - Green Theme */
        .stDataFrame tr:has-text("🥇 EXCELLENT") {
            background: linear-gradient(90deg, 
                rgba(76, 175, 80, 0.1) 0%, 
                rgba(76, 175, 80, 0.04) 50%, 
                rgba(76, 175, 80, 0.1) 100%) !important;
            border-left: 3px solid #4CAF50 !important;
            box-shadow: 
                0 2px 6px rgba(76, 175, 80, 0.15),
                inset 0 1px 0 rgba(76, 175, 80, 0.2) !important;
        }
        
        .stDataFrame tr:has-text("🥇 EXCELLENT"):hover {
            background: linear-gradient(90deg, 
                rgba(76, 175, 80, 0.15) 0%, 
                rgba(76, 175, 80, 0.08) 50%, 
                rgba(76, 175, 80, 0.15) 100%) !important;
            transform: translateY(-1px) scale(1.005) !important;
            box-shadow: 
                0 6px 20px rgba(76, 175, 80, 0.2),
                inset 0 1px 0 rgba(76, 175, 80, 0.3) !important;
        }
        
        /* Good Profit Rows (1000+ gp) - Blue Theme */
        .stDataFrame tr:has-text("🥈 GOOD") {
            background: linear-gradient(90deg, 
                rgba(74, 144, 226, 0.08) 0%, 
                rgba(74, 144, 226, 0.03) 50%, 
                rgba(74, 144, 226, 0.08) 100%) !important;
            border-left: 2px solid #4A90E2 !important;
            box-shadow: 
                0 1px 4px rgba(74, 144, 226, 0.1),
                inset 0 1px 0 rgba(74, 144, 226, 0.15) !important;
        }
        
        .stDataFrame tr:has-text("🥈 GOOD"):hover {
            background: linear-gradient(90deg, 
                rgba(74, 144, 226, 0.12) 0%, 
                rgba(74, 144, 226, 0.06) 50%, 
                rgba(74, 144, 226, 0.12) 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 
                0 4px 15px rgba(74, 144, 226, 0.15),
                inset 0 1px 0 rgba(74, 144, 226, 0.25) !important;
        }
        
        /* Decent Profit Rows (500+ gp) - Orange Theme */
        .stDataFrame tr:has-text("🥉 DECENT") {
            background: linear-gradient(90deg, 
                rgba(255, 140, 0, 0.06) 0%, 
                rgba(255, 140, 0, 0.02) 50%, 
                rgba(255, 140, 0, 0.06) 100%) !important;
            border-left: 2px solid #FF8C00 !important;
            box-shadow: inset 0 1px 0 rgba(255, 140, 0, 0.1) !important;
        }
        
        .stDataFrame tr:has-text("🥉 DECENT"):hover {
            background: linear-gradient(90deg, 
                rgba(255, 140, 0, 0.1) 0%, 
                rgba(255, 140, 0, 0.04) 50%, 
                rgba(255, 140, 0, 0.1) 100%) !important;
            box-shadow: 
                0 2px 10px rgba(255, 140, 0, 0.1),
                inset 0 1px 0 rgba(255, 140, 0, 0.2) !important;
        }
        
        /* Low Profit Rows - Muted Theme */
        .stDataFrame tr:has-text("⚠️ LOW") {
            background: linear-gradient(90deg, 
                rgba(255, 255, 255, 0.03) 0%, 
                rgba(255, 255, 255, 0.01) 50%, 
                rgba(255, 255, 255, 0.03) 100%) !important;
            border-left: 1px solid rgba(255, 255, 255, 0.2) !important;
            opacity: 0.8 !important;
        }
        
        .stDataFrame tr:has-text("⚠️ LOW"):hover {
            background: linear-gradient(90deg, 
                rgba(255, 255, 255, 0.06) 0%, 
                rgba(255, 255, 255, 0.02) 50%, 
                rgba(255, 255, 255, 0.06) 100%) !important;
            opacity: 1 !important;
        }
        
        /* Enhanced Risk Indicator Integration */
        .stDataFrame td:has-text("🟢 SAFE") {
            position: relative !important;
        }
        
        .stDataFrame td:has-text("🟢 SAFE")::before {
            content: '🛡️' !important;
            position: absolute !important;
            right: -15px !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            opacity: 0.6 !important;
            font-size: 0.8rem !important;
        }
        
        /* Alternating Row Enhancement */
        .stDataFrame tbody tr:nth-child(even) {
            background: rgba(255, 255, 255, 0.02) !important;
        }
        
        .stDataFrame tbody tr:nth-child(odd) {
            background: rgba(0, 0, 0, 0.02) !important;
        }
        
        /* Table Integration Polish - Better Section Flow */
        .stDataFrame {
            margin-top: 8px !important;
            border-top: 3px solid transparent !important;
            border-image: linear-gradient(90deg, 
                rgba(255, 215, 0, 0.6), 
                rgba(74, 144, 226, 0.4), 
                rgba(255, 215, 0, 0.6)) 1 !important;
        }
        
        /* Premium Row Spacing and Typography */
        .stDataFrame tr {
            margin-bottom: 2px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        
        .stDataFrame td:first-child {
            font-weight: 600 !important;
            color: #FFFFFF !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5) !important;
        }
        
        /* Volume-based visual cues */
        .stDataFrame td:nth-child(5) {
            font-weight: 600 !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        
        /* Profit column enhancement */
        .stDataFrame td:nth-child(4) {
            font-weight: 700 !important;
            font-family: 'JetBrains Mono', monospace !important;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
        }
        
        /* Profit/Loss Visual Enhancements */
        .stDataFrame td:has-text("EXCEPTIONAL") {
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(76, 175, 80, 0.1)) !important;
            font-weight: 600 !important;
            color: #FFD700 !important;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
        }
        
        .stDataFrame td:has-text("EXCELLENT") {
            background: linear-gradient(135deg, rgba(76, 175, 80, 0.12), rgba(74, 144, 226, 0.08)) !important;
            font-weight: 600 !important;
            color: #4CAF50 !important;
        }
        
        /* Volume Indicators Enhancement */
        .stDataFrame td:has-text("HIGH") {
            position: relative !important;
        }
        
        .stDataFrame td:has-text("HIGH")::before {
            content: '🌊' !important;
            position: absolute !important;
            left: -20px !important;
            opacity: 0.6 !important;
            animation: wave 2s ease-in-out infinite !important;
        }
        
        @keyframes wave {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-3px); }
        }
        
        /* Alternating Row Enhancement */
        .stDataFrame tr:nth-child(even) {
            background: rgba(255, 255, 255, 0.02) !important;
        }
        
        .stDataFrame tr:nth-child(odd) {
            background: rgba(0, 0, 0, 0.02) !important;
        }

        /* Status Indicators */
        .status-excellent {
            color: var(--osrs-green-light) !important;
            font-weight: 600 !important;
        }

        .status-good {
            color: var(--osrs-orange) !important;
            font-weight: 600 !important;
        }

        .status-caution {
            color: var(--osrs-red-light) !important;
            font-weight: 600 !important;
        }

        /* Expandable Sections */
        .streamlit-expanderHeader {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-primary) !important;
            border-radius: 8px !important;
            color: var(--text-primary) !important;
            font-weight: 500 !important;
        }

        .streamlit-expanderContent {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-primary) !important;
            border-top: none !important;
            border-radius: 0 0 8px 8px !important;
        }

        /* Success/Warning/Error Messages */
        .stSuccess {
            background: rgba(34, 139, 34, 0.1) !important;
            border: 1px solid rgba(34, 139, 34, 0.3) !important;
            border-radius: 8px !important;
            color: var(--osrs-green-light) !important;
        }

        .stWarning {
            background: rgba(255, 140, 0, 0.1) !important;
            border: 1px solid rgba(255, 140, 0, 0.3) !important;
            border-radius: 8px !important;
            color: var(--osrs-orange) !important;
        }

        .stError {
            background: rgba(220, 20, 60, 0.1) !important;
            border: 1px solid rgba(220, 20, 60, 0.3) !important;
            border-radius: 8px !important;
            color: var(--osrs-red-light) !important;
        }

        .stInfo {
            background: rgba(74, 144, 226, 0.1) !important;
            border: 1px solid rgba(74, 144, 226, 0.3) !important;
            border-radius: 8px !important;
            color: var(--osrs-blue-light) !important;
        }

        /* Pagination Controls */
        .pagination-container {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-primary) !important;
            border-radius: 12px !important;
            padding: 16px !important;
            margin: 20px 0 !important;
            text-align: center !important;
            backdrop-filter: blur(20px) !important;
        }

        /* Loading Animations */
        @keyframes osrs-pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .osrs-loading {
            animation: osrs-pulse 2s infinite;
            color: var(--text-accent) !important;
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px !important;
            height: 8px !important;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-secondary) !important;
            border-radius: 4px !important;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--osrs-blue) !important;
            border-radius: 4px !important;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--osrs-blue-light) !important;
        }

        /* Mobile Responsiveness */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem !important;
            }
            
            h1 {
                font-size: 2rem !important;
            }
            
            .osrs-card {
                padding: 16px !important;
                margin: 12px 0 !important;
            }
            
            [data-testid="metric-container"] {
                padding: 16px !important;
            }
        }
        
        /* Filter Section Animation */
        @keyframes section-glow {
            0%, 100% { 
                box-shadow: 
                    0 8px 25px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
            }
            50% { 
                box-shadow: 
                    0 8px 25px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1),
                    0 0 20px rgba(255, 215, 0, 0.1);
            }
        }

        .filter-section.active {
            animation: section-glow 3s ease-in-out !important;
        }

        /* Utility Classes */
        .text-accent { color: var(--text-accent) !important; }
        .text-primary { color: var(--text-primary) !important; }
        .text-secondary { color: var(--text-secondary) !important; }
        .text-muted { color: var(--text-muted) !important; }
        
        .bg-card { background: var(--bg-card) !important; }
        .border-accent { border-color: var(--border-accent) !important; }
        
        .osrs-gold { color: var(--osrs-gold) !important; }
        .osrs-blue { color: var(--osrs-blue-light) !important; }
        .osrs-green { color: var(--osrs-green-light) !important; }
        .osrs-red { color: var(--osrs-red-light) !important; }
    </style>
    """, unsafe_allow_html=True)


def inject_interactive_javascript():
    """Inject enhanced interactive JavaScript for better UX"""
    st.markdown("""
    <script>
        // Modern page transitions
        function initOSRSApp() {
            // Add loading states
            const buttons = document.querySelectorAll('.stButton button');
            buttons.forEach(button => {
                button.addEventListener('click', function() {
                    this.innerHTML = '<span class="osrs-loading">Loading...</span>';
                    setTimeout(() => {
                        this.innerHTML = this.getAttribute('data-original-text') || 'Processing';
                    }, 1000);
                });
            });

            // Enhanced hover effects
            const cards = document.querySelectorAll('.osrs-card');
            cards.forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-8px) scale(1.02)';
                });
                card.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0) scale(1)';
                });
            });

            // Keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                // Ctrl+R to refresh
                if (e.ctrlKey && e.key === 'r') {
                    e.preventDefault();
                    const refreshBtn = document.querySelector('button[data-testid="refresh-data"]');
                    if (refreshBtn) refreshBtn.click();
                }
                
                // Escape to clear selection
                if (e.key === 'Escape') {
                    const activeElement = document.activeElement;
                    if (activeElement) activeElement.blur();
                }
            });
        }

        // Initialize when page loads
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initOSRSApp);
        } else {
            initOSRSApp();
        }

        // Reinitialize on Streamlit updates
        window.addEventListener('load', function() {
            setTimeout(initOSRSApp, 1000);
        });
    </script>
    """, unsafe_allow_html=True)


# Legacy compatibility - keep for now
def inject_main_styles():
    """Legacy function - redirects to modern styles"""
    inject_modern_osrs_styles()


def inject_interactive_javascript_legacy():
    """Legacy function - redirects to modern JS"""
    inject_interactive_javascript()
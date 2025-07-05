"""
OSRS Flip Assistant - Main Styles
All CSS styling for the application in one organized place
"""

import streamlit as st


def inject_main_styles():
    """Inject all custom CSS styles for the OSRS Flip Assistant"""
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Root Variables */
        :root {
            --primary-bg: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            --card-bg: rgba(255, 255, 255, 0.05);
            --card-border: rgba(255, 255, 255, 0.1);
            --accent-color: #4CAF50;
            --text-primary: #e0e0e0;
            --text-secondary: #bbb;
            --osrs-gold: #ffd700;
        }

        /* Global Overrides */
        .stApp {
            background: var(--primary-bg) !important;
            font-family: 'Inter', 'Segoe UI', sans-serif !important;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Main content styling */
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1400px !important;
        }

        /* Headers */
        h1, h2, h3 {
            color: var(--osrs-gold) !important;
            font-weight: 600 !important;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5) !important;
        }

        h1 {
            font-size: 2.5rem !important;
            margin-bottom: 1rem !important;
        }

        /* Card-like containers */
        .stContainer > div {
            background: var(--card-bg) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 15px !important;
            padding: 20px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        }

        /* Sidebar styling */
        .css-1d391kg {
            background: rgba(255, 255, 255, 0.03) !important;
            border-right: 1px solid var(--card-border) !important;
        }

        /* Text color overrides */
        .stMarkdown, .stText, p, span, div {
            color: var(--text-primary) !important;
        }

        /* Metric styling */
        [data-testid="metric-container"] {
            background: var(--card-bg) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 10px !important;
            padding: 15px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        }

        [data-testid="metric-container"]:hover {
            transform: translateY(-2px) !important;
            border-color: var(--accent-color) !important;
            transition: all 0.2s ease !important;
        }

        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent-color), #45a049) !important;
            border: none !important;
            border-radius: 8px !important;
            color: white !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2) !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3) !important;
        }

        /* Input styling */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stSlider > div > div > div > div {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 8px !important;
            color: var(--text-primary) !important;
        }

        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus {
            border-color: var(--accent-color) !important;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
        }

        /* Enhanced Sidebar Styling */
        .css-1d391kg, .css-1cypcdb, .css-17eq0hr {
            background: rgba(255, 255, 255, 0.03) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }

        /* Sidebar headers */
        .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
            color: #4CAF50 !important;
            border-bottom: 1px solid rgba(76, 175, 80, 0.2) !important;
            padding-bottom: 10px !important;
            margin-bottom: 15px !important;
        }

        /* Results container */
        .results-container {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
            margin: 20px 0 !important;
        }

        .table-header {
            background: rgba(76, 175, 80, 0.1) !important;
            border-bottom: 1px solid rgba(76, 175, 80, 0.3) !important;
            padding: 15px 20px !important;
            margin-bottom: 0 !important;
        }

        .table-header h2 {
            color: #4CAF50 !important;
            font-size: 1.5rem !important;
            margin-bottom: 5px !important;
        }

        .table-header p {
            color: #bbb !important;
            margin: 0 !important;
            font-size: 0.9rem !important;
        }

        /* DataFrames styling */
        .stDataFrame {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
        }

        .stDataFrame table {
            background: transparent !important;
        }

        .stDataFrame th {
            background: rgba(76, 175, 80, 0.1) !important;
            color: #4CAF50 !important;
            font-weight: 600 !important;
            border-bottom: 2px solid rgba(76, 175, 80, 0.3) !important;
        }

        .stDataFrame td {
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            color: #e0e0e0 !important;
        }

        .stDataFrame tr:hover {
            background: rgba(76, 175, 80, 0.05) !important;
        }

        /* Alert panels */
        .alert-success {
            background: rgba(40, 167, 69, 0.1) !important;
            border: 1px solid rgba(40, 167, 69, 0.3) !important;
            border-radius: 8px !important;
            padding: 15px !important;
            margin: 20px 0 !important;
            color: #28a745 !important;
        }

        .alert-warning {
            background: rgba(255, 193, 7, 0.1) !important;
            border: 1px solid rgba(255, 193, 7, 0.3) !important;
            border-radius: 8px !important;
            padding: 15px !important;
            margin: 20px 0 !important;
            color: #ffc107 !important;
        }

        .alert-danger {
            background: rgba(220, 53, 69, 0.1) !important;
            border: 1px solid rgba(220, 53, 69, 0.3) !important;
            border-radius: 8px !important;
            padding: 15px !important;
            margin: 20px 0 !important;
            color: #dc3545 !important;
        }

        /* Metric cards */
        .metric-card {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            text-align: center !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        }

        .metric-card:hover {
            transform: translateY(-3px) !important;
            border-color: #4CAF50 !important;
            box-shadow: 0 8px 24px rgba(76, 175, 80, 0.2) !important;
        }

        .metric-value {
            font-size: 2rem !important;
            font-weight: bold !important;
            color: #4CAF50 !important;
            margin-bottom: 5px !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        }

        .metric-label {
            color: #bbb !important;
            font-size: 0.9rem !important;
            font-weight: 400 !important;
        }

        /* Enhanced pagination */
        .pagination-container {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            padding: 15px !important;
            margin: 20px 0 !important;
            text-align: center !important;
        }

        .pagination-info {
            color: #4CAF50 !important;
            font-weight: 500 !important;
            font-size: 1rem !important;
        }

        /* Loading spinner */
        .loading-spinner {
            display: inline-block !important;
            width: 20px !important;
            height: 20px !important;
            border: 3px solid rgba(76, 175, 80, 0.3) !important;
            border-radius: 50% !important;
            border-top-color: #4CAF50 !important;
            animation: spin 1s ease-in-out infinite !important;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Mobile Responsive Improvements */
        @media (max-width: 768px) {
            .stApp {
                padding: 10px !important;
            }

            .main .block-container {
                padding: 1rem !important;
                max-width: 100% !important;
            }

            h1 {
                font-size: 1.8rem !important;
                text-align: center !important;
            }

            .metric-card {
                padding: 15px 10px !important;
                margin-bottom: 10px !important;
            }

            .metric-value {
                font-size: 1.5rem !important;
            }
        }

        /* Enhanced scrollbar */
        ::-webkit-scrollbar {
            width: 12px !important;
        }

        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 6px !important;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(76, 175, 80, 0.3) !important;
            border-radius: 6px !important;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(76, 175, 80, 0.5) !important;
        }
    </style>
    """, unsafe_allow_html=True)


def inject_interactive_javascript():
    """Inject interactive JavaScript for enhanced UX"""
    st.markdown("""
    <script>
        // Add smooth animations to elements as they appear
        function addAnimations() {
            const elements = document.querySelectorAll('.metric-card, .results-container');
            elements.forEach((el, index) => {
                el.style.animationDelay = (index * 0.1) + 's';
                el.style.animation = 'fadeInUp 0.6s ease-out forwards';
            });
        }

        // Add keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl+R to refresh
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                const refreshBtn = document.querySelector('[data-testid="stButton"] button');
                if (refreshBtn && refreshBtn.textContent.includes('Refresh')) {
                    refreshBtn.click();
                }
            }
        });

        // Run animations when page loads
        setTimeout(addAnimations, 100);
    </script>

    <style>
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
    """, unsafe_allow_html=True)
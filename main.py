"""
OSRS Grand Exchange Flipping Assistant
Entry point for the Streamlit application

Run with: streamlit run main.py
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main application
if __name__ == "__main__":
    from src.osrs_flip_assistant import streamlit_dashboard
    streamlit_dashboard()
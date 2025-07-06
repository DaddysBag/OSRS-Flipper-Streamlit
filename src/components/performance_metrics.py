"""
Performance Metrics Component
Real-time performance monitoring and optimization insights
"""

import streamlit as st
import time
import pandas as pd
from src.utils.cache_optimizer import get_performance_stats


def create_performance_dashboard():
    """Create a collapsible performance monitoring dashboard"""

    with st.expander("⚡ Performance Monitor", expanded=False):
        # Get current performance stats
        perf_stats = get_performance_stats()

        # Create metrics layout
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Cache Hit Rate",
                f"{perf_stats['hit_rate']:.1f}%",
                delta=f"{'Excellent' if perf_stats['hit_rate'] >= 80 else 'Good' if perf_stats['hit_rate'] >= 60 else 'Needs Work'}"
            )

        with col2:
            st.metric(
                "Total Requests",
                perf_stats['total_requests'],
                delta=f"{perf_stats['hits']} hits"
            )

        with col3:
            avg_load_time = get_average_load_time()
            st.metric(
                "Avg Load Time",
                f"{avg_load_time:.2f}s",
                delta=f"{'Fast' if avg_load_time < 2 else 'Slow'}"
            )

        with col4:
            memory_usage = get_memory_usage()
            st.metric(
                "Memory Usage",
                f"{memory_usage:.1f}MB",
                delta=f"{'Optimal' if memory_usage < 100 else 'High'}"
            )

        # Performance recommendations
        create_performance_recommendations(perf_stats)


def get_average_load_time():
    """Calculate average load time from performance metrics"""
    if 'performance_metrics' not in st.session_state:
        return 0.0

    metrics = st.session_state.performance_metrics
    if not metrics:
        return 0.0

    recent_metrics = [m for m in metrics if time.time() - m['timestamp'] < 300]  # Last 5 minutes
    if not recent_metrics:
        return 0.0

    return sum(m['execution_time'] for m in recent_metrics) / len(recent_metrics)


def get_memory_usage():
    """Estimate current memory usage"""
    # Simple estimation based on session state size
    import sys

    total_size = 0
    for key, value in st.session_state.items():
        total_size += sys.getsizeof(value)

    return total_size / (1024 * 1024)  # Convert to MB


def create_performance_recommendations(perf_stats):
    """Create performance optimization recommendations"""
    st.markdown("### 🎯 Performance Insights")

    recommendations = []

    if perf_stats['hit_rate'] < 60:
        recommendations.append("🔄 **Low cache hit rate** - Consider increasing cache TTL values")

    if get_average_load_time() > 3:
        recommendations.append("⏱️ **Slow load times** - Enable 'Show All' less frequently")

    if get_memory_usage() > 150:
        recommendations.append("🧠 **High memory usage** - Clear cache periodically")

    if not recommendations:
        recommendations.append("✅ **Performance is optimal** - All systems running efficiently")

    for rec in recommendations:
        st.markdown(f"- {rec}")


def create_performance_badge_advanced():
    """Create an advanced floating performance badge"""
    perf_stats = get_performance_stats()
    avg_time = get_average_load_time()

    # Determine overall performance status
    if perf_stats['hit_rate'] >= 80 and avg_time < 2:
        status = "🚀 Excellent"
        color = "#27ae60"
    elif perf_stats['hit_rate'] >= 60 and avg_time < 4:
        status = "⚡ Good"
        color = "#f39c12"
    else:
        status = "🐌 Optimizing"
        color = "#e74c3c"

    st.markdown(f"""
    <div style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: {color};
        color: white;
        padding: 10px 15px;
        border-radius: 25px;
        font-size: 0.85rem;
        font-weight: 600;
        z-index: 1000;
        backdrop-filter: blur(10px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        cursor: pointer;
        transition: all 0.3s ease;
    " title="Cache: {perf_stats['hit_rate']:.1f}% | Load: {avg_time:.1f}s">
        {status}
    </div>
    """, unsafe_allow_html=True)
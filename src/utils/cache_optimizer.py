"""
Advanced Cache Optimization for OSRS Flip Assistant
Implements multi-level caching for optimal performance
"""

import streamlit as st
import pandas as pd
import time
from functools import wraps
from typing import Any, Optional, Callable


class PerformanceCache:
    """Multi-level caching system for OSRS data"""

    def __init__(self):
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        if self.cache_stats['total_requests'] == 0:
            return 0.0
        return (self.cache_stats['hits'] / self.cache_stats['total_requests']) * 100

    def record_hit(self):
        """Record cache hit"""
        self.cache_stats['hits'] += 1
        self.cache_stats['total_requests'] += 1

    def record_miss(self):
        """Record cache miss"""
        self.cache_stats['misses'] += 1
        self.cache_stats['total_requests'] += 1


# Global cache instance
performance_cache = PerformanceCache()


def cache_with_performance_tracking(ttl: int = 300):
    """Decorator to add performance tracking to Streamlit cache"""

    def decorator(func: Callable) -> Callable:
        # Apply Streamlit cache
        cached_func = st.cache_data(ttl=ttl)(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Check if data is in cache
            cache_key = str(args) + str(sorted(kwargs.items()))

            try:
                result = cached_func(*args, **kwargs)
                performance_cache.record_hit()
            except Exception:
                result = func(*args, **kwargs)
                performance_cache.record_miss()

            end_time = time.time()
            execution_time = end_time - start_time

            # Store performance metrics
            if 'performance_metrics' not in st.session_state:
                st.session_state.performance_metrics = []

            st.session_state.performance_metrics.append({
                'function': func.__name__,
                'execution_time': execution_time,
                'timestamp': time.time(),
                'cached': performance_cache.cache_stats['hits'] > 0
            })

            return result

        return wrapper

    return decorator


@cache_with_performance_tracking(ttl=60)  # 1 minute for real-time data
def get_cached_market_data(mode: str):
    """Cache market data with 1-minute TTL"""
    from filters import run_flip_scanner
    return run_flip_scanner(mode)


@cache_with_performance_tracking(ttl=300)  # 5 minutes for processed data
def get_cached_analysis_data(df: pd.DataFrame):
    """Cache analysis calculations with 5-minute TTL"""
    if df.empty:
        return {}

    return {
        'total_opportunities': len(df),
        'exceptional_count': len(df[df['profit'] >= 100000]),
        'safe_trades': len(df[df['risk_score'] <= 3]),
        'avg_profit': df['profit'].mean(),
        'total_volume': df['volume'].sum()
    }


def get_performance_stats():
    """Get current performance statistics"""
    return {
        'hit_rate': performance_cache.get_hit_rate(),
        'total_requests': performance_cache.cache_stats['total_requests'],
        'hits': performance_cache.cache_stats['hits'],
        'misses': performance_cache.cache_stats['misses']
    }
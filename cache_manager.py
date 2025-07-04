"""
OSRS Cache Manager
Handles caching for API responses and expensive calculations
"""

import streamlit as st
import datetime
import json
import hashlib
from typing import Any, Optional, Dict, Callable
import pandas as pd


class CacheManager:
    """Manages caching with TTL (Time To Live) for API responses and calculations"""

    def __init__(self):
        # Don't initialize session state here - do it lazily when first accessed
        pass

    def _ensure_cache_initialized(self):
        """Ensure cache is initialized in session state"""
        if 'osrs_cache' not in st.session_state:
            st.session_state.osrs_cache = {}

        if 'cache_stats' not in st.session_state:
            st.session_state.cache_stats = {
                'hits': 0,
                'misses': 0,
                'total_requests': 0
            }

    def _get_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate unique cache key from function name and parameters"""
        # Create a string representation of all parameters
        key_data = {
            'func': func_name,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }

        # Hash it for consistent key length
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, func_name: str, ttl_minutes: int, *args, **kwargs) -> Optional[Any]:
        """Get cached result if available and not expired"""
        self._ensure_cache_initialized()  # Add this line

        cache_key = self._get_cache_key(func_name, *args, **kwargs)

        st.session_state.cache_stats['total_requests'] += 1

        if cache_key in st.session_state.osrs_cache:
            cached_item = st.session_state.osrs_cache[cache_key]

            # Check if cache is still valid
            now = datetime.datetime.now()
            if now < cached_item['expires']:
                st.session_state.cache_stats['hits'] += 1
                return cached_item['data']
            else:
                # Remove expired cache
                del st.session_state.osrs_cache[cache_key]

        st.session_state.cache_stats['misses'] += 1
        return None

    def set(self, func_name: str, ttl_minutes: int, data: Any, *args, **kwargs) -> None:
        """Store data in cache with TTL"""
        self._ensure_cache_initialized()  # Add this line

        cache_key = self._get_cache_key(func_name, *args, **kwargs)

        expires = datetime.datetime.now() + datetime.timedelta(minutes=ttl_minutes)

        st.session_state.osrs_cache[cache_key] = {
            'data': data,
            'expires': expires,
            'created': datetime.datetime.now(),
            'func_name': func_name
        }

    def cached_call(self, func: Callable, ttl_minutes: int, *args, **kwargs) -> Any:
        """Execute function with caching"""
        func_name = func.__name__

        # Try to get from cache first
        cached_result = self.get(func_name, ttl_minutes, *args, **kwargs)
        if cached_result is not None:
            return cached_result

        # Not in cache, execute function
        result = func(*args, **kwargs)

        # Store in cache
        self.set(func_name, ttl_minutes, result, *args, **kwargs)

        return result

    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries, optionally matching a pattern"""
        self._ensure_cache_initialized()  # Add this line

        if pattern is None:
            count = len(st.session_state.osrs_cache)
            st.session_state.osrs_cache = {}
            return count

        # Clear entries matching pattern
        keys_to_remove = []
        for key, value in st.session_state.osrs_cache.items():
            if pattern in value['func_name']:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del st.session_state.osrs_cache[key]

        return len(keys_to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        self._ensure_cache_initialized()  # Add this line

        stats = st.session_state.cache_stats.copy()
        cache_size = len(st.session_state.osrs_cache)

        if stats['total_requests'] > 0:
            hit_rate = (stats['hits'] / stats['total_requests']) * 100
        else:
            hit_rate = 0

        # Cache info
        cache_info = {}
        for key, value in st.session_state.osrs_cache.items():
            func_name = value['func_name']
            if func_name not in cache_info:
                cache_info[func_name] = 0
            cache_info[func_name] += 1

        return {
            'hit_rate': hit_rate,
            'total_requests': stats['total_requests'],
            'cache_hits': stats['hits'],
            'cache_misses': stats['misses'],
            'cache_size': cache_size,
            'cached_functions': cache_info
        }


# Global cache manager instance
cache_manager = CacheManager()


def show_cache_stats():
    """Display cache statistics for debugging"""
    stats = cache_manager.get_stats()

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ Cache Performance")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        st.metric("Hit Rate", f"{stats['hit_rate']:.1f}%")
        st.metric("Cache Size", stats['cache_size'])

    with col2:
        st.metric("Total Requests", stats['total_requests'])
        if st.button("🗑️ Clear Cache", key="clear_cache_btn"):
            cleared = cache_manager.clear_cache()
            st.success(f"Cleared {cleared} entries")
            st.rerun()

    # Show cached functions
    if stats['cached_functions']:
        st.sidebar.write("**Cached Functions:**")
        for func, count in stats['cached_functions'].items():
            st.sidebar.write(f"• {func}: {count} entries")
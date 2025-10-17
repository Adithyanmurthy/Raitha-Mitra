"""
Rate Limiter Module
Implements per-user rate limiting for AI API calls
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock


class RateLimiter:
    """
    Simple in-memory rate limiter for AI API calls
    
    Tracks API calls per user and enforces limits
    """
    
    def __init__(self):
        # Store: {user_id: [(timestamp, api_type), ...]}
        self.call_history = defaultdict(list)
        self.lock = Lock()
        
        # Rate limits (calls per time window)
        self.limits = {
            'chat': {
                'calls': 50,  # 50 messages
                'window': 3600  # per hour
            },
            'schedule': {
                'calls': 10,  # 10 schedule generations
                'window': 3600  # per hour
            },
            'yield_prediction': {
                'calls': 20,  # 20 predictions
                'window': 3600  # per hour
            },
            'financial_score': {
                'calls': 30,  # 30 score calculations
                'window': 3600  # per hour
            }
        }
    
    def check_rate_limit(self, user_id, api_type):
        """
        Check if user has exceeded rate limit for given API type
        
        Args:
            user_id: User ID
            api_type: Type of API call ('chat', 'schedule', 'yield_prediction', 'financial_score')
            
        Returns:
            tuple: (allowed: bool, remaining: int, reset_time: int)
        """
        if api_type not in self.limits:
            # Unknown API type, allow by default
            return True, 999, 0
        
        with self.lock:
            current_time = time.time()
            limit_config = self.limits[api_type]
            window_start = current_time - limit_config['window']
            
            # Get user's call history
            user_calls = self.call_history[user_id]
            
            # Filter calls within the time window for this API type
            recent_calls = [
                (ts, api) for ts, api in user_calls
                if ts > window_start and api == api_type
            ]
            
            # Update call history (remove old calls)
            self.call_history[user_id] = [
                (ts, api) for ts, api in user_calls
                if ts > window_start
            ]
            
            # Check if limit exceeded
            call_count = len(recent_calls)
            allowed = call_count < limit_config['calls']
            remaining = max(0, limit_config['calls'] - call_count)
            
            # Calculate reset time (when oldest call expires)
            if recent_calls:
                oldest_call_time = min(ts for ts, _ in recent_calls)
                reset_time = int(oldest_call_time + limit_config['window'])
            else:
                reset_time = int(current_time + limit_config['window'])
            
            return allowed, remaining, reset_time
    
    def record_call(self, user_id, api_type):
        """
        Record an API call for rate limiting
        
        Args:
            user_id: User ID
            api_type: Type of API call
        """
        if api_type not in self.limits:
            return
        
        with self.lock:
            current_time = time.time()
            self.call_history[user_id].append((current_time, api_type))
    
    def get_limit_info(self, api_type):
        """
        Get rate limit information for an API type
        
        Args:
            api_type: Type of API call
            
        Returns:
            dict: Limit configuration
        """
        if api_type not in self.limits:
            return None
        
        config = self.limits[api_type]
        return {
            'calls': config['calls'],
            'window_seconds': config['window'],
            'window_minutes': config['window'] // 60
        }
    
    def reset_user_limits(self, user_id):
        """
        Reset rate limits for a specific user (admin function)
        
        Args:
            user_id: User ID
        """
        with self.lock:
            if user_id in self.call_history:
                del self.call_history[user_id]
    
    def cleanup_old_entries(self):
        """
        Clean up old entries from memory (should be called periodically)
        """
        with self.lock:
            current_time = time.time()
            max_window = max(config['window'] for config in self.limits.values())
            cutoff_time = current_time - max_window
            
            # Remove old entries
            for user_id in list(self.call_history.keys()):
                self.call_history[user_id] = [
                    (ts, api) for ts, api in self.call_history[user_id]
                    if ts > cutoff_time
                ]
                
                # Remove user if no recent calls
                if not self.call_history[user_id]:
                    del self.call_history[user_id]


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(user_id, api_type):
    """
    Convenience function to check rate limit
    
    Args:
        user_id: User ID
        api_type: Type of API call
        
    Returns:
        tuple: (allowed: bool, remaining: int, reset_time: int)
    """
    return rate_limiter.check_rate_limit(user_id, api_type)


def record_api_call(user_id, api_type):
    """
    Convenience function to record an API call
    
    Args:
        user_id: User ID
        api_type: Type of API call
    """
    rate_limiter.record_call(user_id, api_type)


def get_rate_limit_info(api_type):
    """
    Convenience function to get rate limit info
    
    Args:
        api_type: Type of API call
        
    Returns:
        dict: Limit configuration
    """
    return rate_limiter.get_limit_info(api_type)

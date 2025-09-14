"""
Rate limiting service.

Handles rate limiting configuration and dependencies.
"""

import os
from typing import Union, Callable
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter

from app.auth.deps import get_user_or_ip_identifier


def create_rate_limiter(times: int = 60, seconds: int = 60) -> Union[RateLimiter, Callable]:
    """
    Create a rate limiter for generation endpoints.
    
    Args:
        times: Number of requests allowed
        seconds: Time window in seconds
        
    Returns:
        RateLimiter dependency
    """
    # If Redis is disabled, return a no-op limiter
    if os.getenv("NO_REDIS", "0") == "1":
        return lambda: None
    
    return RateLimiter(
        times=times, 
        seconds=seconds, 
        identifier=get_user_or_ip_identifier
    )


def create_file_rate_limiter(times: int = 60, seconds: int = 60) -> Union[RateLimiter, Callable]:
    """
    Create a rate limiter for file download endpoints.
    
    Args:
        times: Number of requests allowed
        seconds: Time window in seconds
        
    Returns:
        RateLimiter dependency
    """
    # If Redis is disabled, return a no-op limiter
    if os.getenv("NO_REDIS", "0") == "1":
        return lambda: None
    
    return RateLimiter(
        times=times, 
        seconds=seconds, 
        identifier=get_user_or_ip_identifier
    )

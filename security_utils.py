"""
Security utilities for input sanitization and validation
"""
import re
import html
from datetime import datetime
from typing import Any, Optional, Union


def sanitize_text(text: str, max_length: int = 5000) -> str:
    """
    Sanitize text input to prevent XSS attacks
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Trim to max length
    text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Escape HTML entities to prevent XSS
    text = html.escape(text)
    
    # Remove any remaining script tags (defense in depth)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text.strip()


def sanitize_message(message: str) -> str:
    """
    Sanitize chat messages and user messages
    
    Args:
        message: Message text to sanitize
        
    Returns:
        Sanitized message
    """
    return sanitize_text(message, max_length=2000)


def sanitize_description(description: str) -> str:
    """
    Sanitize descriptions and notes
    
    Args:
        description: Description text to sanitize
        
    Returns:
        Sanitized description
    """
    return sanitize_text(description, max_length=1000)


def validate_numeric(value: Any, min_value: Optional[float] = None, 
                     max_value: Optional[float] = None) -> Optional[float]:
    """
    Validate and sanitize numeric input
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Validated float value or None if invalid
    """
    try:
        num = float(value)
        
        # Check for NaN or infinity
        if not (num == num) or num == float('inf') or num == float('-inf'):
            return None
        
        # Check bounds
        if min_value is not None and num < min_value:
            return None
        if max_value is not None and num > max_value:
            return None
            
        return num
    except (ValueError, TypeError):
        return None


def validate_integer(value: Any, min_value: Optional[int] = None,
                     max_value: Optional[int] = None) -> Optional[int]:
    """
    Validate and sanitize integer input
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Validated integer value or None if invalid
    """
    try:
        num = int(value)
        
        # Check bounds
        if min_value is not None and num < min_value:
            return None
        if max_value is not None and num > max_value:
            return None
            
        return num
    except (ValueError, TypeError):
        return None


def validate_date(date_str: str) -> Optional[str]:
    """
    Validate date string format
    
    Args:
        date_str: Date string to validate (YYYY-MM-DD format)
        
    Returns:
        Validated date string or None if invalid
    """
    if not isinstance(date_str, str):
        return None
    
    try:
        # Try to parse the date
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        return None


def validate_user_id(user_id: Any) -> Optional[int]:
    """
    Validate user ID
    
    Args:
        user_id: User ID to validate
        
    Returns:
        Validated user ID or None if invalid
    """
    return validate_integer(user_id, min_value=1)


def validate_amount(amount: Any) -> Optional[float]:
    """
    Validate monetary amount
    
    Args:
        amount: Amount to validate
        
    Returns:
        Validated amount or None if invalid
    """
    return validate_numeric(amount, min_value=0, max_value=999999999)


def validate_latitude(lat: Any) -> Optional[float]:
    """
    Validate latitude value
    
    Args:
        lat: Latitude to validate
        
    Returns:
        Validated latitude or None if invalid
    """
    return validate_numeric(lat, min_value=-90, max_value=90)


def validate_longitude(lon: Any) -> Optional[float]:
    """
    Validate longitude value
    
    Args:
        lon: Longitude to validate
        
    Returns:
        Validated longitude or None if invalid
    """
    return validate_numeric(lon, min_value=-180, max_value=180)


def validate_enum(value: str, allowed_values: list) -> Optional[str]:
    """
    Validate that value is in allowed list
    
    Args:
        value: Value to validate
        allowed_values: List of allowed values
        
    Returns:
        Validated value or None if invalid
    """
    if not isinstance(value, str):
        return None
    
    value = value.strip().lower()
    allowed_lower = [v.lower() for v in allowed_values]
    
    if value in allowed_lower:
        # Return original case from allowed_values
        idx = allowed_lower.index(value)
        return allowed_values[idx]
    
    return None


def sanitize_sql_like_pattern(pattern: str) -> str:
    """
    Sanitize pattern for SQL LIKE queries
    
    Args:
        pattern: Pattern to sanitize
        
    Returns:
        Sanitized pattern
    """
    if not isinstance(pattern, str):
        return ""
    
    # Escape special SQL LIKE characters
    pattern = pattern.replace('\\', '\\\\')
    pattern = pattern.replace('%', '\\%')
    pattern = pattern.replace('_', '\\_')
    
    return pattern[:100]  # Limit length

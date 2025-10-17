#!/usr/bin/env python3
"""
Test script for geocoding functionality
"""

from geocoding_utils import geocode_location, get_default_privacy_level

# Test cases
test_locations = [
    "Bangalore",
    "Mumbai",
    "Delhi",
    "Bengaluru, Karnataka",
    "Chennai, Tamil Nadu",
    "Hyderabad",
    "Pune, Maharashtra",
    "Unknown City",
    "Karnataka",  # State fallback
    "",  # Empty
    None,  # None
]

print("=" * 60)
print("GEOCODING TEST")
print("=" * 60)

for location in test_locations:
    lat, lon = geocode_location(location)
    status = "✓" if lat and lon else "✗"
    result = f"({lat}, {lon})" if lat and lon else "Not found"
    print(f"{status} {str(location):30s} -> {result}")

print("\n" + "=" * 60)
print(f"Default privacy level: {get_default_privacy_level()}")
print("=" * 60)

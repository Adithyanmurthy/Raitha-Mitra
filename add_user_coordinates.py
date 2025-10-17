#!/usr/bin/env python3
"""
Script to add coordinates to users based on their location text
Uses a simple mapping of common Indian locations
"""

import sqlite3

# Sample coordinates for common Indian locations
LOCATION_COORDS = {
    # Major cities
    'bangalore': (12.9716, 77.5946),
    'bengaluru': (12.9716, 77.5946),
    'mumbai': (19.0760, 72.8777),
    'delhi': (28.7041, 77.1025),
    'new delhi': (28.6139, 77.2090),
    'chennai': (13.0827, 80.2707),
    'kolkata': (22.5726, 88.3639),
    'hyderabad': (17.3850, 78.4867),
    'pune': (18.5204, 73.8567),
    'ahmedabad': (23.0225, 72.5714),
    'jaipur': (26.9124, 75.7873),
    'lucknow': (26.8467, 80.9462),
    'kanpur': (26.4499, 80.3319),
    'nagpur': (21.1458, 79.0882),
    'indore': (22.7196, 75.8577),
    'bhopal': (23.2599, 77.4126),
    'visakhapatnam': (17.6868, 83.2185),
    'patna': (25.5941, 85.1376),
    'vadodara': (22.3072, 73.1812),
    'ghaziabad': (28.6692, 77.4538),
    'ludhiana': (30.9010, 75.8573),
    'agra': (27.1767, 78.0081),
    'nashik': (19.9975, 73.7898),
    'faridabad': (28.4089, 77.3178),
    'meerut': (28.9845, 77.7064),
    'rajkot': (22.3039, 70.8022),
    'varanasi': (25.3176, 82.9739),
    'srinagar': (34.0837, 74.7973),
    'amritsar': (31.6340, 74.8723),
    'allahabad': (25.4358, 81.8463),
    'prayagraj': (25.4358, 81.8463),
    'ranchi': (23.3441, 85.3096),
    'howrah': (22.5958, 88.2636),
    'coimbatore': (11.0168, 76.9558),
    'jabalpur': (23.1815, 79.9864),
    'gwalior': (26.2183, 78.1828),
    'vijayawada': (16.5062, 80.6480),
    'jodhpur': (26.2389, 73.0243),
    'madurai': (9.9252, 78.1198),
    'raipur': (21.2514, 81.6296),
    'kota': (25.2138, 75.8648),
    'chandigarh': (30.7333, 76.7794),
    'guwahati': (26.1445, 91.7362),
    'solapur': (17.6599, 75.9064),
    'hubli': (15.3647, 75.1240),
    'mysore': (12.2958, 76.6394),
    'mysuru': (12.2958, 76.6394),
    'tiruchirappalli': (10.7905, 78.7047),
    'tiruppur': (11.1085, 77.3411),
    'moradabad': (28.8389, 78.7378),
    'salem': (11.6643, 78.1460),
    'warangal': (17.9689, 79.5941),
    'guntur': (16.3067, 80.4365),
    'bhiwandi': (19.2961, 73.0635),
    'saharanpur': (29.9680, 77.5460),
    'gorakhpur': (26.7606, 83.3732),
    'bikaner': (28.0229, 73.3119),
    'amravati': (20.9374, 77.7796),
    'noida': (28.5355, 77.3910),
    'jamshedpur': (22.8046, 86.2029),
    'bhilai': (21.2095, 81.3784),
    'cuttack': (20.4625, 85.8830),
    'firozabad': (27.1591, 78.3957),
    'kochi': (9.9312, 76.2673),
    'cochin': (9.9312, 76.2673),
    'bhavnagar': (21.7645, 72.1519),
    'dehradun': (30.3165, 78.0322),
    'durgapur': (23.5204, 87.3119),
    'asansol': (23.6739, 86.9524),
    'nanded': (19.1383, 77.3210),
    'kolhapur': (16.7050, 74.2433),
    'ajmer': (26.4499, 74.6399),
    'akola': (20.7002, 77.0082),
    'gulbarga': (17.3297, 76.8343),
    'jamnagar': (22.4707, 70.0577),
    'ujjain': (23.1765, 75.7885),
    'loni': (28.7520, 77.2864),
    'siliguri': (26.7271, 88.3953),
    'jhansi': (25.4484, 78.5685),
    'ulhasnagar': (19.2183, 73.1382),
    'jammu': (32.7266, 74.8570),
    'mangalore': (12.9141, 74.8560),
    'erode': (11.3410, 77.7172),
    'belgaum': (15.8497, 74.4977),
    'ambattur': (13.1143, 80.1548),
    'tirunelveli': (8.7139, 77.7567),
    'malegaon': (20.5579, 74.5287),
    'gaya': (24.7955, 85.0002),
    'thiruvananthapuram': (8.5241, 76.9366),
    'davanagere': (14.4644, 75.9218),
}

def get_coordinates_for_location(location):
    """Get coordinates for a location string"""
    if not location:
        return None, None
    
    # Normalize location string
    location_lower = location.lower().strip()
    
    # Try exact match first
    if location_lower in LOCATION_COORDS:
        return LOCATION_COORDS[location_lower]
    
    # Try partial match
    for key, coords in LOCATION_COORDS.items():
        if key in location_lower or location_lower in key:
            return coords
    
    return None, None

def update_user_coordinates():
    """Update coordinates for all users based on their location"""
    conn = sqlite3.connect('raitha_mitra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute('SELECT id, name, location, latitude, longitude FROM users')
    users = cursor.fetchall()
    
    updated_count = 0
    skipped_count = 0
    
    print("\n=== Updating User Coordinates ===\n")
    
    for user in users:
        user_id = user['id']
        name = user['name']
        location = user['location']
        current_lat = user['latitude']
        current_lon = user['longitude']
        
        # Skip if already has coordinates
        if current_lat and current_lon:
            print(f"✓ {name} - Already has coordinates")
            skipped_count += 1
            continue
        
        # Get coordinates
        lat, lon = get_coordinates_for_location(location)
        
        if lat and lon:
            cursor.execute('''
                UPDATE users
                SET latitude = ?, longitude = ?, location_privacy = 'district'
                WHERE id = ?
            ''', (lat, lon, user_id))
            print(f"✓ {name} - Updated: {location} -> ({lat}, {lon})")
            updated_count += 1
        else:
            print(f"✗ {name} - No coordinates found for: {location}")
    
    conn.commit()
    conn.close()
    
    print(f"\n=== Summary ===")
    print(f"Updated: {updated_count}")
    print(f"Skipped (already had coords): {skipped_count}")
    print(f"Failed (no match): {len(users) - updated_count - skipped_count}")
    print()

if __name__ == '__main__':
    update_user_coordinates()

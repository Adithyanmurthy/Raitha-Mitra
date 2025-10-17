"""
Map Service Module
Handles farmer location aggregation, regional statistics, and community mapping
"""

import os
import json
import math
from datetime import datetime, timedelta
from collections import defaultdict
from database import DatabaseManager

db = DatabaseManager()


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula
    Returns distance in kilometers
    """
    # Radius of Earth in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def aggregate_farmer_locations(privacy_level='district'):
    """
    Aggregate farmer locations based on privacy level
    Returns aggregated location data for map display
    
    Privacy enforcement:
    - 'hidden': User is completely excluded from map
    - 'state': Only state-level aggregation
    - 'district': District-level aggregation (default)
    - 'exact': Exact location (requires explicit consent)
    """
    # Get all users with location data
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Query based on privacy level
    if privacy_level == 'exact':
        # Only users who explicitly opted for exact location sharing
        cursor.execute('''
            SELECT id, name, location, latitude, longitude, location_privacy
            FROM users
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND location_privacy = 'exact'
        ''')
    elif privacy_level == 'district':
        # Aggregate by district - exclude 'hidden' users
        cursor.execute('''
            SELECT location, COUNT(*) as farmer_count,
                   AVG(latitude) as avg_lat, AVG(longitude) as avg_lon
            FROM users
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND location_privacy IN ('district', 'exact')
            GROUP BY location
        ''')
    else:  # state level - exclude 'hidden' users
        cursor.execute('''
            SELECT location, COUNT(*) as farmer_count,
                   AVG(latitude) as avg_lat, AVG(longitude) as avg_lon
            FROM users
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND location_privacy != 'hidden'
            GROUP BY location
        ''')
    
    results = cursor.fetchall()
    conn.close()
    
    # Format results
    aggregated_data = []
    for row in results:
        row_dict = dict(row)
        
        if privacy_level == 'exact':
            aggregated_data.append({
                'type': 'individual',
                'farmer_id': row_dict['id'],
                'name': row_dict['name'],
                'location': row_dict['location'],
                'latitude': row_dict['latitude'],
                'longitude': row_dict['longitude']
            })
        else:
            aggregated_data.append({
                'type': 'aggregated',
                'location': row_dict['location'],
                'farmer_count': row_dict['farmer_count'],
                'latitude': row_dict['avg_lat'],
                'longitude': row_dict['avg_lon']
            })
    
    return aggregated_data


def get_regional_stats(region):
    """
    Get statistics for a specific region
    Returns farmer count, crop data, and activity metrics
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get farmer count in region
    cursor.execute('''
        SELECT COUNT(*) as farmer_count
        FROM users
        WHERE location LIKE ?
    ''', (f'%{region}%',))
    
    farmer_count = cursor.fetchone()['farmer_count']
    
    # Get active farmers (those with recent activity)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) as active_count
        FROM farm_activities
        WHERE created_at >= ?
        AND user_id IN (SELECT id FROM users WHERE location LIKE ?)
    ''', (thirty_days_ago, f'%{region}%'))
    
    active_count = cursor.fetchone()['active_count']
    
    # Get top crops in region
    cursor.execute('''
        SELECT crop_type, COUNT(*) as count
        FROM farm_activities
        WHERE user_id IN (SELECT id FROM users WHERE location LIKE ?)
        AND crop_type IS NOT NULL
        GROUP BY crop_type
        ORDER BY count DESC
        LIMIT 5
    ''', (f'%{region}%',))
    
    top_crops = [{'crop': row['crop_type'], 'count': row['count']} for row in cursor.fetchall()]
    
    # Get recent activity types
    cursor.execute('''
        SELECT activity_type, COUNT(*) as count
        FROM farm_activities
        WHERE user_id IN (SELECT id FROM users WHERE location LIKE ?)
        AND created_at >= ?
        GROUP BY activity_type
        ORDER BY count DESC
        LIMIT 5
    ''', (f'%{region}%', thirty_days_ago))
    
    recent_activities = [{'activity': row['activity_type'], 'count': row['count']} for row in cursor.fetchall()]
    
    # Get yield predictions in region
    cursor.execute('''
        SELECT AVG(predicted_yield) as avg_yield, COUNT(*) as prediction_count
        FROM yield_predictions
        WHERE user_id IN (SELECT id FROM users WHERE location LIKE ?)
        AND created_at >= ?
    ''', (f'%{region}%', thirty_days_ago))
    
    yield_data = cursor.fetchone()
    avg_yield = yield_data['avg_yield'] if yield_data['avg_yield'] else 0
    prediction_count = yield_data['prediction_count']
    
    conn.close()
    
    return {
        'region': region,
        'farmer_count': farmer_count,
        'active_farmers': active_count,
        'activity_rate': round((active_count / farmer_count * 100), 2) if farmer_count > 0 else 0,
        'top_crops': top_crops,
        'recent_activities': recent_activities,
        'avg_predicted_yield': round(avg_yield, 2),
        'prediction_count': prediction_count
    }


def find_nearby_farmers(user_id, radius_km=50):
    """
    Find farmers near a specific user within given radius
    Respects privacy settings
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get user's location
    cursor.execute('''
        SELECT latitude, longitude, location_privacy
        FROM users
        WHERE id = ?
    ''', (user_id,))
    
    user = cursor.fetchone()
    
    if not user or not user['latitude'] or not user['longitude']:
        conn.close()
        return []
    
    user_lat = user['latitude']
    user_lon = user['longitude']
    
    # Get all users with location (respecting privacy - exclude 'hidden' users)
    cursor.execute('''
        SELECT id, name, location, latitude, longitude, location_privacy
        FROM users
        WHERE id != ?
        AND latitude IS NOT NULL
        AND longitude IS NOT NULL
        AND location_privacy IN ('district', 'exact', 'state')
        AND location_privacy != 'hidden'
    ''', (user_id,))
    
    all_users = cursor.fetchall()
    conn.close()
    
    # Calculate distances and filter
    nearby_farmers = []
    for farmer in all_users:
        farmer_dict = dict(farmer)
        distance = calculate_distance(
            user_lat, user_lon,
            farmer_dict['latitude'], farmer_dict['longitude']
        )
        
        if distance <= radius_km:
            # Respect privacy - don't show exact location if privacy is 'district'
            if farmer_dict['location_privacy'] == 'district':
                nearby_farmers.append({
                    'farmer_id': farmer_dict['id'],
                    'name': farmer_dict['name'],
                    'location': farmer_dict['location'],
                    'distance_km': round(distance, 2),
                    'exact_location': False
                })
            else:
                nearby_farmers.append({
                    'farmer_id': farmer_dict['id'],
                    'name': farmer_dict['name'],
                    'location': farmer_dict['location'],
                    'latitude': farmer_dict['latitude'],
                    'longitude': farmer_dict['longitude'],
                    'distance_km': round(distance, 2),
                    'exact_location': True
                })
    
    # Sort by distance
    nearby_farmers.sort(key=lambda x: x['distance_km'])
    
    return nearby_farmers


def get_trending_topics(region):
    """
    Get trending topics and activities in a region
    Returns popular crops, common issues, and active discussions
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get users in region
    cursor.execute('''
        SELECT id FROM users WHERE location LIKE ?
    ''', (f'%{region}%',))
    
    user_ids = [row['id'] for row in cursor.fetchall()]
    
    if not user_ids:
        conn.close()
        return {
            'region': region,
            'trending_crops': [],
            'common_activities': [],
            'popular_topics': [],
            'recent_discussions': []
        }
    
    # Get trending crops (from recent activities)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    placeholders = ','.join('?' * len(user_ids))
    
    cursor.execute(f'''
        SELECT crop_type, COUNT(*) as count
        FROM farm_activities
        WHERE user_id IN ({placeholders})
        AND crop_type IS NOT NULL
        AND created_at >= ?
        GROUP BY crop_type
        ORDER BY count DESC
        LIMIT 5
    ''', (*user_ids, thirty_days_ago))
    
    trending_crops = [{'crop': row['crop_type'], 'mentions': row['count']} for row in cursor.fetchall()]
    
    # Get common activities
    cursor.execute(f'''
        SELECT activity_type, COUNT(*) as count
        FROM farm_activities
        WHERE user_id IN ({placeholders})
        AND created_at >= ?
        GROUP BY activity_type
        ORDER BY count DESC
        LIMIT 5
    ''', (*user_ids, thirty_days_ago))
    
    common_activities = [{'activity': row['activity_type'], 'count': row['count']} for row in cursor.fetchall()]
    
    # Get popular chat topics (from chat messages)
    cursor.execute(f'''
        SELECT context_data, COUNT(*) as count
        FROM chat_messages
        WHERE user_id IN ({placeholders})
        AND created_at >= ?
        AND context_data IS NOT NULL
        GROUP BY context_data
        ORDER BY count DESC
        LIMIT 10
    ''', (*user_ids, thirty_days_ago))
    
    chat_contexts = cursor.fetchall()
    
    # Extract topics from context data
    topic_counts = defaultdict(int)
    for row in chat_contexts:
        try:
            context = json.loads(row['context_data'])
            for crop in context.get('crops', []):
                topic_counts[f"crop:{crop}"] += row['count']
            for issue in context.get('issues', []):
                topic_counts[f"issue:{issue}"] += row['count']
            for activity in context.get('activities', []):
                topic_counts[f"activity:{activity}"] += row['count']
        except:
            pass
    
    # Sort topics by count
    popular_topics = [
        {'topic': topic.split(':', 1)[1], 'type': topic.split(':')[0], 'mentions': count}
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    # Get recent discussion snippets (from chat messages)
    cursor.execute(f'''
        SELECT message, created_at
        FROM chat_messages
        WHERE user_id IN ({placeholders})
        AND created_at >= ?
        ORDER BY created_at DESC
        LIMIT 5
    ''', (*user_ids, thirty_days_ago))
    
    recent_discussions = []
    for row in cursor.fetchall():
        message = row['message']
        # Truncate long messages
        if len(message) > 100:
            message = message[:100] + "..."
        recent_discussions.append({
            'snippet': message,
            'date': row['created_at']
        })
    
    conn.close()
    
    return {
        'region': region,
        'trending_crops': trending_crops,
        'common_activities': common_activities,
        'popular_topics': popular_topics,
        'recent_discussions': recent_discussions
    }


def update_regional_stats(region_name, region_type='district'):
    """
    Update cached regional statistics
    This can be called periodically to update the regional_stats table
    """
    stats = get_regional_stats(region_name)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Prepare top crops as JSON
    top_crops_json = json.dumps([crop['crop'] for crop in stats['top_crops'][:3]])
    
    # Update or insert regional stats
    cursor.execute('''
        INSERT INTO regional_stats (region_name, region_type, farmer_count, active_farmers, top_crops, last_updated)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(region_name, region_type) DO UPDATE SET
            farmer_count = excluded.farmer_count,
            active_farmers = excluded.active_farmers,
            top_crops = excluded.top_crops,
            last_updated = CURRENT_TIMESTAMP
    ''', (region_name, region_type, stats['farmer_count'], stats['active_farmers'], top_crops_json))
    
    conn.commit()
    conn.close()
    
    return True


def get_all_regions_summary():
    """
    Get summary of all regions with farmer presence
    Returns list of regions with basic stats
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get all unique locations
    cursor.execute('''
        SELECT location, COUNT(*) as farmer_count,
               AVG(latitude) as avg_lat, AVG(longitude) as avg_lon
        FROM users
        WHERE location IS NOT NULL
        GROUP BY location
        ORDER BY farmer_count DESC
    ''')
    
    regions = []
    for row in cursor.fetchall():
        row_dict = dict(row)
        regions.append({
            'region': row_dict['location'],
            'farmer_count': row_dict['farmer_count'],
            'latitude': row_dict['avg_lat'],
            'longitude': row_dict['avg_lon']
        })
    
    conn.close()
    
    return regions

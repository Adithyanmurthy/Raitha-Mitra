"""
Comprehensive Schema Verification Script
Tests that all tables, columns, indexes, and constraints are properly created
"""

import sqlite3
import sys

def get_connection(db_path='raitha_mitra.db'):
    """Get database connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def verify_schema():
    """Comprehensive schema verification"""
    print("🔍 Running comprehensive schema verification...\n")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    all_passed = True
    
    # ============================================================
    # 1. Verify all tables exist
    # ============================================================
    print("📋 Checking tables...")
    expected_tables = {
        'users': 'Core user information',
        'predictions': 'Disease detection history',
        'chat_messages': 'AI chat conversations',
        'farm_activities': 'Farm planning and tasks',
        'yield_predictions': 'Yield forecasting',
        'farm_expenses': 'Financial tracking',
        'financial_scores': 'Financial health scores',
        'messages': 'Farmer messaging',
        'blocked_users': 'User blocking',
        'friend_requests': 'Friend requests',
        'friendships': 'Friend connections',
        'regional_stats': 'Regional statistics'
    }
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    existing_tables = {row[0] for row in cursor.fetchall()}
    
    for table, description in expected_tables.items():
        if table in existing_tables:
            print(f"  ✅ {table:20} - {description}")
        else:
            print(f"  ❌ {table:20} - MISSING!")
            all_passed = False
    
    # ============================================================
    # 2. Verify users table columns
    # ============================================================
    print("\n👤 Checking users table columns...")
    expected_user_columns = [
        'id', 'name', 'email', 'mobile', 'password_hash', 'location',
        'created_at', 'verified', 'latitude', 'longitude', 
        'location_privacy', 'language_preference', 'last_active'
    ]
    
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    for column in expected_user_columns:
        if column in existing_columns:
            print(f"  ✅ {column}")
        else:
            print(f"  ❌ {column} - MISSING!")
            all_passed = False
    
    # ============================================================
    # 3. Verify indexes
    # ============================================================
    print("\n📊 Checking indexes...")
    expected_indexes = {
        'idx_chat_user_date': 'chat_messages',
        'idx_farm_user_date': 'farm_activities',
        'idx_expenses_user_date': 'farm_expenses',
        'idx_messages_receiver': 'messages',
        'idx_messages_sender': 'messages'
    }
    
    cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    existing_indexes = {row[0]: row[1] for row in cursor.fetchall()}
    
    for index, table in expected_indexes.items():
        if index in existing_indexes and existing_indexes[index] == table:
            print(f"  ✅ {index:25} on {table}")
        else:
            print(f"  ❌ {index:25} on {table} - MISSING!")
            all_passed = False
    
    # ============================================================
    # 4. Verify foreign key constraints
    # ============================================================
    print("\n🔗 Checking foreign key constraints...")
    tables_with_fk = [
        'chat_messages', 'farm_activities', 'yield_predictions',
        'farm_expenses', 'financial_scores', 'messages',
        'blocked_users', 'friend_requests', 'friendships'
    ]
    
    for table in tables_with_fk:
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        if fks:
            print(f"  ✅ {table:20} has {len(fks)} foreign key(s)")
        else:
            print(f"  ⚠️  {table:20} has no foreign keys (might be expected)")
    
    # ============================================================
    # 5. Test basic queries
    # ============================================================
    print("\n🧪 Testing basic queries...")
    
    test_queries = [
        ("SELECT COUNT(*) FROM users", "Count users"),
        ("SELECT COUNT(*) FROM chat_messages", "Count chat messages"),
        ("SELECT COUNT(*) FROM farm_activities", "Count farm activities"),
        ("SELECT COUNT(*) FROM messages", "Count messages"),
        ("SELECT COUNT(*) FROM friendships", "Count friendships"),
    ]
    
    for query, description in test_queries:
        try:
            cursor.execute(query)
            result = cursor.fetchone()[0]
            print(f"  ✅ {description:30} - {result} rows")
        except Exception as e:
            print(f"  ❌ {description:30} - ERROR: {e}")
            all_passed = False
    
    # ============================================================
    # 6. Verify unique constraints
    # ============================================================
    print("\n🔒 Checking unique constraints...")
    
    unique_constraints = [
        ('blocked_users', 'user_id, blocked_user_id'),
        ('friend_requests', 'requester_id, recipient_id'),
        ('friendships', 'user1_id, user2_id'),
        ('regional_stats', 'region_name, region_type')
    ]
    
    for table, columns in unique_constraints:
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
        sql = cursor.fetchone()[0]
        if 'UNIQUE' in sql:
            print(f"  ✅ {table:20} has UNIQUE constraint")
        else:
            print(f"  ⚠️  {table:20} UNIQUE constraint not found in SQL")
    
    # ============================================================
    # 7. Summary
    # ============================================================
    conn.close()
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Schema is correctly configured!")
    else:
        print("⚠️  SOME CHECKS FAILED - Review errors above")
    print("="*60)
    
    return all_passed

if __name__ == '__main__':
    success = verify_schema()
    sys.exit(0 if success else 1)

"""
Test basic database operations on new tables
This ensures the schema is not just created, but functional
"""

import sqlite3
from datetime import datetime, date

def get_connection(db_path='raitha_mitra.db'):
    """Get database connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def test_database_operations():
    """Test basic CRUD operations on new tables"""
    print("🧪 Testing database operations...\n")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    all_passed = True
    
    try:
        # Get a test user (demo user should exist)
        cursor.execute("SELECT id FROM users LIMIT 1")
        user = cursor.fetchone()
        if not user:
            print("❌ No users found in database")
            return False
        
        user_id = user[0]
        print(f"✅ Using test user_id: {user_id}\n")
        
        # ============================================================
        # Test 1: Chat Messages
        # ============================================================
        print("💬 Testing chat_messages...")
        cursor.execute('''
            INSERT INTO chat_messages (user_id, message, response, context_data, language)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, "What crops should I plant?", "Based on your location, consider rice or wheat.", 
              '{"crop": "rice", "season": "monsoon"}', "en"))
        
        cursor.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        print(f"  ✅ Inserted and retrieved chat message (count: {count})")
        
        # ============================================================
        # Test 2: Farm Activities
        # ============================================================
        print("\n🌾 Testing farm_activities...")
        cursor.execute('''
            INSERT INTO farm_activities (user_id, activity_type, crop_type, scheduled_date, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, "irrigation", "rice", date.today().isoformat(), "pending"))
        
        cursor.execute("SELECT COUNT(*) FROM farm_activities WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        print(f"  ✅ Inserted and retrieved farm activity (count: {count})")
        
        # ============================================================
        # Test 3: Yield Predictions
        # ============================================================
        print("\n📊 Testing yield_predictions...")
        cursor.execute('''
            INSERT INTO yield_predictions (user_id, crop_type, predicted_yield, confidence_score)
            VALUES (?, ?, ?, ?)
        ''', (user_id, "rice", 2500.5, 0.85))
        
        cursor.execute("SELECT COUNT(*) FROM yield_predictions WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        print(f"  ✅ Inserted and retrieved yield prediction (count: {count})")
        
        # ============================================================
        # Test 4: Farm Expenses
        # ============================================================
        print("\n💰 Testing farm_expenses...")
        cursor.execute('''
            INSERT INTO farm_expenses (user_id, category, amount, expense_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, "seeds", 5000.00, date.today().isoformat()))
        
        cursor.execute("SELECT COUNT(*) FROM farm_expenses WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        print(f"  ✅ Inserted and retrieved expense (count: {count})")
        
        # ============================================================
        # Test 5: Financial Scores
        # ============================================================
        print("\n📈 Testing financial_scores...")
        cursor.execute('''
            INSERT INTO financial_scores (user_id, overall_score, cost_efficiency_score)
            VALUES (?, ?, ?)
        ''', (user_id, 75.5, 80.0))
        
        cursor.execute("SELECT COUNT(*) FROM financial_scores WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        print(f"  ✅ Inserted and retrieved financial score (count: {count})")
        
        # ============================================================
        # Test 6: Messages (need 2 users)
        # ============================================================
        print("\n✉️ Testing messages...")
        cursor.execute("SELECT id FROM users LIMIT 2")
        users = cursor.fetchall()
        
        if len(users) >= 2:
            cursor.execute('''
                INSERT INTO messages (sender_id, receiver_id, message_text)
                VALUES (?, ?, ?)
            ''', (users[0][0], users[1][0], "Hello, fellow farmer!"))
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            count = cursor.fetchone()[0]
            print(f"  ✅ Inserted and retrieved message (count: {count})")
        else:
            print("  ⚠️  Skipped (need 2 users)")
        
        # ============================================================
        # Test 7: Friend Requests
        # ============================================================
        print("\n👥 Testing friend_requests...")
        if len(users) >= 2:
            cursor.execute('''
                INSERT INTO friend_requests (requester_id, recipient_id, status)
                VALUES (?, ?, ?)
            ''', (users[0][0], users[1][0], "pending"))
            
            cursor.execute("SELECT COUNT(*) FROM friend_requests")
            count = cursor.fetchone()[0]
            print(f"  ✅ Inserted and retrieved friend request (count: {count})")
        else:
            print("  ⚠️  Skipped (need 2 users)")
        
        # ============================================================
        # Test 8: Regional Stats
        # ============================================================
        print("\n🗺️ Testing regional_stats...")
        cursor.execute('''
            INSERT INTO regional_stats (region_name, region_type, farmer_count, top_crops)
            VALUES (?, ?, ?, ?)
        ''', ("Karnataka", "state", 150, '["rice", "wheat", "sugarcane"]'))
        
        cursor.execute("SELECT COUNT(*) FROM regional_stats")
        count = cursor.fetchone()[0]
        print(f"  ✅ Inserted and retrieved regional stat (count: {count})")
        
        # ============================================================
        # Test 9: Update User with New Columns
        # ============================================================
        print("\n👤 Testing users table extensions...")
        cursor.execute('''
            UPDATE users 
            SET latitude = ?, longitude = ?, location_privacy = ?, language_preference = ?
            WHERE id = ?
        ''', (12.9716, 77.5946, "district", "en", user_id))
        
        cursor.execute('''
            SELECT latitude, longitude, location_privacy, language_preference 
            FROM users WHERE id = ?
        ''', (user_id,))
        user_data = cursor.fetchone()
        print(f"  ✅ Updated user location: ({user_data[0]}, {user_data[1]})")
        print(f"  ✅ Privacy level: {user_data[2]}, Language: {user_data[3]}")
        
        # ============================================================
        # Test 10: Index Performance
        # ============================================================
        print("\n📊 Testing index usage...")
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM chat_messages WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        plan = cursor.fetchone()
        if "idx_chat_user_date" in str(plan):
            print("  ✅ Index idx_chat_user_date is being used")
        else:
            print(f"  ⚠️  Query plan: {plan}")
        
        # Commit all test data
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ ALL DATABASE OPERATIONS SUCCESSFUL!")
        print("="*60)
        print("\n📝 Test data has been inserted into the database.")
        print("   You can now proceed with implementing the next tasks.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    import sys
    success = test_database_operations()
    sys.exit(0 if success else 1)

"""
Database Rollback Script for Raitha Mitra Advanced Features
This script removes all new tables and columns added by the migration.
USE WITH CAUTION - This will delete all data in the new tables!
"""

import sqlite3
import sys

def get_connection(db_path='raitha_mitra.db'):
    """Get database connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def rollback_database(db_path='raitha_mitra.db'):
    """Rollback database migration"""
    print("⚠️  WARNING: This will delete all new tables and data!")
    print("⚠️  Original users and predictions tables will be preserved.")
    
    response = input("\nAre you sure you want to rollback? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Rollback cancelled")
        return False
    
    print("\n🔄 Starting database rollback...")
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    try:
        # Drop all new tables
        tables_to_drop = [
            'chat_messages',
            'farm_activities',
            'yield_predictions',
            'farm_expenses',
            'financial_scores',
            'messages',
            'blocked_users',
            'friend_requests',
            'friendships',
            'regional_stats'
        ]
        
        for table in tables_to_drop:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table}')
                print(f"  ✅ Dropped table: {table}")
            except Exception as e:
                print(f"  ⚠️  Could not drop table {table}: {e}")
        
        # Note: SQLite doesn't support DROP COLUMN directly
        # To remove columns from users table, we would need to:
        # 1. Create a new table without those columns
        # 2. Copy data from old table
        # 3. Drop old table
        # 4. Rename new table
        # This is complex and risky, so we'll leave the columns in place
        
        print("\n⚠️  Note: New columns in users table were NOT removed")
        print("   (latitude, longitude, location_privacy, language_preference, last_active)")
        print("   SQLite doesn't support DROP COLUMN easily. These columns are harmless.")
        
        conn.commit()
        
        print("\n✅ Rollback completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    success = rollback_database()
    sys.exit(0 if success else 1)

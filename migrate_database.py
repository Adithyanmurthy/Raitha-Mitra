"""
Database Migration Script for Raitha Mitra Advanced Features
This script adds new tables and columns for:
- Smart FAQ Chatbot with Context Memory
- Smart Decision Intelligence Layer
- Farmer Community and Interactive Map Network
"""

import sqlite3
import sys
from datetime import datetime

def get_connection(db_path='raitha_mitra.db'):
    """Get database connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate_database(db_path='raitha_mitra.db'):
    """Run database migration"""
    print("🚀 Starting database migration...")
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    try:
        # ============================================================
        # 1. EXTEND USERS TABLE
        # ============================================================
        print("\n📝 Extending users table...")
        
        # Add location columns
        if not check_column_exists(cursor, 'users', 'latitude'):
            cursor.execute('ALTER TABLE users ADD COLUMN latitude REAL')
            print("  ✅ Added latitude column")
        
        if not check_column_exists(cursor, 'users', 'longitude'):
            cursor.execute('ALTER TABLE users ADD COLUMN longitude REAL')
            print("  ✅ Added longitude column")
        
        if not check_column_exists(cursor, 'users', 'location_privacy'):
            cursor.execute("ALTER TABLE users ADD COLUMN location_privacy TEXT DEFAULT 'district'")
            print("  ✅ Added location_privacy column")
        
        if not check_column_exists(cursor, 'users', 'language_preference'):
            cursor.execute("ALTER TABLE users ADD COLUMN language_preference TEXT DEFAULT 'en'")
            print("  ✅ Added language_preference column")
        
        if not check_column_exists(cursor, 'users', 'last_active'):
            cursor.execute('ALTER TABLE users ADD COLUMN last_active TIMESTAMP')
            print("  ✅ Added last_active column")
        
        # ============================================================
        # 2. CHAT MESSAGES TABLE
        # ============================================================
        print("\n💬 Creating chat_messages table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                context_data TEXT,
                language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("  ✅ chat_messages table created")
        
        # Create index for chat messages
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_user_date 
            ON chat_messages(user_id, created_at DESC)
        ''')
        print("  ✅ Index idx_chat_user_date created")
        
        # ============================================================
        # 3. FARM ACTIVITIES TABLE
        # ============================================================
        print("\n🌾 Creating farm_activities table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS farm_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                crop_type TEXT,
                description TEXT,
                scheduled_date DATE NOT NULL,
                completed_date DATE,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                ai_generated BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("  ✅ farm_activities table created")
        
        # Create index for farm activities
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_farm_user_date 
            ON farm_activities(user_id, scheduled_date)
        ''')
        print("  ✅ Index idx_farm_user_date created")
        
        # ============================================================
        # 4. YIELD PREDICTIONS TABLE
        # ============================================================
        print("\n📊 Creating yield_predictions table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS yield_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planting_date DATE,
                predicted_yield REAL,
                predicted_quality TEXT,
                confidence_score REAL,
                harvest_date DATE,
                actual_yield REAL,
                actual_quality TEXT,
                factors_considered TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("  ✅ yield_predictions table created")
        
        # ============================================================
        # 5. FARM EXPENSES TABLE
        # ============================================================
        print("\n💰 Creating farm_expenses table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS farm_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                expense_date DATE NOT NULL,
                crop_related TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("  ✅ farm_expenses table created")
        
        # Create index for expenses
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_expenses_user_date 
            ON farm_expenses(user_id, expense_date)
        ''')
        print("  ✅ Index idx_expenses_user_date created")
        
        # ============================================================
        # 6. FINANCIAL SCORES TABLE
        # ============================================================
        print("\n📈 Creating financial_scores table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                overall_score REAL NOT NULL,
                cost_efficiency_score REAL,
                yield_performance_score REAL,
                market_timing_score REAL,
                score_breakdown TEXT,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("  ✅ financial_scores table created")
        
        # ============================================================
        # 7. MESSAGES TABLE
        # ============================================================
        print("\n✉️ Creating messages table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
        ''')
        print("  ✅ messages table created")
        
        # Create indexes for messages
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_receiver 
            ON messages(receiver_id, created_at DESC)
        ''')
        print("  ✅ Index idx_messages_receiver created")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_sender 
            ON messages(sender_id, created_at DESC)
        ''')
        print("  ✅ Index idx_messages_sender created")
        
        # ============================================================
        # 8. BLOCKED USERS TABLE
        # ============================================================
        print("\n🚫 Creating blocked_users table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocked_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                blocked_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (blocked_user_id) REFERENCES users(id),
                UNIQUE(user_id, blocked_user_id)
            )
        ''')
        print("  ✅ blocked_users table created")
        
        # ============================================================
        # 9. FRIEND REQUESTS TABLE
        # ============================================================
        print("\n👥 Creating friend_requests table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friend_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                responded_at TIMESTAMP,
                FOREIGN KEY (requester_id) REFERENCES users(id),
                FOREIGN KEY (recipient_id) REFERENCES users(id),
                UNIQUE(requester_id, recipient_id)
            )
        ''')
        print("  ✅ friend_requests table created")
        
        # ============================================================
        # 10. FRIENDSHIPS TABLE
        # ============================================================
        print("\n🤝 Creating friendships table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users(id),
                FOREIGN KEY (user2_id) REFERENCES users(id),
                UNIQUE(user1_id, user2_id)
            )
        ''')
        print("  ✅ friendships table created")
        
        # ============================================================
        # 11. REGIONAL STATS TABLE
        # ============================================================
        print("\n🗺️ Creating regional_stats table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regional_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region_name TEXT NOT NULL,
                region_type TEXT NOT NULL,
                farmer_count INTEGER DEFAULT 0,
                active_farmers INTEGER DEFAULT 0,
                top_crops TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(region_name, region_type)
            )
        ''')
        print("  ✅ regional_stats table created")
        
        # Commit all changes
        conn.commit()
        
        print("\n✅ Database migration completed successfully!")
        print("\n📋 Summary:")
        print("  - Extended users table with location and preference columns")
        print("  - Created chat_messages table with index")
        print("  - Created farm_activities table with index")
        print("  - Created yield_predictions table")
        print("  - Created farm_expenses table with index")
        print("  - Created financial_scores table")
        print("  - Created messages table with indexes")
        print("  - Created blocked_users table")
        print("  - Created friend_requests table")
        print("  - Created friendships table")
        print("  - Created regional_stats table")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verify_migration(db_path='raitha_mitra.db'):
    """Verify that all tables and columns exist"""
    print("\n🔍 Verifying migration...")
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Check all new tables
    expected_tables = [
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
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    all_exist = True
    for table in expected_tables:
        if table in existing_tables:
            print(f"  ✅ Table '{table}' exists")
        else:
            print(f"  ❌ Table '{table}' missing")
            all_exist = False
    
    # Check new columns in users table
    expected_columns = ['latitude', 'longitude', 'location_privacy', 'language_preference', 'last_active']
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    for column in expected_columns:
        if column in existing_columns:
            print(f"  ✅ Column 'users.{column}' exists")
        else:
            print(f"  ❌ Column 'users.{column}' missing")
            all_exist = False
    
    conn.close()
    
    if all_exist:
        print("\n✅ All tables and columns verified successfully!")
    else:
        print("\n⚠️ Some tables or columns are missing")
    
    return all_exist

if __name__ == '__main__':
    # Run migration
    success = migrate_database()
    
    if success:
        # Verify migration
        verify_migration()
        sys.exit(0)
    else:
        sys.exit(1)

import sqlite3
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class DatabaseManager:
    def __init__(self, db_path='raitha_mitra.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                mobile TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                image_path TEXT,
                disease_name TEXT NOT NULL,
                confidence REAL,
                yield_impact TEXT,
                symptoms TEXT,
                organic_treatment TEXT,
                chemical_treatment TEXT,
                prevention_tips TEXT,
                market_prices TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        

        
        conn.commit()
        conn.close()
        
        # Create demo user
        self.create_demo_user()
    
    def create_demo_user(self):
        """Create a demo user for testing"""
        try:
            demo_user = {
                'name': 'Demo User',
                'email': 'demo@raithamitra.com',
                'mobile': '9876543210',
                'password': '123456',
                'location': 'Bengaluru, Karnataka'
            }
            self.create_user(**demo_user)
            print("✅ Demo user created: demo@raithamitra.com / 9876543210 / 123456")
        except Exception as e:
            # User might already exist
            pass
    
    def create_user(self, name, email, mobile, password, location):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        
        cursor.execute('''
            INSERT INTO users (name, email, mobile, password_hash, location, verified)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, mobile, password_hash, location, True))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return user_id
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def get_user_by_email_or_mobile(self, email_or_mobile):
        """Get user by email or mobile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM users 
            WHERE email = ? OR mobile = ?
        ''', (email_or_mobile, email_or_mobile))
        
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def verify_password(self, user, password):
        """Verify user password"""
        if user['password_hash'].startswith(('pbkdf2:', 'scrypt:', 'argon2:')):
            return check_password_hash(user['password_hash'], password)
        else:
            # Fallback for plain text passwords (demo mode)
            return user['password_hash'] == password
    
    def update_user_password(self, email, new_password_hash):
        """Update user password"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            print(f"🔄 Updating password for email: {email}")
            
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?
                WHERE email = ?
            ''', (new_password_hash, email))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            print(f"✅ Password update success: {success}, rows affected: {cursor.rowcount}")
            return success
        except Exception as e:
            print(f"❌ Error updating password: {e}")
            return False
    

    
    def save_prediction(self, user_id, disease_name, confidence, yield_impact, 
                       symptoms, organic_treatment, chemical_treatment, 
                       prevention_tips, market_prices, image_path=None):
        """Save prediction result"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO predictions (
                user_id, image_path, disease_name, confidence, yield_impact,
                symptoms, organic_treatment, chemical_treatment, 
                prevention_tips, market_prices
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, image_path, disease_name, confidence, yield_impact,
              symptoms, organic_treatment, chemical_treatment, 
              prevention_tips, market_prices))
        
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return prediction_id
    
    def get_user_predictions(self, user_id, limit=10):
        """Get user's prediction history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM predictions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        predictions = cursor.fetchall()
        conn.close()
        
        return [dict(pred) for pred in predictions]
    
    def get_all_predictions(self, limit=50):
        """Get all predictions for analytics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, u.name as user_name, u.email as user_email
            FROM predictions p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            LIMIT ?
        ''', (limit,))
        
        predictions = cursor.fetchall()
        conn.close()
        
        return [dict(pred) for pred in predictions]
    
    # Chat message storage and retrieval methods
    def save_chat_message(self, user_id, message, response, context_data=None, language='en'):
        """Save chat message and AI response"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        context_json = json.dumps(context_data) if context_data else None
        
        cursor.execute('''
            INSERT INTO chat_messages (user_id, message, response, context_data, language)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, message, response, context_json, language))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_chat_history(self, user_id, limit=50):
        """Get chat history for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM chat_messages
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        messages = cursor.fetchall()
        conn.close()
        
        result = []
        for msg in messages:
            msg_dict = dict(msg)
            if msg_dict.get('context_data'):
                try:
                    msg_dict['context_data'] = json.loads(msg_dict['context_data'])
                except:
                    msg_dict['context_data'] = None
            result.append(msg_dict)
        
        return list(reversed(result))  # Return in chronological order
    
    def clear_chat_history(self, user_id):
        """Clear all chat history for a user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM chat_messages
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error clearing chat history: {e}")
            return False
    
    def get_recent_context(self, user_id, limit=10):
        """Get recent chat context for building AI prompts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message, response, context_data, created_at
            FROM chat_messages
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        messages = cursor.fetchall()
        conn.close()
        
        result = []
        for msg in messages:
            msg_dict = dict(msg)
            if msg_dict.get('context_data'):
                try:
                    msg_dict['context_data'] = json.loads(msg_dict['context_data'])
                except:
                    msg_dict['context_data'] = None
            result.append(msg_dict)
        
        return list(reversed(result))  # Return in chronological order
    
    # Farm activity management methods
    def save_farm_activity(self, user_id, activity_type, crop_type, scheduled_date, description=None, ai_generated=False):
        """Save farm activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO farm_activities (user_id, activity_type, crop_type, scheduled_date, description, ai_generated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, activity_type, crop_type, scheduled_date, description, ai_generated))
        
        activity_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return activity_id
    
    def get_farm_schedule(self, user_id, start_date=None, end_date=None):
        """Get farm schedule for a date range"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute('''
                SELECT * FROM farm_activities
                WHERE user_id = ? AND scheduled_date BETWEEN ? AND ?
                ORDER BY scheduled_date ASC
            ''', (user_id, start_date, end_date))
        else:
            cursor.execute('''
                SELECT * FROM farm_activities
                WHERE user_id = ?
                ORDER BY scheduled_date ASC
            ''', (user_id,))
        
        activities = cursor.fetchall()
        conn.close()
        
        return [dict(activity) for activity in activities]
    
    def update_activity_status(self, activity_id, status, completed_date=None, notes=None):
        """Update activity status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE farm_activities
            SET status = ?, completed_date = ?, notes = ?
            WHERE id = ?
        ''', (status, completed_date, notes, activity_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_activity_history(self, user_id, limit=50):
        """Get activity history for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM farm_activities
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        activities = cursor.fetchall()
        conn.close()
        
        return [dict(activity) for activity in activities]
    

    # Yield prediction storage methods
    def save_yield_prediction(self, user_id, crop_type, planting_date, predicted_yield, confidence_score, predicted_quality=None, harvest_date=None, factors_considered=None):
        """Save yield prediction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        factors_json = json.dumps(factors_considered) if factors_considered else None
        
        cursor.execute('''
            INSERT INTO yield_predictions (user_id, crop_type, planting_date, predicted_yield, confidence_score, predicted_quality, harvest_date, factors_considered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, crop_type, planting_date, predicted_yield, confidence_score, predicted_quality, harvest_date, factors_json))
        
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return prediction_id
    
    def get_yield_predictions(self, user_id):
        """Get all yield predictions for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM yield_predictions
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        predictions = cursor.fetchall()
        conn.close()
        
        result = []
        for pred in predictions:
            pred_dict = dict(pred)
            if pred_dict.get('factors_considered'):
                try:
                    pred_dict['factors_considered'] = json.loads(pred_dict['factors_considered'])
                except:
                    pred_dict['factors_considered'] = None
            result.append(pred_dict)
        
        return result
    
    def update_actual_yield(self, prediction_id, actual_yield, actual_quality=None):
        """Update actual yield after harvest"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE yield_predictions
            SET actual_yield = ?, actual_quality = ?
            WHERE id = ?
        ''', (actual_yield, actual_quality, prediction_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success

    # Financial tracking methods
    def save_expense(self, user_id, category, amount, expense_date, description=None, crop_related=None):
        """Save farm expense"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO farm_expenses (user_id, category, amount, expense_date, description, crop_related)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, category, amount, expense_date, description, crop_related))
        
        expense_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return expense_id
    
    def get_expenses(self, user_id, start_date=None, end_date=None):
        """Get expenses for a date range"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute('''
                SELECT * FROM farm_expenses
                WHERE user_id = ? AND expense_date BETWEEN ? AND ?
                ORDER BY expense_date DESC
            ''', (user_id, start_date, end_date))
        else:
            cursor.execute('''
                SELECT * FROM farm_expenses
                WHERE user_id = ?
                ORDER BY expense_date DESC
            ''', (user_id,))
        
        expenses = cursor.fetchall()
        conn.close()
        
        return [dict(expense) for expense in expenses]
    
    def save_financial_score(self, user_id, overall_score, score_breakdown):
        """Save financial health score"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        breakdown_json = json.dumps(score_breakdown) if score_breakdown else None
        
        # Extract individual scores from breakdown if available
        cost_efficiency = score_breakdown.get('cost_efficiency_score') if isinstance(score_breakdown, dict) else None
        yield_performance = score_breakdown.get('yield_performance_score') if isinstance(score_breakdown, dict) else None
        market_timing = score_breakdown.get('market_timing_score') if isinstance(score_breakdown, dict) else None
        
        cursor.execute('''
            INSERT INTO financial_scores (user_id, overall_score, cost_efficiency_score, yield_performance_score, market_timing_score, score_breakdown)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, overall_score, cost_efficiency, yield_performance, market_timing, breakdown_json))
        
        score_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return score_id
    
    def get_latest_financial_score(self, user_id):
        """Get latest financial health score for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM financial_scores
            WHERE user_id = ?
            ORDER BY calculated_at DESC
            LIMIT 1
        ''', (user_id,))
        
        score = cursor.fetchone()
        conn.close()
        
        if score:
            score_dict = dict(score)
            if score_dict.get('score_breakdown'):
                try:
                    score_dict['score_breakdown'] = json.loads(score_dict['score_breakdown'])
                except:
                    score_dict['score_breakdown'] = None
            return score_dict
        
        return None

    # Messaging system methods
    def send_message(self, sender_id, receiver_id, message_text):
        """Send a message to another user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if sender has blocked receiver or vice versa
        if self.is_blocked(sender_id, receiver_id) or self.is_blocked(receiver_id, sender_id):
            conn.close()
            return None
        
        cursor.execute('''
            INSERT INTO messages (sender_id, receiver_id, message_text)
            VALUES (?, ?, ?)
        ''', (sender_id, receiver_id, message_text))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_inbox(self, user_id, limit=50):
        """Get user's inbox with latest message from each conversation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.*, 
                   u.name as sender_name, 
                   u.email as sender_email,
                   (SELECT COUNT(*) FROM messages 
                    WHERE receiver_id = ? AND sender_id = m.sender_id AND is_read = 0) as unread_count
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.id IN (
                SELECT MAX(id) FROM messages
                WHERE receiver_id = ? OR sender_id = ?
                GROUP BY CASE 
                    WHEN sender_id = ? THEN receiver_id 
                    ELSE sender_id 
                END
            )
            ORDER BY m.created_at DESC
            LIMIT ?
        ''', (user_id, user_id, user_id, user_id, limit))
        
        messages = cursor.fetchall()
        conn.close()
        
        return [dict(msg) for msg in messages]
    
    def get_conversation(self, user_id, other_user_id):
        """Get conversation between two users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.*, 
                   sender.name as sender_name,
                   receiver.name as receiver_name
            FROM messages m
            JOIN users sender ON m.sender_id = sender.id
            JOIN users receiver ON m.receiver_id = receiver.id
            WHERE (m.sender_id = ? AND m.receiver_id = ?)
               OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.created_at ASC
        ''', (user_id, other_user_id, other_user_id, user_id))
        
        messages = cursor.fetchall()
        conn.close()
        
        return [dict(msg) for msg in messages]
    
    def mark_message_read(self, message_id):
        """Mark a message as read"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE messages
            SET is_read = 1
            WHERE id = ?
        ''', (message_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def block_user(self, user_id, blocked_user_id):
        """Block a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO blocked_users (user_id, blocked_user_id)
                VALUES (?, ?)
            ''', (user_id, blocked_user_id))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Already blocked
            conn.close()
            return False
    
    def is_blocked(self, user_id, other_user_id):
        """Check if a user is blocked"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM blocked_users
            WHERE user_id = ? AND blocked_user_id = ?
        ''', (user_id, other_user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] > 0

    # Friend network methods
    def send_friend_request(self, requester_id, recipient_id):
        """Send a friend request"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if already friends
        if self.are_friends(requester_id, recipient_id):
            conn.close()
            return None
        
        try:
            cursor.execute('''
                INSERT INTO friend_requests (requester_id, recipient_id)
                VALUES (?, ?)
            ''', (requester_id, recipient_id))
            
            request_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return request_id
        except sqlite3.IntegrityError:
            # Request already exists
            conn.close()
            return None
    
    def accept_friend_request(self, request_id):
        """Accept a friend request"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get request details
        cursor.execute('''
            SELECT requester_id, recipient_id FROM friend_requests
            WHERE id = ? AND status = 'pending'
        ''', (request_id,))
        
        request = cursor.fetchone()
        
        if not request:
            conn.close()
            return False
        
        requester_id = request['requester_id']
        recipient_id = request['recipient_id']
        
        # Update request status
        cursor.execute('''
            UPDATE friend_requests
            SET status = 'accepted', responded_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (request_id,))
        
        # Create friendship (ensure user1_id < user2_id for consistency)
        user1_id = min(requester_id, recipient_id)
        user2_id = max(requester_id, recipient_id)
        
        try:
            cursor.execute('''
                INSERT INTO friendships (user1_id, user2_id)
                VALUES (?, ?)
            ''', (user1_id, user2_id))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Friendship already exists
            conn.commit()
            conn.close()
            return True
    
    def decline_friend_request(self, request_id):
        """Decline a friend request"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE friend_requests
            SET status = 'declined', responded_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'pending'
        ''', (request_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_friends(self, user_id):
        """Get user's friends list"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.name, u.email, u.location, f.created_at as friends_since
            FROM friendships f
            JOIN users u ON (
                CASE 
                    WHEN f.user1_id = ? THEN f.user2_id
                    ELSE f.user1_id
                END = u.id
            )
            WHERE f.user1_id = ? OR f.user2_id = ?
            ORDER BY f.created_at DESC
        ''', (user_id, user_id, user_id))
        
        friends = cursor.fetchall()
        conn.close()
        
        return [dict(friend) for friend in friends]
    
    def get_friend_requests(self, user_id):
        """Get pending friend requests for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fr.*, u.name as requester_name, u.email as requester_email, u.location as requester_location
            FROM friend_requests fr
            JOIN users u ON fr.requester_id = u.id
            WHERE fr.recipient_id = ? AND fr.status = 'pending'
            ORDER BY fr.created_at DESC
        ''', (user_id,))
        
        requests = cursor.fetchall()
        conn.close()
        
        return [dict(req) for req in requests]
    
    def remove_friend(self, user_id, friend_id):
        """Remove a friend"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        user1_id = min(user_id, friend_id)
        user2_id = max(user_id, friend_id)
        
        cursor.execute('''
            DELETE FROM friendships
            WHERE user1_id = ? AND user2_id = ?
        ''', (user1_id, user2_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def are_friends(self, user_id, other_user_id):
        """Check if two users are friends"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        user1_id = min(user_id, other_user_id)
        user2_id = max(user_id, other_user_id)
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM friendships
            WHERE user1_id = ? AND user2_id = ?
        ''', (user1_id, user2_id))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] > 0

    # Map and location methods
    def update_user_location(self, user_id, latitude, longitude, privacy_level='district'):
        """Update user's location and privacy settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET latitude = ?, longitude = ?, location_privacy = ?
            WHERE id = ?
        ''', (latitude, longitude, privacy_level, user_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_regional_farmers(self, region_name, region_type='district'):
        """Get farmers in a specific region"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # This is a simplified version - in production, you'd use proper geocoding
        cursor.execute('''
            SELECT u.id, u.name, u.email, u.location, u.latitude, u.longitude
            FROM users u
            WHERE u.location LIKE ? AND u.location_privacy IN ('district', 'state', 'exact')
            ORDER BY u.created_at DESC
        ''', (f'%{region_name}%',))
        
        farmers = cursor.fetchall()
        conn.close()
        
        return [dict(farmer) for farmer in farmers]
    
    def get_nearby_farmers(self, user_id, radius_km=50):
        """Get nearby farmers within a radius (simplified version)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get user's location
        cursor.execute('''
            SELECT latitude, longitude FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        
        if not user or not user['latitude'] or not user['longitude']:
            conn.close()
            return []
        
        user_lat = user['latitude']
        user_lon = user['longitude']
        
        # Simplified distance calculation using Haversine formula
        # Note: This is a basic implementation. For production, consider using PostGIS or similar
        cursor.execute('''
            SELECT u.id, u.name, u.email, u.location, u.latitude, u.longitude,
                   (6371 * acos(
                       cos(radians(?)) * cos(radians(u.latitude)) *
                       cos(radians(u.longitude) - radians(?)) +
                       sin(radians(?)) * sin(radians(u.latitude))
                   )) AS distance_km
            FROM users u
            WHERE u.id != ? 
              AND u.latitude IS NOT NULL 
              AND u.longitude IS NOT NULL
              AND u.location_privacy IN ('district', 'exact')
            HAVING distance_km <= ?
            ORDER BY distance_km ASC
        ''', (user_lat, user_lon, user_lat, user_id, radius_km))
        
        farmers = cursor.fetchall()
        conn.close()
        
        return [dict(farmer) for farmer in farmers]
    
    def update_regional_stats(self, region_name, region_type='district'):
        """Update regional statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Count farmers in region
        cursor.execute('''
            SELECT COUNT(*) as farmer_count
            FROM users
            WHERE location LIKE ?
        ''', (f'%{region_name}%',))
        
        result = cursor.fetchone()
        farmer_count = result['farmer_count'] if result else 0
        
        # Count active farmers (those with recent activity)
        cursor.execute('''
            SELECT COUNT(DISTINCT u.id) as active_count
            FROM users u
            LEFT JOIN predictions p ON u.id = p.user_id
            WHERE u.location LIKE ?
              AND p.created_at >= datetime('now', '-30 days')
        ''', (f'%{region_name}%',))
        
        result = cursor.fetchone()
        active_count = result['active_count'] if result else 0
        
        # Get top crops (from predictions)
        cursor.execute('''
            SELECT disease_name, COUNT(*) as count
            FROM predictions p
            JOIN users u ON p.user_id = u.id
            WHERE u.location LIKE ?
            GROUP BY disease_name
            ORDER BY count DESC
            LIMIT 5
        ''', (f'%{region_name}%',))
        
        crops = cursor.fetchall()
        top_crops = json.dumps([crop['disease_name'] for crop in crops]) if crops else '[]'
        
        # Insert or update regional stats
        cursor.execute('''
            INSERT INTO regional_stats (region_name, region_type, farmer_count, active_farmers, top_crops, last_updated)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(region_name, region_type) 
            DO UPDATE SET 
                farmer_count = excluded.farmer_count,
                active_farmers = excluded.active_farmers,
                top_crops = excluded.top_crops,
                last_updated = CURRENT_TIMESTAMP
        ''', (region_name, region_type, farmer_count, active_count, top_crops))
        
        conn.commit()
        conn.close()
        
        return True

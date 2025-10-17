#!/usr/bin/env python3
"""
Test script for new DatabaseManager methods
"""
import os
import sys
from datetime import datetime, timedelta
from database import DatabaseManager

def ensure_test_user(db):
    """Ensure test user exists"""
    try:
        user = db.get_user_by_email('test@example.com')
        if not user:
            db.create_user(
                name='Test User',
                email='test@example.com',
                mobile='1234567890',
                password='test123',
                location='Test Location'
            )
            return 1
        return user['id']
    except:
        return 1

def test_chat_methods():
    """Test chat message methods"""
    print("\n=== Testing Chat Methods ===")
    db = DatabaseManager('raitha_mitra.db')
    user_id = ensure_test_user(db)
    
    # Save chat message
    msg_id = db.save_chat_message(
        user_id=user_id,
        message="What fertilizer should I use for tomatoes?",
        response="For tomatoes, use NPK 19:19:19 during vegetative stage...",
        context_data={"crop": "tomato", "issue": "fertilizer"},
        language="en"
    )
    print(f"✓ Saved chat message with ID: {msg_id}")
    
    # Get chat history
    history = db.get_chat_history(user_id=user_id, limit=10)
    print(f"✓ Retrieved {len(history)} chat messages")
    
    # Get recent context
    context = db.get_recent_context(user_id=user_id, limit=5)
    print(f"✓ Retrieved {len(context)} context messages")

def test_farm_activity_methods():
    """Test farm activity methods"""
    print("\n=== Testing Farm Activity Methods ===")
    db = DatabaseManager('raitha_mitra.db')
    user_id = ensure_test_user(db)
    
    # Save farm activity
    activity_id = db.save_farm_activity(
        user_id=user_id,
        activity_type="irrigation",
        crop_type="tomato",
        scheduled_date="2025-10-20",
        description="Water the tomato plants"
    )
    print(f"✓ Saved farm activity with ID: {activity_id}")
    
    # Get farm schedule
    schedule = db.get_farm_schedule(user_id=user_id)
    print(f"✓ Retrieved {len(schedule)} scheduled activities")
    
    # Update activity status
    success = db.update_activity_status(
        activity_id=activity_id,
        status="completed",
        completed_date="2025-10-20",
        notes="Completed successfully"
    )
    print(f"✓ Updated activity status: {success}")
    
    # Get activity history
    history = db.get_activity_history(user_id=user_id, limit=10)
    print(f"✓ Retrieved {len(history)} activity history records")

def test_yield_prediction_methods():
    """Test yield prediction methods"""
    print("\n=== Testing Yield Prediction Methods ===")
    db = DatabaseManager('raitha_mitra.db')
    user_id = ensure_test_user(db)
    
    # Save yield prediction
    pred_id = db.save_yield_prediction(
        user_id=user_id,
        crop_type="tomato",
        planting_date="2025-09-01",
        predicted_yield=500.0,
        confidence_score=0.85,
        predicted_quality="Grade A",
        harvest_date="2025-12-15"
    )
    print(f"✓ Saved yield prediction with ID: {pred_id}")
    
    # Get yield predictions
    predictions = db.get_yield_predictions(user_id=user_id)
    print(f"✓ Retrieved {len(predictions)} yield predictions")
    
    # Update actual yield
    success = db.update_actual_yield(
        prediction_id=pred_id,
        actual_yield=520.0,
        actual_quality="Grade A"
    )
    print(f"✓ Updated actual yield: {success}")

def test_financial_methods():
    """Test financial tracking methods"""
    print("\n=== Testing Financial Methods ===")
    db = DatabaseManager('raitha_mitra.db')
    user_id = ensure_test_user(db)
    
    # Save expense
    expense_id = db.save_expense(
        user_id=user_id,
        category="fertilizer",
        amount=2500.0,
        expense_date="2025-10-15",
        description="NPK fertilizer purchase"
    )
    print(f"✓ Saved expense with ID: {expense_id}")
    
    # Get expenses
    expenses = db.get_expenses(user_id=user_id)
    print(f"✓ Retrieved {len(expenses)} expenses")
    
    # Save financial score
    score_id = db.save_financial_score(
        user_id=user_id,
        overall_score=75.5,
        score_breakdown={
            "cost_efficiency_score": 80.0,
            "yield_performance_score": 70.0,
            "market_timing_score": 76.5
        }
    )
    print(f"✓ Saved financial score with ID: {score_id}")
    
    # Get latest financial score
    score = db.get_latest_financial_score(user_id=user_id)
    print(f"✓ Retrieved latest financial score: {score['overall_score'] if score else 'None'}")

def test_messaging_methods():
    """Test messaging system methods"""
    print("\n=== Testing Messaging Methods ===")
    db = DatabaseManager('raitha_mitra.db')
    user_id = ensure_test_user(db)
    
    # Send message (use demo user as receiver)
    msg_id = db.send_message(
        sender_id=user_id,
        receiver_id=1,
        message_text="Hello! How is your tomato crop doing?"
    )
    print(f"✓ Sent message with ID: {msg_id}")
    
    # Get inbox
    inbox = db.get_inbox(user_id=1, limit=10)
    print(f"✓ Retrieved inbox with {len(inbox)} conversations")
    
    # Get conversation
    conversation = db.get_conversation(user_id=user_id, other_user_id=1)
    print(f"✓ Retrieved conversation with {len(conversation)} messages")
    
    # Mark message as read
    if msg_id:
        success = db.mark_message_read(message_id=msg_id)
        print(f"✓ Marked message as read: {success}")
    
    # Test blocking (use a non-existent user ID to avoid conflicts)
    blocked = db.block_user(user_id=user_id, blocked_user_id=999)
    print(f"✓ Blocked user: {blocked}")
    
    is_blocked = db.is_blocked(user_id=user_id, other_user_id=999)
    print(f"✓ Verified block status: {is_blocked}")

def test_friend_network_methods():
    """Test friend network methods"""
    print("\n=== Testing Friend Network Methods ===")
    db = DatabaseManager('raitha_mitra.db')
    user_id = ensure_test_user(db)
    
    # Send friend request (to demo user)
    req_id = db.send_friend_request(requester_id=user_id, recipient_id=1)
    print(f"✓ Sent friend request with ID: {req_id}")
    
    # Get friend requests
    requests = db.get_friend_requests(user_id=1)
    print(f"✓ Retrieved {len(requests)} friend requests")
    
    # Accept friend request
    if req_id:
        success = db.accept_friend_request(request_id=req_id)
        print(f"✓ Accepted friend request: {success}")
    
    # Get friends
    friends = db.get_friends(user_id=user_id)
    print(f"✓ Retrieved {len(friends)} friends")
    
    # Check if friends
    are_friends = db.are_friends(user_id=user_id, other_user_id=1)
    print(f"✓ Verified friendship status: {are_friends}")
    
    # Remove friend
    # removed = db.remove_friend(user_id=user_id, friend_id=1)
    # print(f"✓ Removed friend: {removed}")

def test_location_methods():
    """Test map and location methods"""
    print("\n=== Testing Location Methods ===")
    db = DatabaseManager('raitha_mitra.db')
    user_id = ensure_test_user(db)
    
    # Update user location
    success = db.update_user_location(
        user_id=user_id,
        latitude=12.9716,
        longitude=77.5946,
        privacy_level="district"
    )
    print(f"✓ Updated user location: {success}")
    
    # Get regional farmers
    farmers = db.get_regional_farmers(region_name="Karnataka", region_type="state")
    print(f"✓ Retrieved {len(farmers)} regional farmers")
    
    # Get nearby farmers
    nearby = db.get_nearby_farmers(user_id=user_id, radius_km=50)
    print(f"✓ Retrieved {len(nearby)} nearby farmers")
    
    # Update regional stats
    success = db.update_regional_stats(region_name="Karnataka", region_type="state")
    print(f"✓ Updated regional stats: {success}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing New DatabaseManager Methods")
    print("=" * 60)
    
    try:
        test_chat_methods()
        test_farm_activity_methods()
        test_yield_prediction_methods()
        test_financial_methods()
        test_messaging_methods()
        test_friend_network_methods()
        test_location_methods()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

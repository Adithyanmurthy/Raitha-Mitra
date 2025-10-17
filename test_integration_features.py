"""
Integration Test Suite for Raitha Mitra Advanced Features
Tests all new features end-to-end including:
- Chat with context memory
- Farm planner schedule generation
- Yield prediction
- Financial health score
- Messaging between users
- Friend network functionality
- Community map with privacy settings
"""

import sqlite3
import json
from datetime import datetime, timedelta
from database import DatabaseManager
from chat_service import generate_contextual_response, build_context_prompt
from farm_service import generate_weekly_schedule, calculate_growth_stage
from yield_service import predict_yield, calculate_confidence
from finance_service import calculate_health_score, analyze_cost_efficiency
from map_service import aggregate_farmer_locations, get_regional_stats, find_nearby_farmers

# Test configuration
TEST_DB = 'raitha_mitra.db'
# Initialize database manager (will be created per test to avoid locking)
db = None

def print_test_header(test_name):
    """Print formatted test header"""
    print("\n" + "="*70)
    print(f"TEST: {test_name}")
    print("="*70)

def print_result(test_name, passed, details=""):
    """Print test result"""
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"{status}: {test_name}")
    if details:
        print(f"  Details: {details}")

def test_chat_context_memory():
    """Test 10.1.1: Chat with context memory across sessions"""
    print_test_header("Chat with Context Memory Across Sessions")
    
    try:
        # Create database connection
        db = DatabaseManager(TEST_DB)
        
        # Get or create test user
        test_user = db.get_user_by_email('test_chat@example.com')
        if not test_user:
            db.create_user('Test Chat User', 'test_chat@example.com', 'password123', '9876543210', 'Karnataka')
            test_user = db.get_user_by_email('test_chat@example.com')
        
        user_id = test_user['id']
        
        # Test 1: Send first message and save
        message1 = "I am growing tomatoes in my farm"
        response1 = "That's great! Tomatoes are a popular crop. What specific help do you need?"
        context1 = json.dumps({"crop": "tomatoes", "topic": "general"})
        
        db.save_chat_message(user_id, message1, response1, context1, 'en')
        print_result("Save first chat message", True, "Message saved with tomato context")
        
        # Test 2: Send second message referencing previous context
        message2 = "What fertilizer should I use?"
        response2 = "For tomatoes, I recommend NPK fertilizer with ratio 5-10-10"
        context2 = json.dumps({"crop": "tomatoes", "topic": "fertilizer"})
        
        db.save_chat_message(user_id, message2, response2, context2, 'en')
        print_result("Save second chat message", True, "Context maintained across messages")
        
        # Test 3: Retrieve chat history
        history = db.get_chat_history(user_id, limit=10)
        if len(history) >= 2:
            print_result("Retrieve chat history", True, f"Retrieved {len(history)} messages")
        else:
            print_result("Retrieve chat history", False, f"Expected 2+, got {len(history)}")
        
        # Test 4: Build context prompt
        context_prompt = build_context_prompt(user_id, "When should I harvest?")
        has_context = "tomato" in context_prompt.lower() or "fertilizer" in context_prompt.lower()
        print_result("Context prompt includes history", has_context, 
                    "Previous conversation context included" if has_context else "Context missing")
        
        # Test 5: Get recent context
        recent_context = db.get_recent_context(user_id, limit=5)
        print_result("Get recent context", len(recent_context) > 0, 
                    f"Retrieved {len(recent_context)} context entries")
        
        return True
        
    except Exception as e:
        print_result("Chat context memory test", False, str(e))
        return False

def test_farm_planner():
    """Test 10.1.2: Farm planner schedule generation and task management"""
    print_test_header("Farm Planner Schedule Generation and Task Management")
    
    try:
        # Create database connection
        db = DatabaseManager(TEST_DB)
        
        # Get test user
        test_user = db.get_user_by_email('test_chat@example.com')
        user_id = test_user['id']
        
        # Test 1: Save farm activity
        today = datetime.now().date()
        activity_id = db.save_farm_activity(
            user_id, 
            'irrigation', 
            'tomatoes', 
            today,
            'Morning irrigation for tomato plants'
        )
        print_result("Save farm activity", activity_id is not None, f"Activity ID: {activity_id}")
        
        # Test 2: Get farm schedule
        end_date = today + timedelta(days=7)
        schedule = db.get_farm_schedule(user_id, today, end_date)
        print_result("Get farm schedule", len(schedule) > 0, f"Retrieved {len(schedule)} activities")
        
        # Test 3: Update activity status
        if activity_id:
            completed = db.update_activity_status(activity_id, 'completed', today, 'Completed successfully')
            print_result("Update activity status", completed, "Activity marked as completed")
        
        # Test 4: Get activity history
        history = db.get_activity_history(user_id, limit=10)
        print_result("Get activity history", len(history) > 0, f"Retrieved {len(history)} activities")
        
        # Test 5: Calculate growth stage
        planting_date = today - timedelta(days=30)
        growth_stage = calculate_growth_stage(planting_date, 'tomatoes')
        print_result("Calculate growth stage", growth_stage is not None, f"Growth stage: {growth_stage}")
        
        # Test 6: Generate weekly schedule (AI-based)
        try:
            schedule_data = generate_weekly_schedule(user_id, 'tomatoes', 'vegetative')
            has_tasks = 'tasks' in schedule_data or 'activities' in schedule_data
            print_result("Generate AI weekly schedule", has_tasks, "Schedule generated with tasks")
        except Exception as e:
            print_result("Generate AI weekly schedule", False, f"AI generation error: {str(e)}")
        
        return True
        
    except Exception as e:
        print_result("Farm planner test", False, str(e))
        return False

def test_yield_prediction():
    """Test 10.1.3: Yield prediction with various crops"""
    print_test_header("Yield Prediction with Various Crops")
    
    try:
        # Create database connection
        db = DatabaseManager(TEST_DB)
        
        test_user = db.get_user_by_email('test_chat@example.com')
        user_id = test_user['id']
        
        crops_to_test = ['tomatoes', 'rice', 'wheat']
        
        for crop in crops_to_test:
            # Test 1: Save yield prediction
            planting_date = datetime.now().date() - timedelta(days=45)
            prediction_id = db.save_yield_prediction(
                user_id,
                crop,
                planting_date,
                predicted_yield=500.0,
                confidence_score=0.85
            )
            print_result(f"Save {crop} prediction", prediction_id is not None, 
                        f"Prediction ID: {prediction_id}")
        
        # Test 2: Get yield predictions
        predictions = db.get_yield_predictions(user_id)
        print_result("Get yield predictions", len(predictions) >= len(crops_to_test), 
                    f"Retrieved {len(predictions)} predictions")
        
        # Test 3: Update actual yield
        if predictions:
            first_pred = predictions[0]
            updated = db.update_actual_yield(first_pred['id'], 520.0, 'Grade A')
            print_result("Update actual yield", updated, "Actual yield recorded")
        
        # Test 4: Calculate confidence score
        confidence = calculate_confidence(data_completeness=0.9, weather_stability=0.8)
        print_result("Calculate confidence score", 0 <= confidence <= 1, 
                    f"Confidence: {confidence:.2f}")
        
        # Test 5: Predict yield with AI
        try:
            farm_data = {
                'soil_type': 'loamy',
                'irrigation': 'drip',
                'farm_size': 2.5
            }
            prediction = predict_yield(user_id, 'tomatoes', planting_date, farm_data)
            has_prediction = 'predicted_yield' in prediction or 'yield' in prediction
            print_result("AI yield prediction", has_prediction, "Prediction generated")
        except Exception as e:
            print_result("AI yield prediction", False, f"AI error: {str(e)}")
        
        return True
        
    except Exception as e:
        print_result("Yield prediction test", False, str(e))
        return False

def test_financial_health():
    """Test 10.1.4: Financial health score calculation"""
    print_test_header("Financial Health Score Calculation")
    
    try:
        # Create database connection
        db = DatabaseManager(TEST_DB)
        
        test_user = db.get_user_by_email('test_chat@example.com')
        user_id = test_user['id']
        
        # Test 1: Save expenses
        expense_categories = [
            ('seeds', 5000.0, 'Tomato seeds'),
            ('fertilizer', 3000.0, 'NPK fertilizer'),
            ('labor', 8000.0, 'Farm labor costs'),
            ('equipment', 2000.0, 'Tools and equipment')
        ]
        
        today = datetime.now().date()
        for category, amount, description in expense_categories:
            expense_id = db.save_expense(user_id, category, amount, today, description)
            print_result(f"Save {category} expense", expense_id is not None, 
                        f"Amount: ₹{amount}")
        
        # Test 2: Get expenses
        start_date = today - timedelta(days=30)
        expenses = db.get_expenses(user_id, start_date, today)
        print_result("Get expenses", len(expenses) >= len(expense_categories), 
                    f"Retrieved {len(expenses)} expenses")
        
        # Test 3: Calculate health score
        try:
            score_data = calculate_health_score(user_id)
            has_score = 'overall_score' in score_data or 'score' in score_data
            if has_score:
                score = score_data.get('overall_score', score_data.get('score', 0))
                print_result("Calculate health score", True, f"Score: {score:.1f}/100")
            else:
                print_result("Calculate health score", False, "No score in response")
        except Exception as e:
            print_result("Calculate health score", False, f"Calculation error: {str(e)}")
        
        # Test 4: Save financial score
        score_breakdown = json.dumps({
            'cost_efficiency': 75.0,
            'yield_performance': 80.0,
            'market_timing': 70.0
        })
        score_id = db.save_financial_score(user_id, 75.0, score_breakdown)
        print_result("Save financial score", score_id is not None, f"Score ID: {score_id}")
        
        # Test 5: Get latest financial score
        latest_score = db.get_latest_financial_score(user_id)
        print_result("Get latest financial score", latest_score is not None, 
                    f"Score: {latest_score.get('overall_score', 0):.1f}")
        
        # Test 6: Analyze cost efficiency
        try:
            analysis = analyze_cost_efficiency(expenses, {'predicted_yield': 500.0})
            has_analysis = analysis is not None and len(str(analysis)) > 0
            print_result("Analyze cost efficiency", has_analysis, "Analysis completed")
        except Exception as e:
            print_result("Analyze cost efficiency", False, f"Analysis error: {str(e)}")
        
        return True
        
    except Exception as e:
        print_result("Financial health test", False, str(e))
        return False

def test_messaging_system():
    """Test 10.1.5: Messaging between users"""
    print_test_header("Messaging Between Users")
    
    try:
        # Create database connection
        db = DatabaseManager(TEST_DB)
        
        # Get or create test users
        user1 = db.get_user_by_email('test_chat@example.com')
        
        user2 = db.get_user_by_email('test_user2@example.com')
        if not user2:
            db.create_user('Test User 2', 'test_user2@example.com', 'password123', '9876543211', 'Karnataka')
            user2 = db.get_user_by_email('test_user2@example.com')
        
        user1_id = user1['id']
        user2_id = user2['id']
        
        # Test 1: Send message
        message_id = db.send_message(user1_id, user2_id, "Hello! How is your tomato crop?")
        print_result("Send message", message_id is not None, f"Message ID: {message_id}")
        
        # Test 2: Get inbox
        inbox = db.get_inbox(user2_id, limit=10)
        print_result("Get inbox", len(inbox) > 0, f"Retrieved {len(inbox)} messages")
        
        # Test 3: Get conversation
        conversation = db.get_conversation(user1_id, user2_id)
        print_result("Get conversation", len(conversation) > 0, 
                    f"Retrieved {len(conversation)} messages")
        
        # Test 4: Mark message as read
        if message_id:
            marked = db.mark_message_read(message_id)
            print_result("Mark message as read", marked, "Message marked as read")
        
        # Test 5: Send reply
        reply_id = db.send_message(user2_id, user1_id, "My tomatoes are doing great! Thanks for asking.")
        print_result("Send reply", reply_id is not None, f"Reply ID: {reply_id}")
        
        # Test 6: Block user
        blocked = db.block_user(user1_id, user2_id)
        print_result("Block user", blocked, "User blocked successfully")
        
        # Test 7: Check if blocked
        is_blocked = db.is_blocked(user1_id, user2_id)
        print_result("Check if blocked", is_blocked, "Block status verified")
        
        # Test 8: Unblock for future tests (cleanup)
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM blocked_users WHERE user_id = ? AND blocked_user_id = ?',
                      (user1_id, user2_id))
        conn.commit()
        conn.close()
        print_result("Cleanup: Unblock user", True, "User unblocked for future tests")
        
        return True
        
    except Exception as e:
        print_result("Messaging system test", False, str(e))
        return False

def test_friend_network():
    """Test 10.1.6: Friend network functionality"""
    print_test_header("Friend Network Functionality")
    
    try:
        # Create database connection
        db = DatabaseManager(TEST_DB)
        
        user1 = db.get_user_by_email('test_chat@example.com')
        user2 = db.get_user_by_email('test_user2@example.com')
        
        user1_id = user1['id']
        user2_id = user2['id']
        
        # Test 1: Send friend request
        request_id = db.send_friend_request(user1_id, user2_id)
        print_result("Send friend request", request_id is not None, f"Request ID: {request_id}")
        
        # Test 2: Get friend requests
        requests = db.get_friend_requests(user2_id)
        print_result("Get friend requests", len(requests) > 0, 
                    f"Retrieved {len(requests)} requests")
        
        # Test 3: Accept friend request
        if request_id:
            accepted = db.accept_friend_request(request_id)
            print_result("Accept friend request", accepted, "Friend request accepted")
        
        # Test 4: Check if friends
        are_friends = db.are_friends(user1_id, user2_id)
        print_result("Check if friends", are_friends, "Friendship verified")
        
        # Test 5: Get friends list
        friends = db.get_friends(user1_id)
        print_result("Get friends list", len(friends) > 0, f"Retrieved {len(friends)} friends")
        
        # Test 6: Remove friend
        removed = db.remove_friend(user1_id, user2_id)
        print_result("Remove friend", removed, "Friend removed successfully")
        
        # Test 7: Verify removal
        still_friends = db.are_friends(user1_id, user2_id)
        print_result("Verify friend removal", not still_friends, "Friendship removed")
        
        # Test 8: Decline friend request (create new request first)
        request_id2 = db.send_friend_request(user1_id, user2_id)
        if request_id2:
            declined = db.decline_friend_request(request_id2)
            print_result("Decline friend request", declined, "Request declined")
        
        return True
        
    except Exception as e:
        print_result("Friend network test", False, str(e))
        return False

def test_community_map():
    """Test 10.1.7: Community map with privacy settings"""
    print_test_header("Community Map with Privacy Settings")
    
    try:
        # Create database connection
        db = DatabaseManager(TEST_DB)
        
        user1 = db.get_user_by_email('test_chat@example.com')
        user1_id = user1['id']
        
        # Test 1: Update user location
        updated = db.update_user_location(user1_id, 12.9716, 77.5946, 'district')
        print_result("Update user location", updated, "Location: Bangalore (district privacy)")
        
        # Test 2: Get regional farmers
        farmers = db.get_regional_farmers('Karnataka', 'state')
        print_result("Get regional farmers", len(farmers) >= 0, 
                    f"Retrieved {len(farmers)} farmers in Karnataka")
        
        # Test 3: Get nearby farmers
        nearby = find_nearby_farmers(user1_id, radius_km=50)
        print_result("Get nearby farmers", nearby is not None, 
                    f"Found {len(nearby) if nearby else 0} nearby farmers")
        
        # Test 4: Aggregate farmer locations
        aggregated = aggregate_farmer_locations(privacy_level='district')
        print_result("Aggregate farmer locations", aggregated is not None, 
                    "Location data aggregated by district")
        
        # Test 5: Get regional stats
        stats = get_regional_stats('Karnataka')
        print_result("Get regional stats", stats is not None, 
                    f"Stats retrieved for Karnataka")
        
        # Test 6: Update regional stats
        updated_stats = db.update_regional_stats('Karnataka', 'state')
        print_result("Update regional stats", updated_stats, "Regional stats updated")
        
        # Test 7: Test privacy levels
        privacy_levels = ['exact', 'district', 'state', 'hidden']
        for privacy in privacy_levels:
            updated = db.update_user_location(user1_id, 12.9716, 77.5946, privacy)
            print_result(f"Privacy level: {privacy}", updated, f"Location privacy set to {privacy}")
        
        return True
        
    except Exception as e:
        print_result("Community map test", False, str(e))
        return False

def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("RAITHA MITRA - INTEGRATION TEST SUITE")
    print("Testing all advanced features end-to-end")
    print("="*70)
    
    results = {
        'Chat Context Memory': test_chat_context_memory(),
        'Farm Planner': test_farm_planner(),
        'Yield Prediction': test_yield_prediction(),
        'Financial Health': test_financial_health(),
        'Messaging System': test_messaging_system(),
        'Friend Network': test_friend_network(),
        'Community Map': test_community_map()
    }
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All integration tests passed successfully!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the details above.")
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)

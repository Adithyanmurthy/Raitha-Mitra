#!/usr/bin/env python3
"""
Verify that all new DatabaseManager methods exist and are callable
"""
import inspect
from database import DatabaseManager

def verify_methods():
    """Verify all new methods exist"""
    print("=" * 60)
    print("Verifying DatabaseManager Methods")
    print("=" * 60)
    
    db = DatabaseManager()
    
    # Define expected methods by category
    expected_methods = {
        "Chat Methods": [
            "save_chat_message",
            "get_chat_history",
            "get_recent_context"
        ],
        "Farm Activity Methods": [
            "save_farm_activity",
            "get_farm_schedule",
            "update_activity_status",
            "get_activity_history"
        ],
        "Yield Prediction Methods": [
            "save_yield_prediction",
            "get_yield_predictions",
            "update_actual_yield"
        ],
        "Financial Methods": [
            "save_expense",
            "get_expenses",
            "save_financial_score",
            "get_latest_financial_score"
        ],
        "Messaging Methods": [
            "send_message",
            "get_inbox",
            "get_conversation",
            "mark_message_read",
            "block_user",
            "is_blocked"
        ],
        "Friend Network Methods": [
            "send_friend_request",
            "accept_friend_request",
            "decline_friend_request",
            "get_friends",
            "get_friend_requests",
            "remove_friend",
            "are_friends"
        ],
        "Location Methods": [
            "update_user_location",
            "get_regional_farmers",
            "get_nearby_farmers",
            "update_regional_stats"
        ]
    }
    
    all_passed = True
    
    for category, methods in expected_methods.items():
        print(f"\n{category}:")
        for method_name in methods:
            if hasattr(db, method_name):
                method = getattr(db, method_name)
                if callable(method):
                    # Get method signature
                    sig = inspect.signature(method)
                    params = list(sig.parameters.keys())
                    print(f"  ✓ {method_name}({', '.join(params)})")
                else:
                    print(f"  ✗ {method_name} exists but is not callable")
                    all_passed = False
            else:
                print(f"  ✗ {method_name} not found")
                all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All methods verified successfully!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some methods are missing or not callable")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    exit(verify_methods())

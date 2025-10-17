"""
System Integration Verification Script
Verifies that all components are properly configured and integrated
"""

import os
import sqlite3
import sys
from pathlib import Path

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_result(test, passed, details=""):
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"[{status}] {test}")
    if details:
        print(f"        {details}")

def verify_files_exist():
    """Verify all required files exist"""
    print_header("FILE STRUCTURE VERIFICATION")
    
    required_files = {
        'Database': 'raitha_mitra.db',
        'Main App': 'app.py',
        'Database Manager': 'database.py',
        'Chat Service': 'chat_service.py',
        'Farm Service': 'farm_service.py',
        'Yield Service': 'yield_service.py',
        'Finance Service': 'finance_service.py',
        'Map Service': 'map_service.py',
        'Rate Limiter': 'rate_limiter.py',
        'Security Utils': 'security_utils.py',
    }
    
    templates = {
        'Chat Template': 'templates/chat.html',
        'Farm Planner Template': 'templates/farm_planner.html',
        'Yield Prediction Template': 'templates/yield_prediction.html',
        'Financial Health Template': 'templates/financial_health.html',
        'Messages Template': 'templates/messages.html',
        'Friends Template': 'templates/friends.html',
        'Community Map Template': 'templates/community_map.html',
        'Privacy Settings Template': 'templates/privacy_settings.html',
    }
    
    javascript = {
        'Chat JS': 'static/js/chat.js',
        'Farm Planner JS': 'static/js/farm-planner.js',
        'Yield Prediction JS': 'static/js/yield-prediction.js',
        'Financial Health JS': 'static/js/financial-health.js',
        'Messages JS': 'static/js/messages.js',
        'Friends JS': 'static/js/friends.js',
        'Community Map JS': 'static/js/community-map.js',
        'Notifications JS': 'static/js/notifications.js',
        'Privacy Settings JS': 'static/js/privacy-settings.js',
    }
    
    all_files = {**required_files, **templates, **javascript}
    
    passed = 0
    failed = 0
    
    for name, filepath in all_files.items():
        exists = os.path.exists(filepath)
        if exists:
            size = os.path.getsize(filepath)
            print_result(name, True, f"{filepath} ({size} bytes)")
            passed += 1
        else:
            print_result(name, False, f"{filepath} NOT FOUND")
            failed += 1
    
    print(f"\nFiles: {passed} found, {failed} missing")
    return failed == 0

def verify_database_schema():
    """Verify database schema is correct"""
    print_header("DATABASE SCHEMA VERIFICATION")
    
    required_tables = [
        'users',
        'predictions',
        'chat_messages',
        'farm_activities',
        'yield_predictions',
        'farm_expenses',
        'financial_scores',
        'messages',
        'blocked_users',
        'friend_requests',
        'friendships',
        'regional_stats',
    ]
    
    try:
        conn = sqlite3.connect('raitha_mitra.db')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        passed = 0
        failed = 0
        
        for table in required_tables:
            if table in existing_tables:
                # Get column count
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                print_result(f"Table: {table}", True, f"{len(columns)} columns")
                passed += 1
            else:
                print_result(f"Table: {table}", False, "NOT FOUND")
                failed += 1
        
        # Check indexes
        print("\nDatabase Indexes:")
        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        for idx_name, tbl_name in indexes:
            print_result(f"Index: {idx_name}", True, f"on table {tbl_name}")
        
        conn.close()
        
        print(f"\nTables: {passed} found, {failed} missing")
        return failed == 0
        
    except Exception as e:
        print_result("Database Connection", False, str(e))
        return False

def verify_database_methods():
    """Verify DatabaseManager has all required methods"""
    print_header("DATABASE METHODS VERIFICATION")
    
    try:
        from database import DatabaseManager
        
        required_methods = [
            # Chat methods
            'save_chat_message',
            'get_chat_history',
            'get_recent_context',
            # Farm methods
            'save_farm_activity',
            'get_farm_schedule',
            'update_activity_status',
            'get_activity_history',
            # Yield methods
            'save_yield_prediction',
            'get_yield_predictions',
            'update_actual_yield',
            # Finance methods
            'save_expense',
            'get_expenses',
            'save_financial_score',
            'get_latest_financial_score',
            # Messaging methods
            'send_message',
            'get_inbox',
            'get_conversation',
            'mark_message_read',
            'block_user',
            'is_blocked',
            # Friend methods
            'send_friend_request',
            'accept_friend_request',
            'decline_friend_request',
            'get_friends',
            'get_friend_requests',
            'remove_friend',
            'are_friends',
            # Map methods
            'update_user_location',
            'get_regional_farmers',
            'get_nearby_farmers',
            'update_regional_stats',
        ]
        
        passed = 0
        failed = 0
        
        for method in required_methods:
            if hasattr(DatabaseManager, method):
                print_result(f"Method: {method}", True)
                passed += 1
            else:
                print_result(f"Method: {method}", False, "NOT FOUND")
                failed += 1
        
        print(f"\nMethods: {passed} found, {failed} missing")
        return failed == 0
        
    except Exception as e:
        print_result("Import DatabaseManager", False, str(e))
        return False

def verify_service_modules():
    """Verify service modules can be imported"""
    print_header("SERVICE MODULES VERIFICATION")
    
    services = [
        ('chat_service', ['generate_contextual_response', 'build_context_prompt']),
        ('farm_service', ['generate_weekly_schedule', 'calculate_growth_stage']),
        ('yield_service', ['predict_yield', 'calculate_confidence']),
        ('finance_service', ['calculate_health_score', 'analyze_cost_efficiency']),
        ('map_service', ['aggregate_farmer_locations', 'get_regional_stats']),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, functions in services:
        try:
            module = __import__(module_name)
            print_result(f"Module: {module_name}", True, "imported successfully")
            passed += 1
            
            # Check functions
            for func in functions:
                if hasattr(module, func):
                    print_result(f"  Function: {func}", True)
                else:
                    print_result(f"  Function: {func}", False, "NOT FOUND")
                    
        except Exception as e:
            print_result(f"Module: {module_name}", False, str(e))
            failed += 1
    
    print(f"\nModules: {passed} imported, {failed} failed")
    return failed == 0

def verify_environment():
    """Verify environment configuration"""
    print_header("ENVIRONMENT CONFIGURATION")
    
    # Check .env file
    env_exists = os.path.exists('.env')
    print_result(".env file", env_exists)
    
    if env_exists:
        with open('.env', 'r') as f:
            env_content = f.read()
            has_gemini_key = 'GEMINI_API_KEY' in env_content
            print_result("GEMINI_API_KEY configured", has_gemini_key)
    
    # Check Python version
    python_version = sys.version
    print_result("Python version", True, python_version.split()[0])
    
    # Check required packages
    required_packages = [
        'flask',
        'google.generativeai',
        'werkzeug',
        'dotenv',
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print_result(f"Package: {package}", True, "installed")
        except ImportError:
            print_result(f"Package: {package}", False, "NOT INSTALLED")
    
    return True

def verify_api_routes():
    """Verify API routes are defined"""
    print_header("API ROUTES VERIFICATION")
    
    try:
        # Read app.py to check for routes
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        required_routes = [
            # Chat routes
            ('/chat', 'GET'),
            ('/api/chat/send', 'POST'),
            ('/api/chat/history', 'GET'),
            # Farm planner routes
            ('/farm-planner', 'GET'),
            ('/api/farm/schedule', 'GET'),
            ('/api/farm/activity', 'POST'),
            ('/api/farm/generate-schedule', 'POST'),
            # Yield prediction routes
            ('/yield-prediction', 'GET'),
            ('/api/yield/predict', 'POST'),
            ('/api/yield/history', 'GET'),
            # Financial health routes
            ('/financial-health', 'GET'),
            ('/api/finance/score', 'GET'),
            ('/api/finance/expense', 'POST'),
            # Messaging routes
            ('/messages', 'GET'),
            ('/api/messages/inbox', 'GET'),
            ('/api/messages/send', 'POST'),
            # Friend routes
            ('/friends', 'GET'),
            ('/api/friends/list', 'GET'),
            # Map routes
            ('/community-map', 'GET'),
            ('/api/map/farmers', 'GET'),
        ]
        
        passed = 0
        failed = 0
        
        for route, method in required_routes:
            # Simple check if route is defined
            route_pattern = f"'{route}'" if "'" in app_content else f'"{route}"'
            if route_pattern in app_content:
                print_result(f"{method} {route}", True)
                passed += 1
            else:
                print_result(f"{method} {route}", False, "NOT FOUND")
                failed += 1
        
        print(f"\nRoutes: {passed} found, {failed} missing")
        return failed == 0
        
    except Exception as e:
        print_result("Read app.py", False, str(e))
        return False

def main():
    """Run all verification tests"""
    print("\n" + "="*70)
    print("  RAITHA MITRA - SYSTEM INTEGRATION VERIFICATION")
    print("  Checking system configuration and component integration")
    print("="*70)
    
    results = {
        'File Structure': verify_files_exist(),
        'Database Schema': verify_database_schema(),
        'Database Methods': verify_database_methods(),
        'Service Modules': verify_service_modules(),
        'Environment': verify_environment(),
        'API Routes': verify_api_routes(),
    }
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"[{status}] {test_name}")
    
    print(f"\nTotal: {passed}/{total} verifications passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All system integration checks passed!")
        print("✅ System is properly configured and ready for testing")
        print("\n📋 Next Steps:")
        print("   1. Review INTEGRATION_TEST_CHECKLIST.md")
        print("   2. Start the Flask application: python app.py")
        print("   3. Perform manual testing using the checklist")
        print("   4. Test on multiple browsers and devices")
        print("   5. Verify performance under load")
    else:
        print(f"\n⚠️  {total - passed} verification(s) failed")
        print("❌ Please fix the issues above before proceeding")
        print("\n📋 Review the failed checks and:")
        print("   1. Ensure all files are present")
        print("   2. Verify database schema is complete")
        print("   3. Check that all methods are implemented")
        print("   4. Confirm all dependencies are installed")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

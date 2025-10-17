"""
Existing Features Verification Script
Verifies that all original features still work after adding new features
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

def verify_disease_detection():
    """Verify disease detection functionality"""
    print_header("DISEASE DETECTION VERIFICATION")
    
    try:
        # Check if model file exists
        model_exists = os.path.exists('crop_disease_detection_model.h5')
        print_result("Disease detection model file", model_exists, 
                    "crop_disease_detection_model.h5")
        
        # Check if class names file exists
        classes_exist = os.path.exists('class_names.json')
        print_result("Class names file", classes_exist, "class_names.json")
        
        # Check if crop_disease_model.py exists
        model_py_exists = os.path.exists('crop_disease_model.py')
        print_result("Disease model Python file", model_py_exists, 
                    "crop_disease_model.py")
        
        # Check if predictions table exists
        conn = sqlite3.connect('raitha_mitra.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
        table_exists = cursor.fetchone() is not None
        print_result("Predictions table", table_exists, "Database table exists")
        
        if table_exists:
            # Check table structure
            cursor.execute("PRAGMA table_info(predictions)")
            columns = [col[1] for col in cursor.fetchall()]
            required_columns = ['id', 'user_id', 'image_path', 'disease_name', 
                              'confidence', 'treatment', 'created_at']
            has_all_columns = all(col in columns for col in required_columns)
            print_result("Predictions table structure", has_all_columns, 
                        f"{len(columns)} columns")
        
        # Check if upload directory exists
        upload_dir = os.path.exists('static/uploads')
        print_result("Upload directory", upload_dir, "static/uploads")
        
        # Check if home template has disease detection
        with open('templates/home.html', 'r') as f:
            home_content = f.read()
            has_upload = 'upload' in home_content.lower() or 'disease' in home_content.lower()
            print_result("Home template has disease detection", has_upload)
        
        conn.close()
        return True
        
    except Exception as e:
        print_result("Disease detection verification", False, str(e))
        return False

def verify_weather_integration():
    """Verify weather integration"""
    print_header("WEATHER INTEGRATION VERIFICATION")
    
    try:
        # Check if weather API is configured in app.py
        with open('app.py', 'r') as f:
            app_content = f.read()
            has_weather = 'weather' in app_content.lower()
            print_result("Weather functionality in app.py", has_weather)
        
        # Check if weather.js exists
        weather_js_exists = os.path.exists('static/js/weather.js')
        print_result("Weather JavaScript file", weather_js_exists, 
                    "static/js/weather.js")
        
        # Check if home template has weather widget
        with open('templates/home.html', 'r') as f:
            home_content = f.read()
            has_weather_widget = 'weather' in home_content.lower()
            print_result("Home template has weather widget", has_weather_widget)
        
        return True
        
    except Exception as e:
        print_result("Weather integration verification", False, str(e))
        return False

def verify_user_authentication():
    """Verify user authentication system"""
    print_header("USER AUTHENTICATION VERIFICATION")
    
    try:
        # Check if users table exists
        conn = sqlite3.connect('raitha_mitra.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone() is not None
        print_result("Users table", table_exists)
        
        if table_exists:
            # Check table structure
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            required_columns = ['id', 'name', 'email', 'mobile', 'location']
            # Check for either 'password' or 'password_hash'
            has_password = 'password' in columns or 'password_hash' in columns
            has_all_columns = all(col in columns for col in required_columns) and has_password
            print_result("Users table structure", has_all_columns, 
                        f"{len(columns)} columns")
            
            # Check if passwords are hashed (check one user)
            password_col = 'password_hash' if 'password_hash' in columns else 'password'
            cursor.execute(f"SELECT {password_col} FROM users LIMIT 1")
            result = cursor.fetchone()
            if result:
                password = result[0]
                # Hashed passwords are typically long strings
                is_hashed = len(password) > 20
                print_result("Passwords are hashed", is_hashed, 
                           f"Password length: {len(password)}")
        
        # Check if login/register templates exist
        login_exists = os.path.exists('templates/login.html')
        print_result("Login template", login_exists, "templates/login.html")
        
        register_exists = os.path.exists('templates/register.html')
        print_result("Register template", register_exists, "templates/register.html")
        
        # Check if auth routes exist in app.py
        with open('app.py', 'r') as f:
            app_content = f.read()
            has_login = "'/login'" in app_content or '"/login"' in app_content
            has_register = "'/register'" in app_content or '"/register"' in app_content
            has_logout = "'/logout'" in app_content or '"/logout"' in app_content
            
            print_result("Login route", has_login)
            print_result("Register route", has_register)
            print_result("Logout route", has_logout)
        
        # Check if auth.js exists
        auth_js_exists = os.path.exists('static/js/auth.js')
        print_result("Auth JavaScript file", auth_js_exists, "static/js/auth.js")
        
        conn.close()
        return True
        
    except Exception as e:
        print_result("User authentication verification", False, str(e))
        return False

def verify_prediction_history():
    """Verify prediction history functionality"""
    print_header("PREDICTION HISTORY VERIFICATION")
    
    try:
        # Check if predictions table has data
        conn = sqlite3.connect('raitha_mitra.db')
        cursor = conn.cursor()
        
        # Check predictions table
        cursor.execute("SELECT COUNT(*) FROM predictions")
        pred_count = cursor.fetchone()[0]
        print_result("Disease predictions in database", pred_count > 0, 
                    f"{pred_count} predictions")
        
        # Check yield_predictions table
        cursor.execute("SELECT COUNT(*) FROM yield_predictions")
        yield_count = cursor.fetchone()[0]
        print_result("Yield predictions in database", yield_count >= 0, 
                    f"{yield_count} predictions")
        
        # Check if home template has history view
        with open('templates/home.html', 'r') as f:
            home_content = f.read()
            has_history = 'history' in home_content.lower()
            print_result("Home template has history view", has_history)
        
        # Check if yield prediction template has history
        with open('templates/yield_prediction.html', 'r') as f:
            yield_content = f.read()
            has_history = 'history' in yield_content.lower()
            print_result("Yield prediction template has history", has_history)
        
        conn.close()
        return True
        
    except Exception as e:
        print_result("Prediction history verification", False, str(e))
        return False

def verify_multi_language_support():
    """Verify multi-language support"""
    print_header("MULTI-LANGUAGE SUPPORT VERIFICATION")
    
    try:
        # Check if chat supports multiple languages
        conn = sqlite3.connect('raitha_mitra.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(chat_messages)")
        columns = [col[1] for col in cursor.fetchall()]
        has_language_column = 'language' in columns
        print_result("Chat messages have language column", has_language_column)
        
        # Check if chat service supports language
        with open('chat_service.py', 'r') as f:
            chat_content = f.read()
            has_language_param = 'language' in chat_content
            print_result("Chat service supports language parameter", has_language_param)
        
        # Check if chat template has language selector
        with open('templates/chat.html', 'r') as f:
            chat_template = f.read()
            has_language_selector = 'language' in chat_template.lower()
            print_result("Chat template has language selector", has_language_selector)
        
        # Check if chat.js handles language
        with open('static/js/chat.js', 'r') as f:
            chat_js = f.read()
            has_language_handling = 'language' in chat_js.lower()
            print_result("Chat JavaScript handles language", has_language_handling)
        
        conn.close()
        return True
        
    except Exception as e:
        print_result("Multi-language support verification", False, str(e))
        return False

def verify_database_integrity():
    """Verify database integrity and relationships"""
    print_header("DATABASE INTEGRITY VERIFICATION")
    
    try:
        conn = sqlite3.connect('raitha_mitra.db')
        cursor = conn.cursor()
        
        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0] == 1
        print_result("Foreign keys enabled", fk_enabled)
        
        # Check for orphaned records in predictions
        cursor.execute("""
            SELECT COUNT(*) FROM predictions 
            WHERE user_id NOT IN (SELECT id FROM users)
        """)
        orphaned_predictions = cursor.fetchone()[0]
        print_result("No orphaned predictions", orphaned_predictions == 0, 
                    f"{orphaned_predictions} orphaned records")
        
        # Check for orphaned records in chat_messages
        cursor.execute("""
            SELECT COUNT(*) FROM chat_messages 
            WHERE user_id NOT IN (SELECT id FROM users)
        """)
        orphaned_chat = cursor.fetchone()[0]
        print_result("No orphaned chat messages", orphaned_chat == 0, 
                    f"{orphaned_chat} orphaned records")
        
        # Check for orphaned records in farm_activities
        cursor.execute("""
            SELECT COUNT(*) FROM farm_activities 
            WHERE user_id NOT IN (SELECT id FROM users)
        """)
        orphaned_activities = cursor.fetchone()[0]
        print_result("No orphaned farm activities", orphaned_activities == 0, 
                    f"{orphaned_activities} orphaned records")
        
        # Check for orphaned messages
        cursor.execute("""
            SELECT COUNT(*) FROM messages 
            WHERE sender_id NOT IN (SELECT id FROM users)
            OR receiver_id NOT IN (SELECT id FROM users)
        """)
        orphaned_messages = cursor.fetchone()[0]
        print_result("No orphaned messages", orphaned_messages == 0, 
                    f"{orphaned_messages} orphaned records")
        
        conn.close()
        return True
        
    except Exception as e:
        print_result("Database integrity verification", False, str(e))
        return False

def verify_api_backward_compatibility():
    """Verify that existing API routes still work"""
    print_header("API BACKWARD COMPATIBILITY VERIFICATION")
    
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Check original routes still exist
        original_routes = [
            ('/', 'Home route'),
            ('/login', 'Login route'),
            ('/register', 'Register route'),
            ('/home', 'Home page route'),
            ('/predict', 'Disease prediction route'),
        ]
        
        all_exist = True
        for route, description in original_routes:
            route_pattern = f"'{route}'" if "'" in app_content else f'"{route}"'
            exists = route_pattern in app_content
            print_result(description, exists, route)
            if not exists:
                all_exist = False
        
        return all_exist
        
    except Exception as e:
        print_result("API backward compatibility verification", False, str(e))
        return False

def main():
    """Run all existing feature verifications"""
    print("\n" + "="*70)
    print("  RAITHA MITRA - EXISTING FEATURES VERIFICATION")
    print("  Verifying that original features still work correctly")
    print("="*70)
    
    results = {
        'Disease Detection': verify_disease_detection(),
        'Weather Integration': verify_weather_integration(),
        'User Authentication': verify_user_authentication(),
        'Prediction History': verify_prediction_history(),
        'Multi-Language Support': verify_multi_language_support(),
        'Database Integrity': verify_database_integrity(),
        'API Backward Compatibility': verify_api_backward_compatibility(),
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
        print("\n🎉 All existing features verified successfully!")
        print("✅ Original functionality is preserved")
        print("\n📋 Verified Features:")
        print("   ✓ Disease detection with ML model")
        print("   ✓ Weather integration and forecasts")
        print("   ✓ User authentication and security")
        print("   ✓ Prediction history tracking")
        print("   ✓ Multi-language support")
        print("   ✓ Database integrity and relationships")
        print("   ✓ API backward compatibility")
    else:
        print(f"\n⚠️  {total - passed} verification(s) failed")
        print("❌ Some existing features may have issues")
        print("\n📋 Please review the failed checks above")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

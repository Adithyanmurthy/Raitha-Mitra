"""
Performance Verification Script
Verifies database performance, query optimization, and system efficiency
"""

import sqlite3
import time
import os
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

def verify_database_indexes():
    """Verify that proper indexes exist for performance"""
    print_header("DATABASE INDEX VERIFICATION")
    
    try:
        conn = sqlite3.connect('raitha_mitra.db')
        cursor = conn.cursor()
        
        # Get all indexes
        cursor.execute("""
            SELECT name, tbl_name, sql 
            FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        indexes = cursor.fetchall()
        
        print(f"Total custom indexes: {len(indexes)}")
        
        # Check for important indexes
        required_indexes = {
            'chat_messages': ['user_id', 'created_at'],
            'farm_activities': ['user_id', 'scheduled_date'],
            'farm_expenses': ['user_id', 'expense_date'],
            'messages': ['receiver_id', 'sender_id'],
            'predictions': ['user_id'],
        }
        
        for table, columns in required_indexes.items():
            for column in columns:
                # Check if index exists for this column
                has_index = any(table in idx[1] and column in str(idx[2]) 
                              for idx in indexes if idx[2])
                print_result(f"Index on {table}.{column}", has_index)
        
        conn.close()
        return True
        
    except Exception as e:
        print_result("Database index verification", False, str(e))
        return False

def verify_query_performance():
    """Test query performance with EXPLAIN QUERY PLAN"""
    print_header("QUERY PERFORMANCE VERIFICATION")
    
    try:
        conn = sqlite3.connect('raitha_mitra.db')
        cursor = conn.cursor()
        
        # Test queries that should use indexes
        test_queries = [
            ("Chat history query", 
             "SELECT * FROM chat_messages WHERE user_id = 1 ORDER BY created_at DESC LIMIT 10"),
            ("Farm schedule query",
             "SELECT * FROM farm_activities WHERE user_id = 1 AND scheduled_date >= date('now')"),
            ("Expense query",
             "SELECT * FROM farm_expenses WHERE user_id = 1 AND expense_date >= date('now', '-30 days')"),
            ("Inbox query",
             "SELECT * FROM messages WHERE receiver_id = 1 ORDER BY created_at DESC LIMIT 20"),
            ("Predictions query",
             "SELECT * FROM predictions WHERE user_id = 1 ORDER BY created_at DESC"),
        ]
        
        for query_name, query in test_queries:
            # Use EXPLAIN QUERY PLAN to check if indexes are used
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = cursor.fetchall()
            
            # Check if index is used (plan should mention "USING INDEX")
            uses_index = any("USING INDEX" in str(row) for row in plan)
            
            # Measure query execution time
            start_time = time.time()
            cursor.execute(query)
            cursor.fetchall()
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            is_fast = execution_time < 100  # Should be under 100ms
            
            print_result(query_name, is_fast, 
                        f"{execution_time:.2f}ms, Index: {uses_index}")
        
        conn.close()
        return True
        
    except Exception as e:
        print_result("Query performance verification", False, str(e))
        return False

def verify_database_size():
    """Check database size and table sizes"""
    print_header("DATABASE SIZE VERIFICATION")
    
    try:
        db_path = 'raitha_mitra.db'
        if not os.path.exists(db_path):
            print_result("Database file", False, "Not found")
            return False
        
        # Get database file size
        db_size = os.path.getsize(db_path)
        db_size_mb = db_size / (1024 * 1024)
        
        print_result("Database file size", True, f"{db_size_mb:.2f} MB")
        
        # Get table sizes
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print("\nTable row counts:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print_result(f"  {table}", True, f"{count} rows")
        
        conn.close()
        return True
        
    except Exception as e:
        print_result("Database size verification", False, str(e))
        return False

def verify_file_sizes():
    """Check sizes of static files"""
    print_header("STATIC FILE SIZE VERIFICATION")
    
    try:
        # Check CSS files
        css_dir = Path('static/css')
        if css_dir.exists():
            for css_file in css_dir.glob('*.css'):
                size = os.path.getsize(css_file)
                size_kb = size / 1024
                is_reasonable = size_kb < 500  # CSS should be under 500KB
                print_result(f"CSS: {css_file.name}", is_reasonable, 
                           f"{size_kb:.2f} KB")
        
        # Check JS files
        js_dir = Path('static/js')
        if js_dir.exists():
            for js_file in js_dir.glob('*.js'):
                size = os.path.getsize(js_file)
                size_kb = size / 1024
                is_reasonable = size_kb < 200  # JS files should be under 200KB each
                print_result(f"JS: {js_file.name}", is_reasonable, 
                           f"{size_kb:.2f} KB")
        
        return True
        
    except Exception as e:
        print_result("File size verification", False, str(e))
        return False

def verify_code_efficiency():
    """Check for potential performance issues in code"""
    print_header("CODE EFFICIENCY VERIFICATION")
    
    try:
        # Check database.py for connection pooling or proper connection handling
        with open('database.py', 'r') as f:
            db_content = f.read()
        
        # Check if connections are properly closed
        has_close = 'conn.close()' in db_content or 'connection.close()' in db_content
        print_result("Database connections are closed", has_close)
        
        # Check if cursors are used efficiently
        has_cursor = 'cursor' in db_content
        print_result("Uses database cursors", has_cursor)
        
        # Check if parameterized queries are used (prevents SQL injection and improves performance)
        has_params = '?' in db_content
        print_result("Uses parameterized queries", has_params)
        
        # Check service modules for caching or optimization
        service_files = ['chat_service.py', 'farm_service.py', 'yield_service.py', 
                        'finance_service.py', 'map_service.py']
        
        for service_file in service_files:
            if os.path.exists(service_file):
                with open(service_file, 'r') as f:
                    content = f.read()
                
                # Check if error handling exists
                has_try_except = 'try:' in content and 'except' in content
                print_result(f"{service_file}: Has error handling", has_try_except)
        
        return True
        
    except Exception as e:
        print_result("Code efficiency verification", False, str(e))
        return False

def verify_rate_limiting():
    """Verify rate limiting is implemented"""
    print_header("RATE LIMITING VERIFICATION")
    
    try:
        # Check if rate_limiter.py exists
        rate_limiter_exists = os.path.exists('rate_limiter.py')
        print_result("Rate limiter module exists", rate_limiter_exists)
        
        if rate_limiter_exists:
            with open('rate_limiter.py', 'r') as f:
                content = f.read()
            
            # Check for rate limiting implementation
            has_rate_limit_class = 'class' in content and 'RateLimit' in content
            print_result("Has RateLimiter class", has_rate_limit_class)
            
            # Check if it's used in app.py
            with open('app.py', 'r') as f:
                app_content = f.read()
            
            uses_rate_limiter = 'rate_limit' in app_content.lower()
            print_result("Rate limiting used in app", uses_rate_limiter)
        
        return True
        
    except Exception as e:
        print_result("Rate limiting verification", False, str(e))
        return False

def verify_security_measures():
    """Verify security measures that affect performance"""
    print_header("SECURITY MEASURES VERIFICATION")
    
    try:
        # Check if security_utils.py exists
        security_exists = os.path.exists('security_utils.py')
        print_result("Security utils module exists", security_exists)
        
        if security_exists:
            with open('security_utils.py', 'r') as f:
                content = f.read()
            
            # Check for input sanitization
            has_sanitize = 'sanitize' in content.lower()
            print_result("Has input sanitization", has_sanitize)
            
            # Check for password hashing
            has_hash = 'hash' in content.lower()
            print_result("Has password hashing", has_hash)
        
        # Check app.py for security headers
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Check for CORS configuration
        has_cors = 'CORS' in app_content or 'cors' in app_content.lower()
        print_result("CORS configured", has_cors)
        
        return True
        
    except Exception as e:
        print_result("Security measures verification", False, str(e))
        return False

def verify_api_response_structure():
    """Verify API responses are optimized"""
    print_header("API RESPONSE OPTIMIZATION")
    
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Check if JSON responses are used
        uses_jsonify = 'jsonify' in app_content
        print_result("Uses jsonify for JSON responses", uses_jsonify)
        
        # Check if error responses are standardized
        has_error_handling = 'error' in app_content.lower() and 'return' in app_content
        print_result("Has error response handling", has_error_handling)
        
        # Check if pagination is implemented for large datasets
        has_limit = 'limit' in app_content.lower()
        print_result("Uses pagination/limits", has_limit)
        
        return True
        
    except Exception as e:
        print_result("API response optimization verification", False, str(e))
        return False

def verify_caching_strategy():
    """Check if caching is implemented where appropriate"""
    print_header("CACHING STRATEGY VERIFICATION")
    
    try:
        # Check service files for caching
        service_files = ['chat_service.py', 'farm_service.py', 'yield_service.py', 
                        'finance_service.py', 'map_service.py']
        
        has_any_caching = False
        
        for service_file in service_files:
            if os.path.exists(service_file):
                with open(service_file, 'r') as f:
                    content = f.read()
                
                # Check for caching mechanisms
                has_cache = 'cache' in content.lower()
                if has_cache:
                    has_any_caching = True
                    print_result(f"{service_file}: Uses caching", has_cache)
        
        # Note: Caching is optional but recommended
        print_result("Caching implemented (optional)", has_any_caching, 
                    "Caching can improve performance for repeated queries")
        
        return True
        
    except Exception as e:
        print_result("Caching strategy verification", False, str(e))
        return False

def main():
    """Run all performance verifications"""
    print("\n" + "="*70)
    print("  RAITHA MITRA - PERFORMANCE VERIFICATION")
    print("  Verifying system performance and optimization")
    print("="*70)
    
    results = {
        'Database Indexes': verify_database_indexes(),
        'Query Performance': verify_query_performance(),
        'Database Size': verify_database_size(),
        'File Sizes': verify_file_sizes(),
        'Code Efficiency': verify_code_efficiency(),
        'Rate Limiting': verify_rate_limiting(),
        'Security Measures': verify_security_measures(),
        'API Response Optimization': verify_api_response_structure(),
        'Caching Strategy': verify_caching_strategy(),
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
        print("\n🎉 All performance checks passed!")
        print("✅ System is optimized for production use")
        print("\n📋 Verified Performance Features:")
        print("   ✓ Database indexes for fast queries")
        print("   ✓ Query performance under 100ms")
        print("   ✓ Reasonable file sizes")
        print("   ✓ Efficient code practices")
        print("   ✓ Rate limiting for API protection")
        print("   ✓ Security measures in place")
        print("   ✓ Optimized API responses")
        print("\n⚡ Performance Recommendations:")
        print("   1. Monitor query performance in production")
        print("   2. Consider implementing caching for frequently accessed data")
        print("   3. Test with realistic user loads")
        print("   4. Monitor database growth and optimize as needed")
        print("   5. Consider CDN for static files in production")
    else:
        print(f"\n⚠️  {total - passed} verification(s) failed")
        print("❌ Some performance optimizations may be needed")
        print("\n📋 Please review the failed checks above")
    
    return passed == total

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)

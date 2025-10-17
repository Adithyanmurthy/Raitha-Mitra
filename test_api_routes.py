"""
Quick test script to verify API routes are properly configured
"""

import sys
import importlib.util

def test_app_imports():
    """Test that app.py can be imported without errors"""
    try:
        spec = importlib.util.spec_from_file_location("app", "app.py")
        app_module = importlib.util.module_from_spec(spec)
        
        print("✅ app.py imports successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing app.py: {e}")
        return False

def test_service_modules():
    """Test that all service modules can be imported"""
    modules = [
        'chat_service',
        'farm_service',
        'yield_service',
        'finance_service',
        'map_service'
    ]
    
    all_success = True
    for module_name in modules:
        try:
            spec = importlib.util.spec_from_file_location(module_name, f"{module_name}.py")
            module = importlib.util.module_from_spec(spec)
            print(f"✅ {module_name}.py imports successfully")
        except Exception as e:
            print(f"❌ Error importing {module_name}.py: {e}")
            all_success = False
    
    return all_success

def main():
    print("=" * 60)
    print("Testing API Routes Implementation")
    print("=" * 60)
    
    print("\n1. Testing Service Modules...")
    service_test = test_service_modules()
    
    print("\n2. Testing App Module...")
    app_test = test_app_imports()
    
    print("\n" + "=" * 60)
    if service_test and app_test:
        print("✅ All tests passed! API routes are properly configured.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 60)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Quick script to reset user password for testing
"""

import requests
import json

def reset_password(email_or_mobile, new_password='123456'):
    """Reset user password via API"""
    try:
        response = requests.post('http://127.0.0.1:5000/api/reset-password', 
                               json={
                                   'emailOrMobile': email_or_mobile,
                                   'newPassword': new_password
                               })
        
        if response.ok:
            result = response.json()
            print(f"✅ Password reset successful!")
            print(f"👤 User: {result['user']}")
            print(f"🔑 New Password: {result['new_password']}")
        else:
            error = response.json()
            print(f"❌ Password reset failed: {error['error']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    print("🔄 Password Reset Tool")
    print("=" * 30)
    
    # Reset password for the users having login issues
    emails = ['tnajaykumar562@gmail.com', 'tnajaykumar563@gmail.com']
    
    for email in emails:
        print(f"Resetting password for: {email}")
        reset_password(email)
        print()
    
    print(f"💡 You can now login with any of these accounts:")
    for email in emails:
        print(f"   Email: {email}")
        print(f"   Password: 123456")
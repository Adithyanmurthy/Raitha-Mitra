#!/usr/bin/env python3
"""
Test script to verify and manually manage friend requests
"""

import sqlite3
from database import Database

db = Database()

def show_all_users():
    """Show all users in the system"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, location FROM users')
    users = cursor.fetchall()
    conn.close()
    
    print("\n=== ALL USERS ===")
    for user in users:
        print(f"ID: {user['id']}, Name: {user['name']}, Email: {user['email']}, Location: {user.get('location', 'N/A')}")
    print()

def show_friend_requests():
    """Show all pending friend requests"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT fr.id, fr.requester_id, fr.recipient_id, fr.status, fr.created_at,
               u1.name as requester_name, u2.name as recipient_name
        FROM friend_requests fr
        JOIN users u1 ON fr.requester_id = u1.id
        JOIN users u2 ON fr.recipient_id = u2.id
        ORDER BY fr.created_at DESC
    ''')
    requests = cursor.fetchall()
    conn.close()
    
    print("\n=== FRIEND REQUESTS ===")
    if not requests:
        print("No friend requests found")
    else:
        for req in requests:
            print(f"Request ID: {req['id']}")
            print(f"  From: {req['requester_name']} (ID: {req['requester_id']})")
            print(f"  To: {req['recipient_name']} (ID: {req['recipient_id']})")
            print(f"  Status: {req['status']}")
            print(f"  Created: {req['created_at']}")
            print()

def show_friendships():
    """Show all friendships"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.*, u1.name as user1_name, u2.name as user2_name
        FROM friendships f
        JOIN users u1 ON f.user1_id = u1.id
        JOIN users u2 ON f.user2_id = u2.id
    ''')
    friendships = cursor.fetchall()
    conn.close()
    
    print("\n=== FRIENDSHIPS ===")
    if not friendships:
        print("No friendships found")
    else:
        for friendship in friendships:
            print(f"{friendship['user1_name']} (ID: {friendship['user1_id']}) <-> {friendship['user2_name']} (ID: {friendship['user2_id']})")
    print()

def accept_request(request_id):
    """Accept a friend request"""
    result = db.accept_friend_request(request_id)
    if result:
        print(f"✓ Friend request {request_id} accepted!")
    else:
        print(f"✗ Failed to accept request {request_id}")

def send_test_request(requester_id, recipient_id):
    """Send a test friend request"""
    request_id = db.send_friend_request(requester_id, recipient_id)
    if request_id:
        print(f"✓ Friend request sent! Request ID: {request_id}")
    else:
        print(f"✗ Failed to send request (may already exist or users are already friends)")

if __name__ == '__main__':
    print("=" * 50)
    print("FRIEND NETWORK TEST TOOL")
    print("=" * 50)
    
    show_all_users()
    show_friend_requests()
    show_friendships()
    
    print("\n=== QUICK ACTIONS ===")
    print("To accept a request: accept_request(request_id)")
    print("To send a request: send_test_request(requester_id, recipient_id)")
    print("\nExample:")
    print("  python3 -i test_friend_workflow.py")
    print("  >>> accept_request(1)")
    print("  >>> send_test_request(1, 2)")

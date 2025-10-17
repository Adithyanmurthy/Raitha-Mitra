#!/usr/bin/env python3
"""
Add sample financial data for testing
"""
import sqlite3
from datetime import datetime, timedelta

def add_sample_data():
    conn = sqlite3.connect('raitha_mitra.db')
    cursor = conn.cursor()
    
    # Get a user ID (use first user or create test user)
    cursor.execute("SELECT id FROM users LIMIT 1")
    result = cursor.fetchone()
    
    if not result:
        print("No users found. Please register a user first.")
        conn.close()
        return
    
    user_id = result[0]
    print(f"Adding sample data for user_id: {user_id}")
    
    # Add sample expenses
    today = datetime.now()
    expenses = [
        ('seeds', 5000, (today - timedelta(days=90)).strftime('%Y-%m-%d'), 'Rice seeds for 2 acres'),
        ('fertilizer', 8000, (today - timedelta(days=75)).strftime('%Y-%m-%d'), 'Organic fertilizer'),
        ('pesticides', 3000, (today - timedelta(days=60)).strftime('%Y-%m-%d'), 'Pest control'),
        ('labor', 12000, (today - timedelta(days=45)).strftime('%Y-%m-%d'), 'Farm labor for planting'),
        ('irrigation', 4000, (today - timedelta(days=30)).strftime('%Y-%m-%d'), 'Water pump maintenance'),
        ('equipment', 6000, (today - timedelta(days=15)).strftime('%Y-%m-%d'), 'Tools and equipment'),
    ]
    
    for category, amount, date, description in expenses:
        try:
            cursor.execute('''
                INSERT INTO farm_expenses (user_id, category, amount, expense_date, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, category, amount, date, description, datetime.now().isoformat()))
            print(f"Added expense: {category} - ₹{amount}")
        except Exception as e:
            print(f"Error adding expense {category}: {e}")
    
    # Check if yield predictions exist
    cursor.execute("SELECT COUNT(*) FROM yield_predictions WHERE user_id = ?", (user_id,))
    pred_count = cursor.fetchone()[0]
    
    if pred_count == 0:
        print("\nAdding sample yield prediction...")
        try:
            cursor.execute('''
                INSERT INTO yield_predictions 
                (user_id, crop_type, planting_date, predicted_yield, confidence_score, 
                 predicted_quality, harvest_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                'rice',
                (today - timedelta(days=90)).strftime('%Y-%m-%d'),
                3000,  # 3000 kg
                0.75,  # 75% confidence
                'B',
                (today + timedelta(days=30)).strftime('%Y-%m-%d'),
                datetime.now().isoformat()
            ))
            print("Added yield prediction: Rice - 3000 kg")
        except Exception as e:
            print(f"Error adding yield prediction: {e}")
    else:
        print(f"\n{pred_count} yield prediction(s) already exist")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Sample financial data added successfully!")
    print(f"Total expenses: ₹38,000")
    print(f"Projected revenue: ₹60,000 (3000 kg × ₹20/kg)")
    print(f"Expected profit: ₹22,000")
    print(f"Expected profit margin: 36.7%")
    print("\nNow refresh the Financial Health page to see the data!")

if __name__ == '__main__':
    add_sample_data()

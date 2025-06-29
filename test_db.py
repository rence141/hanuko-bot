#!/usr/bin/env python3
"""
Simple test script to check database connection and user data
"""

import os
import sys
from db import get_db_connection

def test_database():
    print("🔍 Testing database connection and user data...")
    print("=" * 50)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if users table exists and has data
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✅ Users table found with {user_count} users")
        
        if user_count > 0:
            # Get first few users
            cursor.execute("SELECT id, inventory, inventory_value FROM users LIMIT 5")
            users = cursor.fetchall()
            
            print("\n📋 Sample user data:")
            for user in users:
                user_id, inventory, inventory_value = user
                print(f"• User {user_id}: inventory={inventory}, value={inventory_value}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_database() 
#!/usr/bin/env python3
"""
Script to calculate and update inventory values for all existing users
"""

import os
import sys
from db import get_all_users, update_user, calculate_inventory_value

def update_all_inventory_values():
    print("💰 Updating inventory values for all users...")
    print("=" * 50)
    
    users = get_all_users()
    print(f"Found {len(users)} users in database")
    
    if not users:
        print("No users found. Checking if this is a database connection issue...")
        return
    
    total_updated = 0
    total_value = 0
    
    for user in users:
        user_id = user['id']
        inventory = user.get('inventory', [])
        
        print(f"Processing user {user_id} with inventory: {inventory}")
        
        # Calculate inventory value
        inventory_value = calculate_inventory_value(inventory)
        
        # Update user's inventory_value
        update_user(user_id, inventory_value=inventory_value)
        
        total_updated += 1
        total_value += inventory_value
        
        print(f"✅ User {user_id}: {len(inventory)} items = {inventory_value:,} credits")
    
    print(f"\n📊 Summary:")
    print(f"• Updated {total_updated} users")
    print(f"• Total inventory value across all users: {total_value:,} credits")
    print(f"• Average inventory value: {total_value // total_updated if total_updated > 0 else 0:,} credits")

if __name__ == "__main__":
    update_all_inventory_values() 
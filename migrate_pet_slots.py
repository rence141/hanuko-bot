#!/usr/bin/env python3
"""
Migration script to upgrade pet system from 1 slot to 2 slots
Converts equipped_pet (VARCHAR) to equipped_pets (TEXT JSON array)
"""

import psycopg2
import json
import os

# Database configuration
db_config = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'hanuko_bot'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'port': os.environ.get('DB_PORT', '5432')
}

def migrate_pet_slots():
    """Migrate from equipped_pet to equipped_pets"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        print("Starting pet slot migration...")
        
        # Check if equipped_pets column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'equipped_pets'
        """)
        
        if not cursor.fetchone():
            print("Adding equipped_pets column...")
            cursor.execute("ALTER TABLE users ADD COLUMN equipped_pets TEXT DEFAULT '[]'")
        
        # Check if equipped_pet column still exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'equipped_pet'
        """)
        
        if cursor.fetchone():
            print("Migrating data from equipped_pet to equipped_pets...")
            
            # Get all users with equipped_pet
            cursor.execute("SELECT id, equipped_pet FROM users WHERE equipped_pet IS NOT NULL AND equipped_pet != ''")
            users = cursor.fetchall()
            
            migrated_count = 0
            for user_id, equipped_pet in users:
                if equipped_pet:
                    # Convert single pet to array
                    equipped_pets = [equipped_pet]
                    cursor.execute(
                        "UPDATE users SET equipped_pets = %s WHERE id = %s",
                        (json.dumps(equipped_pets), user_id)
                    )
                    migrated_count += 1
            
            print(f"Migrated {migrated_count} users from single pet to pet array")
            
            # Drop the old column
            print("Dropping old equipped_pet column...")
            cursor.execute("ALTER TABLE users DROP COLUMN equipped_pet")
        
        conn.commit()
        print("Pet slot migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate_pet_slots() 
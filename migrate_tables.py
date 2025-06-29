#!/usr/bin/env python3
"""
Migration script to add missing columns to existing tables
"""

import os
import sys
from db import get_db_connection, SCHEMA

def migrate_tables():
    print("🔄 Migrating database tables...")
    print("=" * 50)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Migration for users table
    print("\n📋 Migrating users table...")
    user_migrations = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS equipped_weapon VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_daily TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_weekly TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS quiz_last TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS team VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS team_role VARCHAR(50)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS team_points INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_mission_start TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS equipped_pet VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS damaged_items TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS equipped_gun VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_streak INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_streak INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS inventory_value INTEGER DEFAULT 0"
    ]
    
    for migration in user_migrations:
        try:
            cursor.execute(migration)
            print(f"  ✅ {migration}")
        except Exception as e:
            print(f"  ⚠️  {migration} - {e}")
    
    # Migration for teams table
    print("\n📋 Migrating teams table...")
    team_migrations = [
        "ALTER TABLE teams ADD COLUMN IF NOT EXISTS owner BIGINT",
        "ALTER TABLE teams ADD COLUMN IF NOT EXISTS created TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE teams ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0",
        "ALTER TABLE teams ADD COLUMN IF NOT EXISTS icon TEXT",
        "ALTER TABLE teams ADD COLUMN IF NOT EXISTS description TEXT"
    ]
    
    for migration in team_migrations:
        try:
            cursor.execute(migration)
            print(f"  ✅ {migration}")
        except Exception as e:
            print(f"  ⚠️  {migration} - {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    migrate_tables() 
#!/usr/bin/env python3
"""
Database Setup Script for Hanuko Bot
This script automatically creates the database tables when the bot starts
"""

import os
import sys
import psycopg2
import psycopg2.extras

# Database Schema Definition
SCHEMA = {
    'users': {
        'id': 'BIGINT PRIMARY KEY',
        'xp': 'INTEGER DEFAULT 0',
        'level': 'INTEGER DEFAULT 1',
        'credits': 'INTEGER DEFAULT 0',
        'pets': 'TEXT',
        'inventory': 'TEXT',
        'equipped_weapon': 'VARCHAR(100)',
        'last_daily': 'TIMESTAMP',
        'last_weekly': 'TIMESTAMP',
        'achievements': 'TEXT',
        'pet_stats': 'TEXT',
        'pet_last_train': 'TEXT',
        'mission_progress': 'TEXT',
        'quiz_last': 'TIMESTAMP',
        'team': 'VARCHAR(100)',
        'team_role': 'VARCHAR(50)',
        'team_points': 'INTEGER DEFAULT 0',
        'last_mission_start': 'TIMESTAMP',
        'equipped_pets': 'TEXT DEFAULT \'[]\'',
        'battle_team': 'TEXT DEFAULT \'[]\'',
        'damaged_items': 'TEXT',
        'equipped_gun': 'VARCHAR(255)',
        'daily_streak': 'INTEGER DEFAULT 0',
        'weekly_streak': 'INTEGER DEFAULT 0',
        'inventory_value': 'INTEGER DEFAULT 0',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    },
    'teams': {
        'name': 'VARCHAR(100) PRIMARY KEY',
        'owner': 'BIGINT',
        'members': 'TEXT',
        'created': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'points': 'INTEGER DEFAULT 0',
        'icon': 'TEXT',
        'description': 'TEXT',
        'achievements': 'TEXT',
        'quest': 'TEXT'
    },
    'polls': {
        'id': 'SERIAL PRIMARY KEY',
        'question': 'TEXT NOT NULL',
        'options': 'JSONB NOT NULL',
        'votes': 'JSONB DEFAULT \'{}\'',
        'created_by': 'BIGINT NOT NULL',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    },
    'warnings': {
        'id': 'SERIAL PRIMARY KEY',
        'user_id': 'BIGINT NOT NULL',
        'reason': 'TEXT NOT NULL',
        'moderator_id': 'BIGINT NOT NULL',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }
}

def get_db_config():
    """Get database configuration from environment variables"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'hanuko_bot'),
        'port': os.getenv('DB_PORT', '5432')
    }

def get_db_connection():
    """Get database connection"""
    config = get_db_config()
    return psycopg2.connect(**config)

def create_tables():
    """Create all tables if they don't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🔧 Creating database tables...")
        
        for table_name, columns in SCHEMA.items():
            # Build CREATE TABLE statement
            column_definitions = []
            for col_name, col_type in columns.items():
                column_definitions.append(f"{col_name} {col_type}")
            
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(column_definitions)}
            );
            """
            
            try:
                cursor.execute(create_sql)
                print(f"✅ Table {table_name} created/verified successfully")
            except Exception as e:
                print(f"❌ Error creating table {table_name}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def check_database():
    """Check if database is accessible and tables exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return table_exists
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Hanuko Bot Database Setup")
    print("=" * 40)
    
    # Check environment variables
    config = get_db_config()
    print(f"📊 Database: {config['database']}")
    print(f"🌐 Host: {config['host']}")
    print(f"👤 User: {config['user']}")
    print(f"🔌 Port: {config['port']}")
    
    # Check if database is accessible
    if check_database():
        print("✅ Database is accessible and tables exist!")
    else:
        print("⚠️  Database tables not found, creating them...")
        if create_tables():
            print("✅ Database setup successful!")
        else:
            print("❌ Database setup failed!")
            sys.exit(1)

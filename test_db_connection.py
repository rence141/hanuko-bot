#!/usr/bin/env python3
"""
Test Database Connection Script
This script tests the database connection and table creation
"""

import os
import sys
from setup_database import get_db_config, create_tables, check_database

def main():
    print("🔍 Testing Database Connection...")
    print("=" * 40)
    
    # Get database config
    config = get_db_config()
    print(f"📊 Database: {config['database']}")
    print(f"🌐 Host: {config['host']}")
    print(f"👤 User: {config['user']}")
    print(f"🔌 Port: {config['port']}")
    
    # Check if database is accessible
    print("\n🔍 Checking database connection...")
    if check_database():
        print("✅ Database is accessible and tables exist!")
        return True
    else:
        print("⚠️  Database tables not found, creating them...")
        if create_tables():
            print("✅ Database setup successful!")
            return True
        else:
            print("❌ Database setup failed!")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

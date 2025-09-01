#!/usr/bin/env python3
"""
Database Setup Script for Hanuko Bot
This script helps you set up your database for deployment
"""

import os
import sys

def check_environment():
    """Check if required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} = {os.getenv(var)[:10]}..." if len(os.getenv(var)) > 10 else f"✅ {var} = {os.getenv(var)}")
        else:
            print(f"❌ {var} - NOT SET")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def setup_database():
    """Initialize the database"""
    print("\n🚀 Setting up database...")
    
    try:
        from db import create_tables
        create_tables()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def main():
    print("📊 Hanuko Bot Database Setup")
    print("=" * 40)
    
    # Check environment
    if not check_environment():
        print("\n❌ Missing environment variables!")
        print("\n📋 Please set these environment variables:")
        print("  DB_HOST=your-postgres-host")
        print("  DB_USER=your-postgres-user") 
        print("  DB_PASSWORD=your-postgres-password")
        print("  DB_NAME=your-database-name")
        print("  DB_PORT=5432 (optional, defaults to 5432)")
        return
    
    # Setup database
    if setup_database():
        print("\n🎉 Database setup complete!")
        print("\n📋 Your bot is ready to use with the database!")
    else:
        print("\n❌ Database setup failed!")
        print("Check your database connection and try again.")

if __name__ == "__main__":
    main()

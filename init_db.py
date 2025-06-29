#!/usr/bin/env python3
"""
Database initialization script for Hanuko Discord Bot
Run this script to create all necessary tables in PostgreSQL
"""

import os
import sys
from db import create_tables, get_table_structure, SCHEMA

def main():
    print("🚀 Initializing Hanuko Bot Database...")
    print("=" * 50)
    
    # Create all tables
    print("📋 Creating tables...")
    create_tables()
    
    # Show table structures
    print("\n📊 Database Schema:")
    print("=" * 50)
    
    for table_name in SCHEMA.keys():
        print(f"\n📋 Table: {table_name}")
        print("-" * 30)
        
        # Show defined schema
        print("Defined columns:")
        for col_name, col_type in SCHEMA[table_name].items():
            print(f"  • {col_name}: {col_type}")
        
        # Show actual database structure
        try:
            actual_columns = get_table_structure(table_name)
            if actual_columns:
                print("\nActual database columns:")
                for col in actual_columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {col[3]}" if col[3] else ""
                    print(f"  • {col[0]}: {col[1]} {nullable}{default}")
            else:
                print("  ⚠️  Table not found in database")
        except Exception as e:
            print(f"  ❌ Error reading table structure: {e}")
    
    print("\n✅ Database initialization complete!")
    print("\n🔧 Environment Variables needed:")
    print("  DB_HOST=your-postgres-host")
    print("  DB_USER=your-postgres-user")
    print("  DB_PASSWORD=your-postgres-password")
    print("  DB_NAME=your-database-name")
    print("  DB_PORT=5432")

if __name__ == "__main__":
    main() 
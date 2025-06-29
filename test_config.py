#!/usr/bin/env python3
"""
Test script to verify config module works correctly
"""

try:
    import config
    print("✅ Config module imported successfully!")
    print(f"BOT_TOKEN: {'Set' if config.BOT_TOKEN != 'your_discord_bot_token_here' else 'Not set'}")
    print(f"DEFAULT_PREFIX: {config.DEFAULT_PREFIX}")
    print(f"DB_CONFIG: {config.DB_CONFIG}")
    print("✅ All config values loaded successfully!")
except ImportError as e:
    print(f"❌ Error importing config: {e}")
except Exception as e:
    print(f"❌ Error with config: {e}") 
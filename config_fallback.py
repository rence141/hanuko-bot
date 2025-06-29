# config_fallback.py
import os

# Bot configuration with environment variable fallbacks
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "your_discord_bot_token_here")
DEFAULT_PREFIX = os.getenv("BOT_PREFIX", "/")

# Embed colors
EMBED_COLORS = {
    "warning": 0xFFA500,
    "success": 0x00FF00,
    "error": 0xFF0000,
    "info": 0x3498DB,
    "mod": 0x5865F2
}

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'hanuko_bot'),
    'port': os.getenv('DB_PORT', '5432')
} 
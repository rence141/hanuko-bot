#!/usr/bin/env python3
"""
Render Deployment Setup Script
Checks if your bot is ready for Render deployment
"""

import os
import json
import sys

def check_files():
    """Check if all required files exist"""
    required_files = [
        'hanuko_bot.py',
        'requirements.txt',
        'render.yaml',
        'cogs/__init__.py',
        'cogs/game.py',
        'cogs/misc.py',
        'cogs/moderation.py',
        'cogs/pets.py',
        'cogs/roles.py',
        'cogs/shop.py',
        'cogs/teams.py'
    ]
    
    print("🔍 Checking required files...")
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_requirements():
    """Check if requirements.txt has necessary packages"""
    print("\n📦 Checking requirements.txt...")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    required_packages = ['discord.py', 'aiohttp']
    missing_packages = []
    
    for package in required_packages:
        if package in content:
            print(f"✅ {package}")
        else:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_config():
    """Check if config.py exists and has BOT_TOKEN"""
    print("\n⚙️ Checking configuration...")
    
    if not os.path.exists('config.py'):
        print("⚠️ config.py not found - You'll need to set DISCORD_BOT_TOKEN in Render")
        return True
    
    try:
        with open('config.py', 'r') as f:
            content = f.read()
        
        if 'BOT_TOKEN' in content:
            print("✅ BOT_TOKEN found in config.py")
        else:
            print("⚠️ BOT_TOKEN not found in config.py")
        
        return True
    except:
        print("❌ Error reading config.py")
        return False

def check_json_files():
    """Check if JSON data files exist"""
    print("\n📄 Checking JSON data files...")
    
    json_files = [
        'game_data.json',
        'teams.json',
        'marketplace.json',
        'warnings.json',
        'afk_status.json',
        'polls.json'
    ]
    
    for file in json_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"⚠️ {file} - Will be created automatically")

def main():
    """Main setup check"""
    print("🚀 Render Deployment Setup Check")
    print("=" * 40)
    
    all_good = True
    
    # Check files
    if not check_files():
        all_good = False
    
    # Check requirements
    if not check_requirements():
        all_good = False
    
    # Check config
    if not check_config():
        all_good = False
    
    # Check JSON files
    check_json_files()
    
    print("\n" + "=" * 40)
    
    if all_good:
        print("🎉 Your bot is ready for Render deployment!")
        print("\n📋 Next steps:")
        print("1. Go to render.com and create account")
        print("2. Connect your GitHub repository")
        print("3. Create new Web Service")
        print("4. Set environment variables")
        print("5. Deploy!")
        print("\n📖 See DEPLOYMENT.md for detailed instructions")
    else:
        print("❌ Some issues found. Please fix them before deploying.")
        print("\n🔧 Common fixes:")
        print("- Make sure all files are in the correct locations")
        print("- Check that requirements.txt has discord.py and aiohttp")
        print("- Verify your bot token is ready")
    
    print("\n🇵🇭 Good luck with your deployment!")

if __name__ == "__main__":
    main() 
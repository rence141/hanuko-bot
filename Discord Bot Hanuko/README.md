# 🤖 Hanuko - SCP Foundation Discord Bot

A comprehensive SCP Foundation-themed Discord bot with gaming mechanics, economy systems, pet battles, and special events.

## ✨ Features

### 🎮 Core Game Features
- **Mission System**: Complete missions to earn XP and progress
- **Daily & Weekly Rewards**: Claim regular rewards to build your wealth
- **Leveling System**: Gain XP and level up your character
- **Leaderboards**: Compete with other players for top spots

### 🏪 Economy & Trading
- **SCP Shop**: Purchase items like Containment Suits, Keycards, and more
- **Marketplace**: List, browse, and buy items from other players
- **Trading System**: Propose and complete trades with other users
- **Credit System**: Earn and spend credits throughout the game

### 🐾 Pet System
- **Pet Adoption**: Adopt random pets through gacha mechanics
- **Premium Pets**: Special high-tier pets for dedicated players
- **Pet Battles**: Battle your pets against other users' pets
- **Pet Management**: Train, equip, unequip, and release pets

### 🎲 Gambling & Entertainment
- **SCP-914**: Gamble with different settings (rough, coarse, 1:1, fine, very fine)
- **SCP-294**: Order mystery drinks for random outcomes
- **SCP-963**: Flip Dr. Bright's Coin of Fate
- **SCP-999**: Hug the tickle monster for lucky rewards

### 🎯 Special Events
- **SCP-008 Breach Events**: Server-wide containment breach events where players can use Containment Suits to survive
- **Vault Airdrop Events**: Special vaults drop that require specific keycard levels to claim
- **Quest System**: Daily, weekly, and monthly quests with rewards

### 🛡️ Moderation & Admin
- **Word Filter**: Auto-detect and moderate inappropriate content
- **Warning System**: Track and manage user warnings
- **Custom Roles**: Create and assign custom server roles
- **Team System**: Join teams and collaborate with other players

## 🚀 Setup

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token
- Discord.py library

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/hanuko-bot.git
   cd hanuko-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the bot**
   - Create a `config.py` file with your bot token:
   ```python
   BOT_TOKEN = "your_discord_bot_token_here"
   DEFAULT_COMMAND = "/"
   ```

4. **Run the bot**
   ```bash
   python hanuko_bot.py
   ```

## 📁 Project Structure

```
hanuko-bot/
├── cogs/                 # Bot command modules
│   ├── game.py          # Core game mechanics
│   ├── misc.py          # Miscellaneous commands
│   ├── moderation.py    # Moderation features
│   ├── pets.py          # Pet system
│   ├── roles.py         # Role management
│   ├── shop.py          # Shop and economy
│   ├── teams.py         # Team system
│   └── testcmd.py       # Testing commands
├── hanuko_bot.py        # Main bot file
├── config.py            # Configuration (create this)
├── db.py               # Database functions
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🎯 Key Commands

### General
- `/profile` - View your profile
- `/mission` - Complete missions
- `/daily` - Claim daily rewards
- `/weekly` - Claim weekly rewards
- `/leaderboard` - View top players

### Economy
- `/shop` - Browse the shop
- `/buy` - Purchase items
- `/inventory` - View your inventory
- `/marketplace` - Trade with other players

### Pets
- `/adoptpet` - Adopt a random pet
- `/premiumpets` - Adopt premium pets
- `/petbattle` - Battle other pets
- `/pets` - Manage your pets

### Events
- `/containmentsuit` - Use during SCP-008 breaches
- `/claimvault` - Claim airdropped vaults
- `/quest` - View and claim quests

## 🔧 Configuration

The bot uses several JSON files for data storage:
- `game_data.json` - Game configuration
- `teams.json` - Team data
- `marketplace.json` - Marketplace listings
- `warnings.json` - User warnings
- And more...

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Creator

**Rence / notreiiii**

## ⭐ Support

If you find this bot useful, please give it a star! For support, join our Discord server or open an issue on GitHub.

---

*"Your SCP Foundation assistant - missions, pets, and containment chaos await!"* 

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

### AFK System

The bot includes a comprehensive AFK (Away From Keyboard) system:

#### Commands
- `/afk [message]` - Set your AFK status with an optional custom message
- `/return` - Manually return from AFK status
- `/afklist` - View all currently AFK users

#### Features
- **Automatic Return**: Users are automatically removed from AFK when they send any message
- **Time Tracking**: Shows how long a user was AFK when they return
- **Custom Messages**: Set personalized AFK messages
- **Public Notifications**: When someone returns from AFK, a welcome message is sent to the channel
- **Mention Detection**: When someone mentions an AFK user, the bot shows their AFK status and reason
- **Persistent Storage**: AFK status is saved and persists across bot restarts

#### How It Works
1. Use `/afk [message]` to set your AFK status
2. Your AFK status is stored with timestamp and message
3. When you send any message, you're automatically removed from AFK
4. A welcome back message shows your AFK message and time spent AFK
5. When someone mentions you while AFK, the bot shows your AFK status and reason
6. Use `/afklist` to see who's currently AFK
7. Use `/return` to manually return from AFK without sending a message

### Daily & Weekly Streaks

Enhanced reward system with streak tracking and multipliers:

#### Daily Streaks
- **Base Reward**: 100 credits
- **Streak Multiplier**: Up to 2x (10% increase per day)
- **Milestone Bonuses**:
  - 7 days: +200 credits
  - 14 days: +500 credits
  - 30 days: +1000 credits
  - 100 days: +5000 credits
- **Streak Reset**: Automatically resets if missed for more than 48 hours

#### Weekly Streaks
- **Base Reward**: 500 credits
- **Streak Multiplier**: Up to 3x (20% increase per week)
- **Milestone Bonuses**:
  - 4 weeks: +1000 credits
  - 8 weeks: +2500 credits
  - 12 weeks: +5000 credits
  - 52 weeks (1 year): +25000 credits
- **Streak Reset**: Automatically resets if missed for more than 14 days

#### Features
- **Visual Feedback**: Shows current streak, multiplier, and bonus rewards
- **Profile Integration**: Streak information displayed in user profiles
- **Milestone Celebrations**: Special messages for reaching streak milestones
- **Persistent Tracking**: Streaks are saved and maintained across sessions

### Poll System

Comprehensive polling system for server engagement:

#### Commands
- `/poll <question> <options> [duration]` - Create a poll with multiple options
- `/vote <poll_id> <option_number>` - Vote on a poll
- `/pollresults <poll_id>` - View poll results with progress bars
- `/endpoll <poll_id>` - End a poll early (creator only)
- `/listpolls` - List active polls in the current channel

#### Features
- **Multiple Options**: Up to 10 options per poll
- **Custom Duration**: Set poll duration (default 24h, max 7 days)
- **Real-time Results**: View results with visual progress bars and percentages
- **Creator Control**: Poll creators can end polls early
- **Persistent Storage**: Polls are saved and persist across bot restarts
- **Channel-specific**: Polls are organized by channel

#### How It Works
1. Create a poll with `/poll "What's for lunch?" "Pizza,Burger,Sushi" 2h`
2. Users vote with `/vote <poll_id> <option_number>`
3. View results anytime with `/pollresults <poll_id>`
4. Results show vote counts, percentages, and visual progress bars
5. Polls automatically end after the set duration

### Auto-Moderation System

Advanced chat protection with multiple detection methods:

#### Features
- **Spam Detection**: Detects rapid message sending (3+ messages in 10 seconds)
- **Caps Lock Detection**: Detects excessive caps (70%+ uppercase letters)
- **Emoji Spam Protection**: Detects excessive emoji usage (50%+ emojis)
- **Link Filtering**: Blocks unauthorized links with whitelist support
- **Word Filter**: Blocks inappropriate language (configurable)

#### Admin Commands
- `/automod <feature> <on/off>` - Configure auto-moderation features
  - Features: `spam`, `caps`, `emoji`, `links`
- `/alloweddomains <domains>` - Set allowed domains for link filtering
- `/automodstatus` - View current auto-moderation settings
- `/autodetect <on/off>` - Enable/disable word filtering

#### Configuration
- **Guild-specific**: Each server can configure features independently
- **Flexible Thresholds**: Adjustable detection sensitivity
- **Whitelist Support**: Allow specific domains for link filtering
- **Automatic Actions**: Messages are automatically deleted with user notifications

#### How It Works
1. Admins enable features with `/automod spam on`
2. Set allowed domains with `/alloweddomains discord.com,youtube.com`
3. Bot automatically monitors messages and takes action
4. Users receive notifications when their messages are removed
5. View current settings with `/automodstatus`

## 🚀 Setup

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token
- Discord.py library

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/rence141/hanuko-bot.git
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
   DEFAULT_PREFIX = "!"
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
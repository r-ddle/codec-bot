#  MGS Discord Bot - Refactored Architecture

A Metal Gear Solid-themed Discord bot with XP-based ranking system, now with clean, modular architecture and **cloud database backup**.

## ✨ New Features

- 🌐 **Neon PostgreSQL** integration for cloud data backup
- 🚀 **24/7 hosting ready** - Deploy to Railway, Render, or Oracle Cloud
- 💾 **Automatic data sync** - Never lose member progress
- 📊 **Database commands** - `!neon_backup`, `!neon_status`

## 🚀 Quick Start

### Easy Installation (Windows)

```powershell
.\setup.ps1
```

### Manual Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your tokens:
#   - DISCORD_TOKEN (required)
#   - NEON_DATABASE_URL (optional, recommended)
```

3. Run the bot:
```bash
cd src
python bot.py
```

## ☁️ Cloud Deployment

See **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for:
- Setting up Neon PostgreSQL (free database)
- Deploying to Railway.app (recommended)
- Alternative free hosting options
- 24/7 uptime solutions

## 📁 Project Structure

```
txrails/
├── .env.example              # Environment template
├── .gitignore                # Git ignore patterns
├── README.md                 # This file
├── MIGRATION_GUIDE.md        # Migration instructions
├── requirements.txt          # Python dependencies
├── member_data.json          # Bot database (generated)
└── src/                      # Source code
    ├── bot.py                # Main entry point - starts the bot
    ├── config/               # Configuration & constants
    settings.py           # Environment variables & bot settings
    constants.py          # MGS ranks, rewards, tactical words
 core/                     # Bot core logic
    bot_instance.py       # MGSBot class with task loops
 database/                 # Data persistence layer
    member_data.py        # MemberData class for JSON storage
 utils/                    # Utility functions
    formatters.py         # Number formatting, progress bars
    rank_system.py        # Rank calculations
    role_manager.py       # Discord role management
 cogs/                     # Command modules
    progression.py        # gmp, rank, leaderboard, daily
    info.py               # codec, help, info, tactical_test
    moderation.py         # kick, ban, clear
    admin.py              # test_promotion, auto_promote, etc.
    intel.py              # news/intel commands
    slash_commands.py     # /ping, /status
 events/                   # Event handlers
    member_events.py      # on_ready, on_member_join
    message_events.py     # on_message, XP rewards
    reaction_events.py    # on_reaction_add, on_command_error
 requirements.txt          # Python dependencies
 .env.example              # Environment template
```

##  Features

### Progression System
- **XP-based ranking** with automatic Discord role assignment
- **GMP currency** for stats and activities
- **Tactical word detection** for bonus XP
- **Daily bonuses** with cooldown system
- **Leaderboards** by XP, GMP, messages, and tactical words

### Commands

#### Basic Commands
- `!gmp` - Check your status, rank, and progression
- `!rank [@user]` - View rank information
- `!daily` - Claim daily bonus
- `!leaderboard [category]` - View server rankings
- `!codec` - Interactive MGS codec conversation
- `!tactical_test` - Test tactical word detection
- `!help` - Complete command manual
- `!info` - Quick command reference

#### Moderation Commands
- `!kick <user> [reason]` - Remove a member
- `!ban <user> [reason]` - Ban a member
- `!clear <amount>` - Delete messages (1-100)

#### Admin Commands
- `!test_promotion [@user]` - Test promotion system
- `!auto_promote` - Auto-assign roles based on XP
- `!fix_all_roles` - Sync roles with database
- `!check_roles` - Verify required roles exist

#### Slash Commands
- `/ping` - Test bot connection
- `/status` - Check your status (ephemeral)

##  Rank System

| Rank | Required XP | Discord Role |
|------|-------------|--------------|
| Rookie | 0 | None |
| Private | 100 | Private |
| Specialist | 200 | Specialist |
| Corporal | 350 | Corporal |
| Sergeant | 500 | Sergeant |
| Lieutenant | 750 | Lieutenant |
| Captain | 1,000 | Captain |
| Major | 1,500 | Major |
| Colonel | 2,500 | Colonel |
| FOXHOUND | 4,000 | FOXHOUND |

### How to Earn XP

-  Send messages: **+3 XP** (30s cooldown)
-  Voice activity: **+2 XP/minute**
-  Give reactions: **+1 XP**
-  Receive reactions: **+2 XP**
-  Daily bonus: **+50 XP**
-  Tactical words: **+8 XP each** (up to 10 per message)

##  Development

### Adding New Commands

1. Create or edit a cog in `cogs/`:
```python
from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='mycommand')
    async def my_command(self, ctx):
        await ctx.send("Hello!")

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

2. The cog is automatically loaded by `bot.py`

### Adding New Events

1. Create or edit an event handler in `events/`:
```python
from discord.ext import commands

class MyEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_my_event(self, ...):
        # Handle event
        pass

async def setup(bot):
    await bot.add_cog(MyEvents(bot))
```

##  Database

Member data is stored in `member_data.json` with automatic backups:
- Atomic writes to prevent corruption
- Automatic backup before each save
- Scheduled auto-save every 5 minutes
- Backup every 12 hours

**Data Structure:**
```json
{
  "guild_id": {
    "member_id": {
      "gmp": 1000,
      "xp": 0,
      "rank": "Rookie",
      "messages_sent": 0,
      "voice_minutes": 0,
      "reactions_given": 0,
      "reactions_received": 0,
      "total_tactical_words": 0,
      "last_daily": null,
      "last_message_time": 0,
      "verified": false
    }
  }
}
```

##  Permissions Required

- **Read Messages/View Channels**
- **Send Messages**
- **Embed Links**
- **Add Reactions**
- **Manage Roles** (for rank system)
- **Kick Members** (for moderation)
- **Ban Members** (for moderation)
- **Manage Messages** (for clear command)

##  Environment Variables

```env
# Required
DISCORD_TOKEN=your_discord_bot_token_here

# Optional
NEWS_API_KEY=your_news_api_key_here
WELCOME_CHANNEL_ID=channel_id_for_welcome_messages
```

##  Benefits of New Architecture

 **Modularity** - Each feature in its own file
 **Maintainability** - Easy to find and fix issues
 **Scalability** - Add new features without touching existing code
 **Testability** - Can test individual components
 **Collaboration** - Multiple developers can work simultaneously
✅ **Type Safety** - Comprehensive type hints throughout
 **Documentation** - Clear docstrings on all functions

##  License

 2025 MGS Discord Bot. All rights reserved.

##  Credits

- Metal Gear Solid franchise by Konami
- Original bot concept and design
- Refactored architecture for production use

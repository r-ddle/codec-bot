# 🎮 TXRails Bot - Quick Reference

## 🚀 Getting Started

### First Time Setup

```powershell
# 1. Clone or download the repository
# 2. Run setup script
.\setup.ps1

# 3. Edit .env file with your Discord token
notepad .env

# 4. Run the bot
cd src
python bot.py
```

---

## 📊 Database Setup (Optional but Recommended)

### Why Neon?
- ✅ **Free forever** - 10 GB storage
- ✅ **Automatic backups** - Never lose data
- ✅ **24/7 hosting ready** - Required for cloud deployment
- ✅ **No maintenance** - Fully managed

### Quick Setup

1. **Create Account**: Go to [neon.tech](https://neon.tech)
2. **Create Project**: Click "New Project" → Name it "txrails"
3. **Get URL**: Copy connection string from dashboard
4. **Add to .env**:
   ```env
   NEON_DATABASE_URL=postgres://user:pass@host/db?sslmode=require
   ```
5. **Restart Bot**: Bot will auto-connect and backup data

### Database Commands

```
!neon_status    - Check database connection
!neon_backup    - Manually backup all data to cloud
```

---

## 🤖 Bot Commands

### User Commands

```
!gmp              - Check your stats
!rank [@user]     - View rank card
!daily            - Claim daily bonus (24h cooldown)
!leaderboard      - Top 10 by XP
!leaderboard gmp  - Top 10 by GMP
!codec            - Start codec conversation
!help             - List all commands
```

### Admin Commands (Requires Admin Permission)

```
!test_promotion [@user]   - Test rank promotion
!auto_promote             - Mass promote eligible members
!force_promote <@user> <rank> - Force set rank
!manual_backup            - Backup data to JSON
!checkrank                - Show rank distribution
!info                     - Bot information
!neon_status              - Database status
!neon_backup              - Backup to cloud
```

### Moderation Commands (Requires Permissions)

```
!kick <@user> [reason]    - Kick member
!ban <@user> [reason]     - Ban member
!clear <amount>           - Delete messages
```

---

## 🎖️ Rank System

### How XP Works

- **Messages**: 3 XP per message (30s cooldown)
- **Tactical Words**: 2 XP per word (max 10/message)
- **Reactions**: 1 XP per reaction
- **Voice**: 5 XP per minute (active only)
- **Daily Bonus**: 20 XP + 100 GMP

### Tactical Words (Bonus XP)

Words like: `tactical`, `espionage`, `stealth`, `infiltration`, `boss`, `snake`, `metal gear`, and more!

### Rank Progression

```
Rookie        → 0 XP
Soldier       → 50 XP
Elite Soldier → 150 XP
Sergeant      → 300 XP
Lieutenant    → 500 XP
Captain       → 800 XP
Major         → 1,200 XP
Colonel       → 1,800 XP
Big Boss      → 2,500 XP
The Boss      → 5,000 XP
```

---

## ☁️ Deployment Options

### Option 1: Railway.app (Easiest)

```
1. Go to railway.app
2. Connect GitHub repo
3. Add environment variables (DISCORD_TOKEN, NEON_DATABASE_URL)
4. Deploy!
```

**Pros**: Easiest setup, $5 free credit (20 days 24/7)
**Cons**: Limited free tier

### Option 2: Render.com (Free 24/7)

```
1. Go to render.com
2. Create "Background Worker"
3. Add environment variables
4. Set up keep-alive with UptimeRobot
```

**Pros**: Free 24/7 with keep-alive
**Cons**: Requires keep-alive setup

### Option 3: Oracle Cloud (Advanced)

```
1. Sign up for Oracle Cloud Free Tier
2. Create Ubuntu VM
3. Clone repo and install dependencies
4. Set up systemd service
```

**Pros**: True free forever, powerful VPS
**Cons**: Requires Linux knowledge

**See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions**

---

## 🐛 Troubleshooting

### Bot won't start

```
❌ Check DISCORD_TOKEN is set in .env
❌ Check Python version (3.8+)
❌ Check dependencies installed: pip install -r requirements.txt
```

### Database connection failed

```
❌ Check NEON_DATABASE_URL format
❌ Verify Neon project is active
❌ Ensure ?sslmode=require is at end of URL
```

### Commands not working

```
❌ Check bot has proper permissions in Discord
❌ Check command prefix is ! (exclamation mark)
❌ Try !help to list available commands
```

### Duplicate messages

```
✅ This was fixed! Make sure:
   - tx.py is renamed to tx.py.backup
   - Only bot.py is running
```

---

## 📁 File Structure

```
txrails/
├── .env                    # Your config (don't commit!)
├── .env.example            # Template
├── requirements.txt        # Dependencies
├── setup.ps1              # Setup script
├── README.md              # Full documentation
├── DEPLOYMENT_GUIDE.md    # Hosting guide
└── src/
    ├── bot.py             # Start here
    ├── config/            # Settings
    ├── cogs/              # Commands
    ├── events/            # Event handlers
    ├── database/          # Data storage
    │   ├── member_data.py # JSON handling
    │   └── neon_db.py     # PostgreSQL (cloud)
    └── utils/             # Helper functions
```

---

## 📞 Support

### Common Issues

1. **"Module not found"** → Run `pip install -r requirements.txt`
2. **"Token is invalid"** → Check DISCORD_TOKEN in .env
3. **"Permission denied"** → Bot needs admin role in Discord
4. **"Database error"** → Neon URL might be wrong

### Logs

Check `src/bot.log` for detailed error messages.

---

## 🎯 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Ran `.\setup.ps1` or `pip install -r requirements.txt`
- [ ] Created Discord bot at discord.com/developers
- [ ] Added DISCORD_TOKEN to .env
- [ ] (Optional) Created Neon database
- [ ] (Optional) Added NEON_DATABASE_URL to .env
- [ ] Ran `cd src; python bot.py`
- [ ] Bot shows online in Discord
- [ ] Tested with `!help` command

---

## 📚 Additional Resources

- **Full Documentation**: README.md
- **Deployment Guide**: DEPLOYMENT_GUIDE.md
- **Migration Guide**: MIGRATION_GUIDE.md
- **Discord Developer Portal**: https://discord.com/developers
- **Neon Database**: https://neon.tech
- **Railway Hosting**: https://railway.app

---

**Need help? Check the logs in `src/bot.log` or review the documentation!** 🚀

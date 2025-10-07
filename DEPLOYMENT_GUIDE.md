# 🚀 Deployment Guide - Free 24/7 Hosting Options

This guide covers setting up Neon PostgreSQL and deploying your Discord bot to free 24/7 hosting platforms.

---

## 📊 Part 1: Setting Up Neon PostgreSQL Database

### Step 1: Create Neon Account

1. Go to [neon.tech](https://neon.tech)
2. Sign up with GitHub (free tier includes):
   - **10 GB storage**
   - **Unlimited read/write operations**
   - **Always-on database**
   - **Automatic backups**

### Step 2: Create Database

1. Click "**New Project**"
2. Name it: `txrails-discord-bot`
3. Select region closest to your hosting (US East recommended)
4. Wait for database creation (~30 seconds)

### Step 3: Get Connection String

1. In your Neon dashboard, click on your project
2. Go to "**Connection Details**"
3. Copy the connection string (looks like):
   ```
   postgres://username:password@ep-xxx-xxx.region.aws.neon.tech/dbname?sslmode=require
   ```

### Step 4: Add to .env File

Add this to your `.env` file:

```env
# Neon PostgreSQL Database
NEON_DATABASE_URL=postgres://your_connection_string_here

# Discord Bot Token
DISCORD_TOKEN=your_token_here

# Optional: News API
NEWS_API_KEY=your_news_api_key

# Welcome Channel
WELCOME_CHANNEL_ID=your_channel_id
```

### Step 5: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 6: Test Connection

Run the bot locally to test Neon connection:

```powershell
cd src
python bot.py
```

You should see:
```
✅ Connected to Neon PostgreSQL database
📊 Database schema initialized
✅ Backed up X members from Y guild(s) to Neon
```

---

## 🌐 Part 2: Free 24/7 Hosting Options

### Option 1: **Railway.app** (RECOMMENDED) ⭐

**Pros:**
- ✅ $5 free credit monthly (500 hours = ~20 days 24/7)
- ✅ GitHub integration (auto-deploy)
- ✅ Built-in logs and monitoring
- ✅ Easy environment variables
- ✅ No restrictions on Discord bots

**Cons:**
- ⚠️ Credit runs out after ~20 days
- ⚠️ Requires credit card for verification (not charged)

**Setup:**

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "**New Project**" → "**Deploy from GitHub repo**"
4. Select your `txrails` repository
5. Add environment variables:
   - `DISCORD_TOKEN`
   - `NEON_DATABASE_URL`
   - `NEWS_API_KEY`
   - `WELCOME_CHANNEL_ID`
6. Add start command:
   ```
   cd src && python bot.py
   ```
7. Deploy! ✅

---

### Option 2: **Render.com** (Good Alternative)

**Pros:**
- ✅ Free tier (750 hours/month = 24/7)
- ✅ GitHub integration
- ✅ No credit card required
- ✅ Built-in health checks

**Cons:**
- ⚠️ Sleeps after 15 minutes of inactivity
- ⚠️ Need to keep bot "awake" with health checks

**Setup:**

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "**New**" → "**Background Worker**"
4. Connect your repository
5. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd src && python bot.py`
6. Add environment variables
7. Deploy!

**Keep-Alive Solution:**
Create a simple HTTP endpoint in your bot to prevent sleeping:

```python
# Add to bot.py
from aiohttp import web

async def health_check(request):
    return web.Response(text="Bot is alive!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
    await site.start()
```

Then use [UptimeRobot](https://uptimerobot.com) (free) to ping your health endpoint every 5 minutes.

---

### Option 3: **Fly.io**

**Pros:**
- ✅ Free tier with 3 VMs
- ✅ Always-on (no sleeping)
- ✅ Good for small bots

**Cons:**
- ⚠️ Limited to 160 GB bandwidth/month
- ⚠️ Requires credit card
- ⚠️ More complex setup

**Setup:**

1. Install Fly CLI: [fly.io/docs/hands-on/install-flyctl](https://fly.io/docs/hands-on/install-flyctl/)
2. Run: `fly launch`
3. Follow prompts
4. Set secrets:
   ```bash
   fly secrets set DISCORD_TOKEN=your_token
   fly secrets set NEON_DATABASE_URL=your_neon_url
   ```
5. Deploy: `fly deploy`

---

### Option 4: **Oracle Cloud (Free Tier)** - Advanced

**Pros:**
- ✅ ACTUALLY free forever
- ✅ 2 AMD VMs or 4 ARM VMs
- ✅ 200 GB storage
- ✅ No time limits
- ✅ Full VPS control

**Cons:**
- ⚠️ More complex setup (Linux server)
- ⚠️ Requires credit card verification
- ⚠️ Accounts sometimes get suspended

**Quick Setup:**

1. Sign up at [oracle.com/cloud/free](https://www.oracle.com/cloud/free/)
2. Create a VM instance (Ubuntu)
3. SSH into server
4. Install Python & dependencies:
   ```bash
   sudo apt update
   sudo apt install python3-pip git
   git clone https://github.com/yourusername/txrails.git
   cd txrails
   pip3 install -r requirements.txt
   ```
5. Create `.env` file with your tokens
6. Run with systemd (keeps bot running):
   ```bash
   sudo nano /etc/systemd/system/txrails.service
   ```

   Add:
   ```ini
   [Unit]
   Description=TXRails Discord Bot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/txrails/src
   ExecStart=/usr/bin/python3 bot.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. Enable and start:
   ```bash
   sudo systemctl enable txrails
   sudo systemctl start txrails
   ```

---

### Option 5: **Discloud.app** (Discord Bot Specific)

**Pros:**
- ✅ Free forever
- ✅ Specifically for Discord bots
- ✅ Simple setup

**Cons:**
- ⚠️ 512 MB RAM limit
- ⚠️ Sometimes unstable

**Setup:**

1. Go to [discloud.app](https://discloud.app)
2. Create `discloud.config`:
   ```json
   {
     "TYPE": "bot",
     "MAIN": "src/bot.py",
     "RAM": "512",
     "AUTORESTART": true,
     "VERSION": "recommended",
     "APT": "tools"
   }
   ```
3. Upload files
4. Add environment variables
5. Deploy!

---

## 🔄 Comparison Table

| Platform | Cost | Uptime | Setup | RAM | Best For |
|----------|------|--------|-------|-----|----------|
| **Railway** | $5/mo free | ~20 days | ⭐⭐⭐⭐⭐ | 512 MB | Best overall |
| **Render** | Free | 24/7* | ⭐⭐⭐⭐ | 512 MB | With keep-alive |
| **Fly.io** | Free | 24/7 | ⭐⭐⭐ | 256 MB | Small bots |
| **Oracle** | Free forever | 24/7 | ⭐⭐ | 1-24 GB | Advanced users |
| **Discloud** | Free | 24/7 | ⭐⭐⭐⭐ | 512 MB | Discord-specific |

*With keep-alive solution

---

## 📝 Recommendation

### For Beginners:
**Railway.app** - Easiest setup, good free tier, perfect for learning

### For 24/7 Free:
**Oracle Cloud** - True free forever, but requires Linux knowledge

### For Quick Deploy:
**Render.com** + UptimeRobot - Free and easy with keep-alive

---

## 🛠️ Deployment Checklist

- [ ] Created Neon database account
- [ ] Got Neon connection string
- [ ] Added `NEON_DATABASE_URL` to `.env`
- [ ] Tested bot locally with Neon
- [ ] Chose hosting platform
- [ ] Created account on hosting platform
- [ ] Connected GitHub repository
- [ ] Added all environment variables
- [ ] Configured build/start commands
- [ ] Deployed bot
- [ ] Verified bot is online in Discord
- [ ] Checked logs for errors
- [ ] Tested commands (`!rank`, `!daily`)
- [ ] Verified data is syncing to Neon

---

## 🆘 Troubleshooting

### Bot crashes on startup:
```
Check DISCORD_TOKEN is correct
Check NEON_DATABASE_URL is correct
Check all dependencies installed
```

### Database connection fails:
```
Verify Neon project is active
Check connection string has ?sslmode=require
Test connection locally first
```

### Bot goes offline:
```
Railway: Check if credit ran out
Render: Set up keep-alive
Oracle: Check systemd service status
```

---

## 📞 Support

If you encounter issues:
1. Check logs in your hosting platform
2. Verify environment variables are set
3. Test locally first
4. Check Neon dashboard for connection stats

---

## 🎉 Next Steps

Once deployed:
- Monitor your bot in Discord
- Check Neon dashboard for database usage
- Set up monitoring alerts
- Consider upgrading to paid tier for longer uptime

**Your bot is now running 24/7 with cloud database backup! 🚀**

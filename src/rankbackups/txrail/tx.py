import discord
from discord.ext import tasks, commands
import requests
import asyncio
import os
from collections import defaultdict, deque
import datetime
from dotenv import load_dotenv
import random
import json
import re
from datetime import datetime, timedelta
import logging
import time

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('mgs_bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID')) if os.getenv('WELCOME_CHANNEL_ID') else None
DATABASE_FILE = 'member_data.json'

# MGS-themed messages
MGS_QUOTES = [
    "Kept you waiting, huh?",
    "Snake? Snake?! SNAAAAKE!",
    "I'm no hero. Never was, never will be.",
    "Metal Gear?!",
    "War has changed...",
    "Nanomachines, son!",
    "This is good... isn't it?"
]

MGS_CODEC_SOUNDS = [
    "*codec ring*",
    "*codec beep*",
    "*codec static*",
]

# Anti-Raid Configuration
ANTI_RAID_CONFIG = {
    "join_threshold": 5,
    "join_window": 60,
    "lockdown_duration": 300,
    "max_account_age_hours": 24,
    "auto_kick_new_accounts": True,
    "verification_level_on_raid": discord.VerificationLevel.high,
    "log_channel_name": "security-logs"
}

# Security tracking
class SecurityTracker:
    def __init__(self):
        self.recent_joins = deque(maxlen=50)
        self.raid_mode = False
        self.raid_start_time = None
        self.kicked_users = set()
        
    def add_join(self, member):
        join_data = {
            'user_id': member.id,
            'username': member.name,
            'account_created': member.created_at,
            'join_time': datetime.utcnow()
        }
        self.recent_joins.append(join_data)
        
    def check_raid_pattern(self):
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=ANTI_RAID_CONFIG["join_window"])
        recent_count = sum(1 for join in self.recent_joins 
                          if join['join_time'] >= window_start)
        return recent_count >= ANTI_RAID_CONFIG["join_threshold"]
    
    def check_suspicious_account(self, member):
        account_age = datetime.utcnow() - member.created_at
        hours_old = account_age.total_seconds() / 3600
        
        suspicious_factors = []
        if hours_old < ANTI_RAID_CONFIG["max_account_age_hours"]:
            suspicious_factors.append("new_account")
        if not member.avatar:
            suspicious_factors.append("no_avatar")
        if re.match(r'^[a-zA-Z]+\d{3,}$', member.name):
            suspicious_factors.append("numeric_pattern")
            
        return suspicious_factors

security_tracker = SecurityTracker()

# MGS Ranks system
MGS_RANKS = [
    {"name": "Rookie", "required_gmp": 0, "required_xp": 0, "icon": "🔰", "prefix": ""},
    {"name": "Private", "required_gmp": 1000, "required_xp": 100, "icon": "⭐", "prefix": "| Pvt "},
    {"name": "Corporal", "required_gmp": 2500, "required_xp": 250, "icon": "⭐⭐", "prefix": "| Cpl "},
    {"name": "Sergeant", "required_gmp": 5000, "required_xp": 500, "icon": "⭐⭐⭐", "prefix": "| Sgt "},
    {"name": "Lieutenant", "required_gmp": 10000, "required_xp": 1000, "icon": "🥉", "prefix": "| Lt "},
    {"name": "Captain", "required_gmp": 20000, "required_xp": 2000, "icon": "🥈", "prefix": "| Cpt "},
    {"name": "Major", "required_gmp": 40000, "required_xp": 4000, "icon": "🥇", "prefix": "| Maj "},
    {"name": "Lieutenant Colonel", "required_gmp": 75000, "required_xp": 7500, "icon": "🏅", "prefix": "| Lt.Col "},
    {"name": "Colonel", "required_gmp": 150000, "required_xp": 15000, "icon": "💎", "prefix": "| Col "},
    {"name": "FOXHOUND", "required_gmp": 300000, "required_xp": 30000, "icon": "🦊", "prefix": "| FOX "}
]

# Activity rewards
ACTIVITY_REWARDS = {
    "message": {"gmp": 10, "xp": 2},
    "voice_minute": {"gmp": 5, "xp": 1},
    "reaction": {"gmp": 2, "xp": 0.5},
    "reaction_received": {"gmp": 5, "xp": 1},
    "daily_bonus": {"gmp": 100, "xp": 20},
    "tactical_word": {"gmp": 15, "xp": 5}
}

# Tactical vocabulary
TACTICAL_WORDS = [
    "tactical", "stealth", "operation", "infiltrate", "extract", "intel", 
    "recon", "mission", "target", "objective", "deploy", "enemy", "patrol",
    "metal gear", "foxhound", "shadow moses", "outer heaven", "snake",
    "ocelot", "motherbase", "phantom pain", "peace walker", "mg", "mgs",
    "nanomachines", "revolver", "diamond dogs", "boss", "tactic", 
    "espionage", "alert", "caution", "silencer", "weapon", "gear", "military"
]

def format_number(number):
    return f"{number:,}"

def make_progress_bar(current, maximum, length=10):
    current = min(current, maximum)
    percentage = int((current / maximum) * 100) if maximum > 0 else 100
    filled = int((current / maximum) * length) if maximum > 0 else length
    empty = length - filled
    bar = ''.join(['■' for _ in range(filled)] + ['□' for _ in range(empty)])
    return f"[{bar}] {percentage}%"

def get_rank_data_by_name(rank_name):
    for rank in MGS_RANKS:
        if rank["name"] == rank_name:
            return rank
    return MGS_RANKS[0]

def extract_original_name(nickname):
    if not nickname:
        return nickname
    if nickname.startswith('|'):
        parts = nickname.split('|', 2)
        if len(parts) >= 3:
            return parts[2].strip()
        elif len(parts) == 2:
            return parts[1].strip()
    return nickname

def create_ranked_nickname(original_name, rank_name):
    rank_data = get_rank_data_by_name(rank_name)
    if rank_name == "Rookie":
        return original_name
    
    prefix = rank_data['prefix']
    max_name_length = 32 - len(prefix)
    if len(original_name) > max_name_length:
        original_name = original_name[:max_name_length-3] + "..."
    
    return f"{prefix}{original_name}"

class MemberData:
    def __init__(self):
        self.data = self.load_data()
        self.last_activity = defaultdict(lambda: defaultdict(int))
        self._save_lock = asyncio.Lock()

    def load_data(self):
        try:
            if os.path.exists(DATABASE_FILE):
                with open(DATABASE_FILE, 'r') as f:
                    data = json.load(f)
                    return data if data else {}
            return {}
        except Exception as e:
            logger.error(f"Error loading member data: {e}")
            return {}

    async def save_data_async(self):
        async with self._save_lock:
            try:
                with open(DATABASE_FILE, 'w') as f:
                    json.dump(self.data, f, indent=2)
            except Exception as e:
                logger.error(f"Error saving member data: {e}")

    def get_member_data(self, member_id):
        str_id = str(member_id)
        
        default_member = {
            "gmp": 1000,
            "xp": 0,
            "rank": "Rookie",
            "rank_icon": "🔰",
            "messages_sent": 0,
            "voice_minutes": 0,
            "reactions_given": 0,
            "reactions_received": 0,
            "last_daily": None,
            "tactical_words_used": 0,
            "original_name": None,
            "verified": False,
            "security_flags": []
        }
        
        if str_id not in self.data:
            self.data[str_id] = default_member.copy()
            return self.data[str_id]
        
        # Handle existing members - check for missing fields
        for key, value in default_member.items():
            if key not in self.data[str_id]:
                if key == "rank_icon":
                    current_rank = self.data[str_id].get("rank", "Rookie")
                    icon = next((r["icon"] for r in MGS_RANKS if r["name"] == current_rank), "🔰")
                    self.data[str_id][key] = icon
                else:
                    self.data[str_id][key] = value
        
        return self.data[str_id]

    def update_member(self, member_id, gmp_change=0, xp_change=0, activity_type=None):
        str_id = str(member_id)
        member_data = self.get_member_data(str_id)
        
        # Update activity stats
        if activity_type:
            if activity_type == "message":
                member_data["messages_sent"] += 1
            elif activity_type == "voice_minute":
                member_data["voice_minutes"] += 1
            elif activity_type == "reaction":
                member_data["reactions_given"] += 1
            elif activity_type == "reaction_received":
                member_data["reactions_received"] += 1
            elif activity_type == "tactical_word":
                member_data["tactical_words_used"] = member_data.get("tactical_words_used", 0) + 1
        
        # Update GMP with minimum balance check
        new_gmp = member_data["gmp"] + gmp_change
        member_data["gmp"] = max(0, new_gmp)
        
        # Update XP
        member_data["xp"] += xp_change
        
        # Check for rank increase
        old_rank = member_data["rank"]
        new_rank, new_icon = self.calculate_rank(member_data["gmp"], member_data["xp"])
        
        member_data["rank"] = new_rank
        member_data["rank_icon"] = new_icon
        
        return new_rank != old_rank, new_rank

    def calculate_rank(self, gmp, xp):
        current_rank = MGS_RANKS[0]["name"]
        current_icon = MGS_RANKS[0]["icon"]
        
        for rank_data in MGS_RANKS:
            if gmp >= rank_data["required_gmp"] and xp >= rank_data["required_xp"]:
                current_rank = rank_data["name"]
                current_icon = rank_data["icon"]
            else:
                break
                
        return current_rank, current_icon

    def get_next_rank_info(self, member_id):
        member_data = self.get_member_data(member_id)
        current_rank = member_data["rank"]
        
        current_index = 0
        for i, rank_data in enumerate(MGS_RANKS):
            if rank_data["name"] == current_rank:
                current_index = i
                break
        
        if current_index >= len(MGS_RANKS) - 1:
            return None
        
        next_rank = MGS_RANKS[current_index + 1]
        current_rank_data = MGS_RANKS[current_index]
        
        return {
            "name": next_rank["name"],
            "icon": next_rank["icon"],
            "gmp_needed": max(0, next_rank["required_gmp"] - member_data["gmp"]),
            "xp_needed": max(0, next_rank["required_xp"] - member_data["xp"]),
            "current_gmp": member_data["gmp"],
            "current_xp": member_data["xp"],
            "next_gmp": next_rank["required_gmp"],
            "next_xp": next_rank["required_xp"],
            "current_rank_gmp": current_rank_data["required_gmp"],
            "current_rank_xp": current_rank_data["required_xp"]
        }

    def award_daily_bonus(self, member_id):
        member_data = self.get_member_data(member_id)
        today = datetime.now().strftime('%Y-%m-%d')
        
        if member_data["last_daily"] != today:
            member_data["last_daily"] = today
            
            gmp_bonus = ACTIVITY_REWARDS["daily_bonus"]["gmp"]
            xp_bonus = ACTIVITY_REWARDS["daily_bonus"]["xp"]
            
            rank_up, new_rank = self.update_member(member_id, gmp_change=gmp_bonus, xp_change=xp_bonus)
            
            return True, gmp_bonus, xp_bonus, rank_up, new_rank
        
        return False, 0, 0, False, None

    def award_activity_reward(self, member_id, activity_type):
        if activity_type not in ACTIVITY_REWARDS:
            return 0, 0, False, None
        
        reward = ACTIVITY_REWARDS[activity_type]
        rank_up, new_rank = self.update_member(
            member_id, 
            gmp_change=reward["gmp"], 
            xp_change=reward["xp"], 
            activity_type=activity_type
        )
        
        return reward["gmp"], reward["xp"], rank_up, new_rank

    def get_leaderboard(self, sort_by="gmp", limit=10):
        valid_sort_options = ["gmp", "xp", "tactical_words_used", "messages_sent"]
        if sort_by not in valid_sort_options:
            sort_by = "gmp"
            
        sorted_members = sorted(
            self.data.items(),
            key=lambda x: x[1].get(sort_by, 0),
            reverse=True
        )
        
        return sorted_members[:limit]

    def store_original_name(self, member_id, original_name):
        str_id = str(member_id)
        member_data = self.get_member_data(str_id)
        if not member_data.get("original_name"):
            member_data["original_name"] = original_name

    def get_original_name(self, member_id):
        str_id = str(member_id)
        member_data = self.get_member_data(str_id)
        return member_data.get("original_name")

    def mark_member_verified(self, member_id):
        str_id = str(member_id)
        member_data = self.get_member_data(str_id)
        member_data["verified"] = True

    def add_security_flag(self, member_id, flag):
        str_id = str(member_id)
        member_data = self.get_member_data(str_id)
        if "security_flags" not in member_data:
            member_data["security_flags"] = []
        if flag not in member_data["security_flags"]:
            member_data["security_flags"].append(flag)

class MGSBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
        self.member_data = MemberData()
        self.polls = defaultdict(dict)
        self.remove_command('help')
        
    async def setup_hook(self):
        # Start background tasks here
        self.check_alerts.start()
        self.track_voice_activity.start()
        self.backup_data.start()
        self.security_monitor.start()
        
        try:
            await self.tree.sync()
            logger.info("Slash commands synced successfully")
        except Exception as e:
            logger.error(f"Error syncing slash commands: {e}")

    @tasks.loop(minutes=30)
    async def check_alerts(self):
        """Simulates random codec calls"""
        for guild in self.guilds:
            if random.random() < 0.3:  # 30% chance
                general = discord.utils.get(guild.text_channels, name='general')
                if general:
                    sound = random.choice(MGS_CODEC_SOUNDS)
                    quote = random.choice(MGS_QUOTES)
                    await general.send(f"{sound}\nColonel: {quote}")

    @tasks.loop(minutes=5)
    async def track_voice_activity(self):
        for guild in self.guilds:
            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    if member.bot:
                        continue
                    if not member.voice.self_deaf and not member.voice.self_mute:
                        self.member_data.award_activity_reward(member.id, "voice_minute")
    
    @tasks.loop(hours=6)
    async def backup_data(self):
        await self.member_data.save_data_async()

    @tasks.loop(seconds=30)
    async def security_monitor(self):
        if security_tracker.raid_mode and security_tracker.raid_start_time:
            elapsed = datetime.utcnow() - security_tracker.raid_start_time
            if elapsed.total_seconds() >= ANTI_RAID_CONFIG["lockdown_duration"]:
                for guild in self.guilds:
                    await self.deactivate_raid_mode(guild)

    def check_tactical_words(self, message_content):
        count = 0
        lower_content = message_content.lower()
        
        for word in TACTICAL_WORDS:
            if re.search(r'\b' + re.escape(word) + r'\b', lower_content):
                count += 1
                
        return count

    async def get_security_log_channel(self, guild):
        channel = discord.utils.get(guild.text_channels, name=ANTI_RAID_CONFIG["log_channel_name"])
        if not channel:
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                for role in guild.roles:
                    if role.permissions.administrator:
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True)
                        
                channel = await guild.create_text_channel(
                    ANTI_RAID_CONFIG["log_channel_name"],
                    overwrites=overwrites,
                    topic="🛡️ Security logs and anti-raid monitoring"
                )
            except Exception as e:
                logger.error(f"Error creating security log channel: {e}")
                return None
        return channel

    async def log_security_event(self, guild, embed):
        channel = await self.get_security_log_channel(guild)
        if channel:
            try:
                await channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Error sending security log: {e}")

    async def activate_raid_mode(self, guild):
        if security_tracker.raid_mode:
            return
            
        security_tracker.raid_mode = True
        security_tracker.raid_start_time = datetime.utcnow()
        
        try:
            embed = discord.Embed(
                title="🚨 RAID PROTECTION ACTIVATED",
                description="```\nSECURITY PROTOCOL: ACTIVE\nTHREAT LEVEL: HIGH\nDEFENSIVE MEASURES: DEPLOYED\n```",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            await self.log_security_event(guild, embed)
            
        except Exception as e:
            logger.error(f"Error activating raid mode: {e}")

    async def deactivate_raid_mode(self, guild):
        if not security_tracker.raid_mode:
            return
            
        security_tracker.raid_mode = False
        
        try:
            embed = discord.Embed(
                title="✅ RAID PROTECTION DEACTIVATED",
                description="```\nSECURITY PROTOCOL: NORMAL\nTHREAT LEVEL: LOW\nSTATUS: ALL CLEAR\n```",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await self.log_security_event(guild, embed)
            security_tracker.kicked_users.clear()
            
        except Exception as e:
            logger.error(f"Error deactivating raid mode: {e}")

    async def handle_suspicious_member(self, member, suspicious_factors):
        guild = member.guild
        
        embed = discord.Embed(
            title="⚠️ SUSPICIOUS ACCOUNT DETECTED",
            description=f"**User:** {member.mention}\n**ID:** {member.id}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="SUSPICIOUS FACTORS",
            value=f"```\n{', '.join(suspicious_factors).replace('_', ' ').title()}\n```",
            inline=False
        )
        
        action_taken = "Monitoring"
        
        if security_tracker.raid_mode and ANTI_RAID_CONFIG["auto_kick_new_accounts"]:
            if "new_account" in suspicious_factors and len(suspicious_factors) >= 2:
                try:
                    await member.kick(reason="Auto-kick: Suspicious account during raid")
                    security_tracker.kicked_users.add(member.id)
                    action_taken = "Kicked (Auto)"
                    embed.color = discord.Color.red()
                    self.member_data.add_security_flag(member.id, "auto_kicked_raid")
                except Exception as e:
                    logger.error(f"Error kicking suspicious member: {e}")
                    action_taken = "Kick Failed"
        
        embed.add_field(name="ACTION TAKEN", value=f"```\n{action_taken}\n```", inline=True)
        await self.log_security_event(guild, embed)
        return action_taken

    async def update_member_nickname(self, member, new_rank):
        try:
            if member.guild_permissions.administrator or member.id == member.guild.owner_id:
                return False

            if not member.guild.me.guild_permissions.manage_nicknames:
                return False

            original_name = self.member_data.get_original_name(member.id)
            if not original_name:
                display_name = member.display_name or member.name
                original_name = extract_original_name(display_name)
                self.member_data.store_original_name(member.id, original_name)

            new_nickname = create_ranked_nickname(original_name, new_rank)
            
            if len(new_nickname) > 32:
                max_original_length = 32 - len(get_rank_data_by_name(new_rank)["prefix"])
                truncated_name = original_name[:max_original_length-3] + "..."
                new_nickname = create_ranked_nickname(truncated_name, new_rank)
            
            if member.display_name != new_nickname:
                await member.edit(nick=new_nickname, reason=f"Rank promotion to {new_rank}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating nickname for {member.name}: {e}")
            return False

bot = MGSBot()

@bot.event
async def on_ready():
    """Enhanced ready event with better logging"""
    print(f"✅ {bot.user} is now online and ready!")
    print(f"🏗️ Connected to {len(bot.guilds)} guilds")
    
    # List all connected guilds
    for guild in bot.guilds:
        print(f"   - {guild.name} (ID: {guild.id}) - {guild.member_count} members")
    
    # Check welcome channel configuration
    if WELCOME_CHANNEL_ID:
        print(f"📬 Welcome channel ID configured: {WELCOME_CHANNEL_ID}")
        # Try to verify the channel exists
        channel_found = False
        for guild in bot.guilds:
            channel = guild.get_channel(WELCOME_CHANNEL_ID)
            if channel:
                print(f"✅ Welcome channel found: #{channel.name} in {guild.name}")
                # Check permissions
                perms = channel.permissions_for(guild.me)
                print(f"   - Send Messages: {'✅' if perms.send_messages else '❌'}")
                print(f"   - Embed Links: {'✅' if perms.embed_links else '❌'}")
                channel_found = True
                break
        
        if not channel_found:
            print(f"⚠️ Welcome channel {WELCOME_CHANNEL_ID} not found in any guild!")
            print("   Available text channels:")
            for guild in bot.guilds:
                for channel in guild.text_channels[:5]:  # Show first 5 channels
                    print(f"   - #{channel.name} (ID: {channel.id}) in {guild.name}")
    else:
        print("⚠️ WELCOME_CHANNEL_ID not configured!")
        print("   Set WELCOME_CHANNEL_ID in your .env file")
    
    print("🚀 Bot is fully ready and operational!")

# FIXED MEMBER JOIN EVENT - SIMPLIFIED AND ROBUST
@bot.event
async def on_member_join(member):
    """Simplified and robust member join handler"""
    print(f"🎖️ NEW MEMBER JOINED: {member.name} (ID: {member.id}) in {member.guild.name}")
    
    try:
        # Security checks first
        security_tracker.add_join(member)
        if security_tracker.check_raid_pattern():
            await bot.activate_raid_mode(member.guild)
        
        suspicious_factors = security_tracker.check_suspicious_account(member)
        if suspicious_factors and security_tracker.raid_mode:
            action = await bot.handle_suspicious_member(member, suspicious_factors)
            if "Kicked" in action:
                print(f"❌ Member {member.name} was kicked for security reasons")
                return
        
        # Initialize member data
        bot.member_data.get_member_data(member.id)
        bot.member_data.store_original_name(member.id, member.display_name or member.name)
        bot.member_data.mark_member_verified(member.id)
        
        # Find welcome channel - TRY MULTIPLE METHODS
        welcome_channel = None
        
        # Method 1: Use configured channel ID
        if WELCOME_CHANNEL_ID:
            welcome_channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
            if welcome_channel:
                print(f"✅ Using configured welcome channel: #{welcome_channel.name}")
        
        # Method 2: Find channel named 'welcome' or 'general'
        if not welcome_channel:
            for channel_name in ['welcome', 'general', 'main', 'chat']:
                welcome_channel = discord.utils.get(member.guild.text_channels, name=channel_name)
                if welcome_channel:
                    print(f"✅ Found welcome channel by name: #{welcome_channel.name}")
                    break
        
        # Method 3: Use the first channel bot can write to
        if not welcome_channel:
            for channel in member.guild.text_channels:
                if channel.permissions_for(member.guild.me).send_messages and channel.permissions_for(member.guild.me).embed_links:
                    welcome_channel = channel
                    print(f"✅ Using first available channel: #{welcome_channel.name}")
                    break
        
        if not welcome_channel:
            print(f"❌ No suitable welcome channel found in {member.guild.name}")
            return
        
        # Create MGS-themed welcome embed
        security_status = "🔒 RAID MODE" if security_tracker.raid_mode else "🟢 SECURE"
        alert_emoji = "🚨" if security_tracker.raid_mode else "🟢"
        
        embed = discord.Embed(
            title="CONNECTION ESTABLISHED",
            color=0x5865F2
        )
        
        embed.description = f"""```
> SYSTEM BOOT...
> FOX-HOUND TACTICAL DATABASE
> ACCESS GRANTED

> NEW OPERATIVE DETECTED
> CODENAME: {member.display_name}
> ACCESS GRANTED
```"""
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        welcome_content = f"""```
╔═══════════════════════════════════╗
  WELCOME TO TACTICAL OPERATIONS!
╚═══════════════════════════════════╝

> OPERATIVE STATUS: ACTIVE
> GMP BALANCE: 1000 
> STARTING RANK: 🔰 ROOKIE
> SECURITY LEVEL: {security_status}

📡 Type !info for command list and
mission details
```"""
        
        embed.add_field(
            name="MOTHER BASE WELCOMES YOU",
            value=welcome_content,
            inline=False
        )
        
        if security_tracker.raid_mode:
            embed.add_field(
                name="🚨 SECURITY NOTICE",
                value="```\nMother Base is currently under enhanced security.\nPlease be patient as our systems verify your credentials.\n```",
                inline=False
            )
        
        embed.set_image(url="https://images-ext-1.discordapp.net/external/znqAGtNjrN09-n-59N5jJGCNJSBIJwYB31d8qzAzXYI/https/media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExdzVqMTFjZXNyZWh6cDA3eGc3YjJuMmUxdjl0Yml6cnhobjlxZzZrMyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/CacxhprRlavR0AveWN/giphy.gif?width=960&height=540")
        
        embed.set_footer(text=f"Joined Mother Base: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # Send welcome message
        announcement = f"{alert_emoji} **ATTENTION ALL PERSONNEL** {alert_emoji}\nNew operative has entered Mother Base: {member.mention}"
        
        await welcome_channel.send(content=announcement, embed=embed)
        print(f"✅ Welcome message sent to #{welcome_channel.name} for {member.name}")
        
        # Save data
        await bot.member_data.save_data_async()
        
    except Exception as e:
        print(f"❌ Error in welcome system: {e}")
        import traceback
        traceback.print_exc()



@bot.event
async def on_message(message):
    await bot.process_commands(message)
    
    if message.author.bot:
        return
        
    member_id = message.author.id
    current_time = datetime.now()
    
    # Only award points if it's been more than a minute since last message
    last_msg_time = bot.member_data.last_activity[member_id].get("message", 0)
    if current_time.timestamp() - last_msg_time > 60:
        # Base message reward
        gmp, xp, rank_up, new_rank = bot.member_data.award_activity_reward(member_id, "message")
        
        # Check for tactical words and award bonus
        tactical_count = bot.check_tactical_words(message.content)
        if tactical_count > 0:
            for _ in range(min(tactical_count, 5)):
                t_gmp, t_xp, t_rank_up, t_new_rank = bot.member_data.award_activity_reward(
                    member_id, "tactical_word"
                )
                if t_rank_up:
                    rank_up = True
                    new_rank = t_new_rank
        
        # Handle rank up with nickname update
        if rank_up:
            try:
                nickname_updated = await bot.update_member_nickname(message.author, new_rank)
                
                embed = discord.Embed(
                    title="🎖️ RANK PROMOTION",
                    description=f"```\n[ PROMOTION NOTICE ]\nOPERATIVE: {message.author.display_name}\nNEW RANK: {new_rank}\n```",
                    color=0x599cff
                )
                
                if message.author.avatar:
                    embed.set_thumbnail(url=message.author.avatar.url)
                    
                embed.add_field(
                    name="COMMANDER MESSAGE",
                    value=f"Excellent work, {message.author.mention}. Your performance has been recognized by high command.",
                    inline=False
                )
                
                if nickname_updated:
                    embed.add_field(
                        name="NICKNAME UPDATED",
                        value="```\nYour callsign has been updated to reflect your new rank.\n```",
                        inline=False
                    )
                
                await message.channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Error sending rank up message: {e}")
        
        bot.member_data.last_activity[member_id]["message"] = current_time.timestamp()

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
        
    giver_id = user.id
    bot.member_data.award_activity_reward(giver_id, "reaction")
    
    if not reaction.message.author.bot and reaction.message.author.id != user.id:
        receiver_id = reaction.message.author.id
        bot.member_data.award_activity_reward(receiver_id, "reaction_received")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❗ You don't have the security clearance for this operation!")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❓ Unknown codec frequency")
    else:
        await ctx.send("❗ An error occurred.")

# YOUR ORIGINAL COMMANDS
@bot.command(name='codec')
async def codec(ctx):
    """Simulates MGS codec conversation"""
    messages = [
        "*codec ring*",
        "Snake, do you copy?",
        f"I read you, {ctx.author.name}.",
        "Here's your mission briefing...",
    ]
    
    msg = await ctx.send(messages[0])
    for i in range(1, len(messages)):
        await asyncio.sleep(1.5)
        await msg.edit(content='\n'.join(messages[:i+1]))

@bot.command(name='intel')
async def intel(ctx):
    """Get latest news as intelligence reports"""
    try:
        params = {
            'apiKey': NEWS_API_KEY,
            'country': 'us',
            'pageSize': 3
        }
        response = requests.get('https://newsapi.org/v2/top-headlines', params=params)
        news = response.json().get('articles', [])
        
        if not news:
            await ctx.send("❗ No intel available at this time.")
            return

        intel_report = discord.Embed(
            title="⚠ INTEL REPORT ⚠",
            color=discord.Color.red()
        )
        
        for i, article in enumerate(news, 1):
            intel_report.add_field(
                name=f"Intel #{i}",
                value=f"```{article['title']}```\n[Read more]({article['url']})",
                inline=False
            )
            
        await ctx.send(embed=intel_report)
    except Exception as e:
        await ctx.send("❗ Intel retrieval failed")

@bot.command(name='alert')
@commands.has_permissions(administrator=True)
async def alert(ctx, *, message):
    """Send an alert in MGS style"""
    alert_msg = f"""
```
!!!!!!!!! ALERT !!!!!!!!!!

{message}

########################
```
"""
    await ctx.send(alert_msg)

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 3):
    """Clear messages in any channel"""
    try:
        deleted = await ctx.channel.purge(limit=amount)
        confirmation = await ctx.send(f"🧹 Cleared {len(deleted)} messages in {ctx.channel.mention}")
        # Delete the confirmation message after 5 seconds
        await confirmation.delete(delay=5)
    except Exception as e:
        error_msg = await ctx.send(f"❌ An error occurred while clearing messages: {str(e)}")
        await error_msg.delete(delay=5)

# FIXED KICK COMMAND WITH GIF
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """Kick a member with MGS-style message and DM"""
    if member is None:
        await ctx.send("❌ Please specify a member to kick!")
        return
    
    # Check if user can be kicked
    if member == ctx.author:
        await ctx.send("❌ You cannot kick yourself!")
        return
    
    if member.guild_permissions.administrator:
        await ctx.send("❌ Cannot kick administrators!")
        return
    
    if member.top_role >= ctx.guild.me.top_role:
        await ctx.send("❌ Cannot kick this member - they have higher or equal role!")
        return
    
    kick_gif_url = "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHloYzl5dDc0bGV6MzEyMHIxdjB3OWljZjh3eXhxeHhkYml4dThwdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/nA3kAfPuPQmFn57qIk/giphy.gif"
    
    try:
        # Send DM to the user first (before they get kicked)
        dm_sent = False
        try:
            dm_embed = discord.Embed(
                title="🚨 EXTRACTION NOTICE",
                description=f"```\n> MISSION STATUS: TERMINATED\n> OPERATIVE EXTRACTED FROM MOTHER BASE\n> SERVER: {ctx.guild.name}\n> OPERATOR: {ctx.author.name}\n```",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            if reason:
                dm_embed.add_field(
                    name="EXTRACTION REASON",
                    value=f"```\n{reason}\n```",
                    inline=False
                )
            else:
                dm_embed.add_field(
                    name="EXTRACTION REASON",
                    value="```\nNo specific reason provided\n```",
                    inline=False
                )
            
            dm_embed.add_field(
                name="COMMANDER MESSAGE",
                value="```\nYour mission at Mother Base has been terminated.\nContact command if you believe this is an error.\n```",
                inline=False
            )
            
            dm_embed.set_image(url=kick_gif_url)
            dm_embed.set_footer(text=f"Extracted from {ctx.guild.name}")
            
            await member.send(embed=dm_embed)
            dm_sent = True
            print(f"✅ DM sent to {member.name}")
            
        except discord.Forbidden:
            print(f"❌ Cannot send DM to {member.name} - DMs disabled")
            dm_sent = False
        except Exception as e:
            print(f"❌ Error sending DM to {member.name}: {e}")
            dm_sent = False
        
        # Kick the member
        kick_reason = f"Kicked by {ctx.author.name}" + (f" - {reason}" if reason else "")
        await member.kick(reason=kick_reason)
        print(f"✅ Successfully kicked {member.name}")
        
        # Send public embed with GIF
        public_embed = discord.Embed(
            title="🚨 OPERATIVE EXTRACTED",
            description=f"```\n> EXTRACTION COMPLETE\n> TARGET: {member.name}#{member.discriminator}\n> USER ID: {member.id}\n> STATUS: REMOVED FROM MOTHER BASE\n```",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        if reason:
            public_embed.add_field(
                name="EXTRACTION REASON",
                value=f"```\n{reason}\n```",
                inline=False
            )
        else:
            public_embed.add_field(
                name="EXTRACTION REASON",
                value="```\nNo specific reason provided\n```",
                inline=False
            )
        
        public_embed.add_field(
            name="OPERATION DETAILS",
            value=f"```\nExtracted by: {ctx.author.display_name}\nDM Notification: {'✅ Sent' if dm_sent else '❌ Failed'}\nTime: {datetime.utcnow().strftime('%H:%M:%S')} UTC\n```",
            inline=False
        )
        
        public_embed.set_image(url=kick_gif_url)
        public_embed.set_footer(text="Mother Base security protocol executed successfully")
        
        await ctx.send(embed=public_embed)
        print(f"✅ Kick message sent to #{ctx.channel.name}")
        
    except discord.Forbidden:
        await ctx.send("❌ **OPERATION FAILED**: I don't have permission to kick this member!")
    except discord.HTTPException as e:
        await ctx.send(f"❌ **EXTRACTION FAILED**: {str(e)}")
    except Exception as e:
        await ctx.send(f"❌ **UNEXPECTED ERROR**: {str(e)}")
        print(f"❌ Error in kick command: {e}")
        import traceback
        traceback.print_exc()

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"⚠ {member.name} has been marked as an enemy combatant and eliminated!")

# GMP SYSTEM COMMANDS
@bot.command(name='gmp')
async def gmp(ctx):
    """Check GMP balance, rank, and stats"""
    member_id = ctx.author.id
    member_data = bot.member_data.get_member_data(member_id)
    
    next_rank = bot.member_data.get_next_rank_info(member_id)
    
    embed = discord.Embed(
        title=f"{member_data.get('rank_icon', '🔰')} GMP & RANK STATUS",
        description="```\n> ACCESSING PERSONNEL FILE\n> DATA RETRIEVAL COMPLETE\n```",
        color=0x599cff
    )
    
    if ctx.author.avatar:
        embed.set_thumbnail(url=ctx.author.avatar.url)
    
    embed.add_field(
        name="IDENTITY",
        value=f"```\nOPERATIVE: {ctx.author.display_name}\nRANK: {member_data['rank']}\nSTATUS: {'VERIFIED' if member_data.get('verified', False) else 'UNVERIFIED'}\n```",
        inline=False
    )
    
    embed.add_field(
        name="GMP BALANCE",
        value=f"```\n{format_number(member_data['gmp'])} GMP\n```",
        inline=True
    )
    
    embed.add_field(
        name="EXPERIENCE",
        value=f"```\n{format_number(member_data['xp'])} XP\n```",
        inline=True
    )
    
    embed.add_field(
        name="ACTIVITY RECORDS",
        value=f"```\nMessages: {format_number(member_data['messages_sent'])}\nVoice: {format_number(member_data['voice_minutes'])} min\nTactical Words: {format_number(member_data.get('tactical_words_used', 0))}\n```",
        inline=False
    )
    
    if next_rank:
        gmp_progress = member_data["gmp"] - next_rank["current_rank_gmp"]
        xp_progress = member_data["xp"] - next_rank["current_rank_xp"]
        
        gmp_total = next_rank["next_gmp"] - next_rank["current_rank_gmp"]
        xp_total = next_rank["next_xp"] - next_rank["current_rank_xp"]
        
        gmp_bar = make_progress_bar(gmp_progress, gmp_total)
        xp_bar = make_progress_bar(xp_progress, xp_total)
        
        rank_text = f"```\nRANK: {member_data['rank']} {member_data['rank_icon']}\n"
        rank_text += f"GMP: {format_number(member_data['gmp'])} / {format_number(next_rank['next_gmp'])} {gmp_bar}\n"
        rank_text += f"XP:  {format_number(member_data['xp'])} / {format_number(next_rank['next_xp'])} {xp_bar}\n```"
        
        embed.add_field(
            name=f"NEXT RANK: {next_rank['icon']} {next_rank['name']}",
            value=rank_text,
            inline=False
        )
    else:
        embed.add_field(
            name="MAXIMUM RANK ACHIEVED",
            value="```\nYou've reached the highest rank, FOXHOUND operative.\n```",
            inline=False
        )
    
    embed.set_footer(text=f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
@bot.command(name='debug_welcome')
@commands.has_permissions(administrator=True)
async def debug_welcome(ctx):
    """Debug welcome system configuration"""
    embed = discord.Embed(title="🔧 WELCOME SYSTEM DEBUG", color=0x599cff)
    
    # Check current configuration
    config_text = f"```\nWELCOME_CHANNEL_ID: {WELCOME_CHANNEL_ID}\n"
    config_text += f"Bot User: {bot.user.name}#{bot.user.discriminator}\n"
    config_text += f"Guild: {ctx.guild.name} (ID: {ctx.guild.id})\n"
    config_text += f"Member Count: {ctx.guild.member_count}\n"
    config_text += "```"
    
    embed.add_field(name="CONFIGURATION", value=config_text, inline=False)
    
    # Check welcome channel status
    if WELCOME_CHANNEL_ID:
        channel = ctx.guild.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            perms = channel.permissions_for(ctx.guild.me)
            channel_status = f"```\nChannel: #{channel.name}\n"
            channel_status += f"Type: {channel.type}\n"
            channel_status += f"Send Messages: {'✅' if perms.send_messages else '❌'}\n"
            channel_status += f"Embed Links: {'✅' if perms.embed_links else '❌'}\n"
            channel_status += f"View Channel: {'✅' if perms.view_channel else '❌'}\n"
            channel_status += "```"
            embed.add_field(name="WELCOME CHANNEL STATUS", value=channel_status, inline=False)
        else:
            embed.add_field(name="WELCOME CHANNEL STATUS", value="```\n❌ CHANNEL NOT FOUND\n```", inline=False)
    else:
        embed.add_field(name="WELCOME CHANNEL STATUS", value="```\n⚠️ NOT CONFIGURED\n```", inline=False)
    
    # Test recommendations
    recommendations = "```\n"
    if not WELCOME_CHANNEL_ID:
        recommendations += "1. Set welcome channel: !set_welcome #channel\n"
    recommendations += "2. Test welcome system: !test_welcome\n"
    recommendations += "3. Check channels: !debug_channels\n"
    recommendations += "4. Check bot intents and permissions\n"
    recommendations += "```"
    
    embed.add_field(name="RECOMMENDATIONS", value=recommendations, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='daily')
async def daily(ctx):
    """Claim daily GMP and XP bonus"""
    member_id = ctx.author.id
    
    success, gmp, xp, rank_up, new_rank = bot.member_data.award_daily_bonus(member_id)
    
    if success:
        embed = discord.Embed(
            title="📦 SUPPLY DROP RECEIVED",
            description="```\n> MOTHER BASE LOGISTICS\n> DAILY SUPPLY DROP DELIVERED\n> STATUS: COMPLETE\n```",
            color=0x599cff
        )
        
        embed.add_field(
            name="SUPPLIES RECEIVED",
            value=f"```\n[+] {format_number(gmp)} GMP\n[+] {format_number(xp)} XP\n```",
            inline=False
        )
        
        if rank_up:
            nickname_updated = await bot.update_member_nickname(ctx.author, new_rank)
            
            embed.add_field(
                name="🎖️ PROMOTION AUTHORIZED",
                value=f"```\n[ ! ] NEW RANK: {new_rank}\n```",
                inline=False
            )
            
            if nickname_updated:
                embed.add_field(
                    name="NICKNAME UPDATED",
                    value="```\nYour callsign has been updated to reflect your new rank.\n```",
                    inline=False
                )
        
        embed.set_footer(text="Return tomorrow for another supply drop.")
        await ctx.send(embed=embed)
        
        # Save data after successful daily claim
        await bot.member_data.save_data_async()
    else:
        embed = discord.Embed(
            title="❌ SUPPLY DROP UNAVAILABLE",
            description="```\n> MOTHER BASE LOGISTICS\n> DAILY SUPPLY DROP REQUEST\n> STATUS: REJECTED\n```",
            color=discord.Color.red()
        )
        
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time_left = tomorrow - now
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds // 60) % 60
        
        embed.add_field(
            name="⚠️ CAUTION",
            value=f"```\nSupplies already claimed today.\nNext drop available in {hours:02d}:{minutes:02d}.\n```",
            inline=False
        )
        
        await ctx.send(embed=embed)

@bot.command(name='rank')
async def rank(ctx, member: discord.Member = None):
    """Check your or another member's rank"""
    if member is None:
        member = ctx.author
    
    if member.bot:
        await ctx.send("```\n⚠️ CAUTION\nCombat units are for humans only.\n```")
        return
    
    member_id = member.id
    member_data = bot.member_data.get_member_data(member_id)
    next_rank = bot.member_data.get_next_rank_info(member_id)
    
    embed = discord.Embed(
        title=f"{member_data.get('rank_icon', '🔰')} OPERATIVE STATUS",
        description="```\n> ACCESSING PERSONNEL FILE\n> OPERATIVE ID: {}\n```".format(member_id),
        color=0x599cff
    )
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    rank_display = f"```\nOPERATIVE: {member.display_name}\n"
    
    if next_rank:
        gmp_progress = member_data["gmp"] - next_rank["current_rank_gmp"]
        xp_progress = member_data["xp"] - next_rank["current_rank_xp"]
        
        gmp_total = next_rank["next_gmp"] - next_rank["current_rank_gmp"]
        xp_total = next_rank["next_xp"] - next_rank["current_rank_xp"]
        
        gmp_bar = make_progress_bar(gmp_progress, gmp_total)
        xp_bar = make_progress_bar(xp_progress, xp_total)
        
        rank_display += f"RANK: {member_data['rank']} {member_data['rank_icon']}\n"
        rank_display += f"GMP: {format_number(member_data['gmp'])} / {format_number(next_rank['next_gmp'])} {gmp_bar}\n"
        rank_display += f"XP:  {format_number(member_data['xp'])} / {format_number(next_rank['next_xp'])} {xp_bar}\n\n"
        rank_display += f"NEXT RANK: {next_rank['name']} {next_rank['icon']}\n"
    else:
        rank_display += f"RANK: {member_data['rank']} {member_data['rank_icon']}\n"
        rank_display += f"GMP: {format_number(member_data['gmp'])}\n"
        rank_display += f"XP:  {format_number(member_data['xp'])}\n\n"
        rank_display += "MAXIMUM RANK ACHIEVED\n"
    
    rank_display += "```"
    
    embed.add_field(name="PERSONNEL DATA", value=rank_display, inline=False)
    
    activity_text = f"```\n"
    activity_text += f"Messages Sent: {format_number(member_data['messages_sent'])}\n"
    activity_text += f"Voice Minutes: {format_number(member_data['voice_minutes'])}\n"
    activity_text += f"Tactical Words: {format_number(member_data.get('tactical_words_used', 0))}\n"
    
    if ctx.author.guild_permissions.administrator:
        security_flags = member_data.get('security_flags', [])
        activity_text += f"Security Flags: {len(security_flags)}\n"
        activity_text += f"Verified: {'Yes' if member_data.get('verified', False) else 'No'}\n"
    
    activity_text += "```"
    
    embed.add_field(name="ACTIVITY RECORD", value=activity_text, inline=False)
    embed.set_footer(text=f"Data retrieved at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    await ctx.send(embed=embed)

@bot.command(name='leaderboard', aliases=['lb'])
async def leaderboard(ctx, category: str = "gmp"):
    """View server leaderboard by different categories"""
    valid_categories = {
        "gmp": "GMP Ranking",
        "xp": "Experience Points",
        "tactical": "Tactical Vocabulary",
        "messages": "Messages Sent"
    }
    
    category_mapping = {
        "gmp": "gmp",
        "xp": "xp",
        "tactical": "tactical_words_used",
        "messages": "messages_sent"
    }
    
    if category.lower() not in category_mapping:
        category = "gmp"
    
    sort_field = category_mapping[category.lower()]
    title = valid_categories[category.lower()]
    
    leaderboard_data = bot.member_data.get_leaderboard(sort_by=sort_field, limit=10)
    
    embed = discord.Embed(
        title=f"🏆 FOX-HOUND LEADERBOARD: {title.upper()}",
        description="```\n> PERSONNEL RANKING SYSTEM\n> CATEGORY: {}\n```".format(title.upper()),
        color=0x599cff
    )
    
    if not leaderboard_data:
        embed.add_field(name="⚠️ CAUTION", value="```\nNo operatives have records yet.\n```")
        await ctx.send(embed=embed)
        return
    
    leaderboard_text = "```\n"
    for i, (member_id, data) in enumerate(leaderboard_data, 1):
        try:
            member = ctx.guild.get_member(int(member_id))
            name = member.display_name if member else f"Unknown Operative ({member_id})"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            value = data.get(sort_field, 0)
            rank_icon = data.get("rank_icon", "🔰")
            
            leaderboard_text += f"{medal} {name} - {format_number(value)} {category.upper()}\n"
            leaderboard_text += f"   Rank: {data['rank']} {rank_icon}\n\n"
        except Exception as e:
            logger.error(f"Error processing leaderboard entry: {e}")
            continue
    
    leaderboard_text += "```"
    embed.add_field(name="[ TOP OPERATIVES ]", value=leaderboard_text, inline=False)
    
    categories_help = "**View other categories:**\n"
    for cat, name in valid_categories.items():
        categories_help += f"`!leaderboard {cat}` - {name}\n"
    
    embed.add_field(name="[ AVAILABLE FILTERS ]", value=categories_help, inline=False)
    embed.set_footer(text=f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Type !rank to see your status")
    
    await ctx.send(embed=embed)

@bot.command(name='info')
async def info(ctx):
    """Display comprehensive information about available commands"""
    embed = discord.Embed(
        title="📡 TACTICAL OPERATIONS CENTER",
        description="```\n> COMMAND SYSTEM ACCESS GRANTED\n> SECURITY STATUS: {}\n```".format('🔒 RAID MODE' if security_tracker.raid_mode else '🟢 SECURE'),
        color=0x599cff if not security_tracker.raid_mode else discord.Color.orange()
    )
    
    # Basic Commands
    embed.add_field(
        name="🔰 BASIC COMMANDS",
        value="""```
!codec   - Open codec menu
!intel   - Get latest intel
!gmp     - Check GMP balance and rank
!daily   - Claim daily bonus
!rank    - View detailed rank status
!leaderboard - View the top operatives
```""",
        inline=False
    )
    
    # Utility Commands
    embed.add_field(
        name="🛠 UTILITY OPERATIONS",
        value="""```
!info   - Show this command list
!clear <number> - Delete messages (Moderator+)
```""",
        inline=False
    )
    
    # Moderator Commands
    if ctx.author.guild_permissions.kick_members:
        embed.add_field(
            name="🛡️ MODERATOR OPERATIONS",
            value="""```
!kick <user>    - Remove personnel
!ban <user>     - Eliminate hostile elements
!alert <message> - Send priority alert (Admin)
```""",
            inline=False
        )
    
    # How to earn GMP/XP
    embed.add_field(
        name="💎 EARNING GMP & XP",
        value="""```
📝 Send messages        +10 GMP, +2 XP
🎤 Voice activity       +5 GMP, +1 XP per minute
👍 Give reactions       +2 GMP, +0.5 XP
❤️ Receive reactions    +5 GMP, +1 XP
📦 Daily bonus          +100 GMP, +20 XP
🎯 Use tactical words   +15 GMP, +5 XP each
```""",
        inline=False
    )
    
    embed.set_footer(text="🛡️ Anti-Raid Protection Active | Stay Alert, Comrade!")
    await ctx.send(embed=embed)

# NEWS COMMANDS (Enhanced Intel System)
COUNTRY_DOMAINS = {
    'au': 'abc.net.au,news.com.au',
    'in': 'timesofindia.indiatimes.com,ndtv.com',
    'us': 'cnn.com,reuters.com',
    'de': 'dw.com,spiegel.de'
}

async def get_news_with_backup(country_code, max_retries=3):
    """Get news with fallback methods"""
    news_articles = []
    
    try:
        params = {
            'apiKey': NEWS_API_KEY,
            'country': country_code,
            'pageSize': 5,
            'language': 'en'
        }
        response = requests.get('https://newsapi.org/v2/top-headlines', params=params, timeout=10)
        if response.status_code == 200:
            news = response.json().get('articles', [])
            if news:
                news_articles.extend(news)
    except Exception as e:
        logger.error(f"Error in news query: {e}")

    if not news_articles and country_code in COUNTRY_DOMAINS:
        try:
            params = {
                'apiKey': NEWS_API_KEY,
                'domains': COUNTRY_DOMAINS[country_code],
                'pageSize': 5,
                'language': 'en',
                'sortBy': 'publishedAt'
            }
            response = requests.get('https://newsapi.org/v2/everything', params=params, timeout=10)
            if response.status_code == 200:
                news = response.json().get('articles', [])
                if news:
                    news_articles.extend(news)
        except Exception as e:
            logger.error(f"Error in domain-specific query: {e}")
    
    # Deduplicate articles by title
    seen_titles = set()
    unique_articles = []
    for article in news_articles:
        title = article.get('title', '')
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_articles.append(article)
    
    return unique_articles[:5]

async def fetch_country_news(ctx, country_code: str, title: str):
    """Enhanced news fetching with backup sources"""
    status_message = None
    try:
        status_message = await ctx.send("```\n> Accessing intelligence networks...\n```")
        
        flag_emoji = {
            'de': '🇩🇪',
            'us': '🇺🇸',
            'in': '🇮🇳',
            'au': '🇦🇺'
        }.get(country_code, '🌐')
        
        news_articles = await get_news_with_backup(country_code)
        
        if not news_articles:
            if status_message:
                await status_message.edit(content="```\n❗ No intel available from this region at this time.\n```")
            return

        embed = discord.Embed(
            title=f"{flag_emoji} {title} {flag_emoji}",
            description="Here's the latest intel from the region, Comrade.",
            color=0x599cff
        )

        for i, article in enumerate(news_articles, 1):
            date = article.get('publishedAt', '').split('T')[0]
            title = article.get('title', 'No title available').replace('\n', ' ').strip()
            source = article.get('source', {}).get('name', 'Unknown Source')
            
            field_name = f"INTEL #{i} - {source} ({date})"
            
            description = article.get('description', 'No description available').replace('\n', ' ').strip()
            value = f"```\n{title}\n```\n{description[:150]}...\n[Full Report]({article.get('url', '')})"
            
            embed.add_field(name=field_name, value=value, inline=False)

        embed.set_footer(text=f"Intel updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        if status_message:
            await status_message.delete()
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        if status_message:
            await status_message.edit(content="```\n❗ Intel retrieval failed: Network error detected\n```")

@bot.command(name='news_au')
async def news_au(ctx):
    """Get latest news from Australia"""
    await fetch_country_news(ctx, 'au', 'AUSTRALIAN INTEL REPORT')

@bot.command(name='news_in')
async def news_in(ctx):
    """Get latest news from India"""
    await fetch_country_news(ctx, 'in', 'INDIAN INTEL REPORT')

@bot.command(name='news_us')
async def news_us(ctx):
    """Get latest news from United States"""
    await fetch_country_news(ctx, 'us', 'US INTEL REPORT')

@bot.command(name='news_de')
async def news_de(ctx):
    """Get latest news from Germany"""
    await fetch_country_news(ctx, 'de', 'GERMAN INTEL REPORT')

# SLASH COMMANDS
@bot.tree.command(name="ping", description="Verify communications with headquarters")
async def ping(interaction: discord.Interaction):
    embed = discord.Embed(
        title="CODEC CONNECTION TEST",
        description="```\nCodec connection stable.\nFrequency: 140.85 MHz\n```",
        color=0x599cff
    )
    
    embed.add_field(
        name="CONNECTION STATUS",
        value=f"```\nLatency: {round(bot.latency * 1000)}ms\nSignal: Strong\nSecurity: {'🔒 RAID MODE' if security_tracker.raid_mode else '🟢 SECURE'}\n```",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="update", description="Update Active Developer Badge Status")
async def update(interaction: discord.Interaction):
    await interaction.response.send_message("Initiating badge status update...")
    try:
        await asyncio.sleep(2)
        embed = discord.Embed(
            title="🎖️ Active Developer Badge Update",
            description="Status check complete!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Status",
            value="Your Active Developer badge status has been refreshed.\nPlease check the [Active Developer Portal](https://discord.com/developers/active-developer) to see your updated status.",
            inline=False
        )
        await interaction.edit_original_response(content=None, embed=embed)
    except Exception as e:
        logger.error(f"Error in update command: {e}")
        await interaction.edit_original_response(
            content="❌ An error occurred while updating the badge status. Please try again later."
        )

# ADMIN COMMANDS
@bot.command(name='stats')
async def server_stats(ctx):
    """Display comprehensive server statistics"""
    guild = ctx.guild
    
    embed = discord.Embed(
        title="📊 MOTHER BASE INTELLIGENCE REPORT",
        description="```\n> RETRIEVING SERVER DATA\n> ACCESS GRANTED\n> SECURITY STATUS: {}\n```".format('🔒 RAID MODE' if security_tracker.raid_mode else '🟢 SECURE'),
        color=0x599cff if not security_tracker.raid_mode else discord.Color.orange()
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    stats_text = "```\n"
    stats_text += f"OPERATIVES: {guild.member_count}\n"
    stats_text += f"CHANNELS: {len(guild.channels)}\n"
    stats_text += f"ROLES: {len(guild.roles)}\n"
    stats_text += f"BOOST LEVEL: {guild.premium_tier}\n"
    stats_text += "```"
    
    embed.add_field(name="SERVER PARAMETERS", value=stats_text, inline=False)
    
    created_delta = discord.utils.utcnow() - guild.created_at
    years = created_delta.days // 365
    months = (created_delta.days % 365) // 30
    
    time_text = "```\n"
    time_text += f"SERVER AGE: {years} years, {months} months\n"
    time_text += f"CREATED ON: {guild.created_at.strftime('%Y-%m-%d')}\n"
    time_text += f"VERIFICATION: {guild.verification_level.name.upper()}\n"
    time_text += "```"
    
    embed.add_field(name="TIME DATA", value=time_text, inline=False)
    
    # Security statistics for admins
    if ctx.author.guild_permissions.administrator:
        security_text = "```\n"
        security_text += f"Recent Joins: {len(security_tracker.recent_joins)}\n"
        security_text += f"Raid Mode: {'ACTIVE' if security_tracker.raid_mode else 'INACTIVE'}\n"
        security_text += f"Kicked Users: {len(security_tracker.kicked_users)}\n"
        security_text += "```"
        embed.add_field(name="SECURITY STATUS", value=security_text, inline=False)
    
    embed.set_footer(text=f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    await ctx.send(embed=embed)

@bot.command(name='security_status')
@commands.has_permissions(administrator=True)
async def security_status(ctx):
    """Check current security status (Admin only)"""
    embed = discord.Embed(
        title="🛡️ SECURITY STATUS REPORT",
        description="```\n> ACCESSING SECURITY SYSTEMS\n> CLEARANCE: ADMINISTRATOR\n```",
        color=discord.Color.blue()
    )
    
    status_text = f"```\n"
    status_text += f"Raid Mode: {'ACTIVE' if security_tracker.raid_mode else 'INACTIVE'}\n"
    status_text += f"Recent Joins: {len(security_tracker.recent_joins)}\n"
    status_text += f"Verification Level: {ctx.guild.verification_level.name.upper()}\n"
    status_text += f"Kicked Users: {len(security_tracker.kicked_users)}\n"
    status_text += "```"
    
    embed.add_field(name="CURRENT STATUS", value=status_text, inline=False)
    
    config_text = f"```\n"
    config_text += f"Join Threshold: {ANTI_RAID_CONFIG['join_threshold']} per {ANTI_RAID_CONFIG['join_window']}s\n"
    config_text += f"Account Age Filter: {ANTI_RAID_CONFIG['max_account_age_hours']} hours\n"
    config_text += f"Lockdown Duration: {ANTI_RAID_CONFIG['lockdown_duration']} seconds\n"
    config_text += f"Auto-kick New Accounts: {ANTI_RAID_CONFIG['auto_kick_new_accounts']}\n"
    config_text += "```"
    
    embed.add_field(name="CONFIGURATION", value=config_text, inline=False)
    
    if security_tracker.recent_joins:
        recent_text = f"```\n"
        for join in list(security_tracker.recent_joins)[-5:]:
            age_hours = (datetime.utcnow() - join['account_created']).total_seconds() / 3600
            recent_text += f"{join['username']}: {age_hours:.1f}h old\n"
        recent_text += "```"
        embed.add_field(name="RECENT JOINS (Last 5)", value=recent_text, inline=False)
    
    embed.set_footer(text=f"Report generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    await ctx.send(embed=embed)

@bot.command(name='force_raid_mode')
@commands.has_permissions(administrator=True)
async def force_raid_mode(ctx, action: str = None):
    """Manually activate/deactivate raid mode (Admin only)"""
    if action is None:
        await ctx.send("```\nUsage: !force_raid_mode [activate|deactivate]\n```")
        return
    
    action = action.lower()
    
    if action in ['activate', 'on', 'enable']:
        if security_tracker.raid_mode:
            await ctx.send("```\nRaid mode is already active.\n```")
            return
        
        await bot.activate_raid_mode(ctx.guild)
        embed = discord.Embed(
            title="🚨 RAID MODE MANUALLY ACTIVATED",
            description=f"```\n> ADMINISTRATOR OVERRIDE\n> RAID MODE: ACTIVE\n> AUTHORIZED BY: {ctx.author.name}\n```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        
    elif action in ['deactivate', 'off', 'disable']:
        if not security_tracker.raid_mode:
            await ctx.send("```\nRaid mode is not currently active.\n```")
            return
        
        await bot.deactivate_raid_mode(ctx.guild)
        embed = discord.Embed(
            title="✅ RAID MODE MANUALLY DEACTIVATED",
            description=f"```\n> ADMINISTRATOR OVERRIDE\n> RAID MODE: INACTIVE\n> AUTHORIZED BY: {ctx.author.name}\n```",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
    else:
        await ctx.send("```\nInvalid action. Use: activate or deactivate\n```")

@bot.command(name='set_welcome')
@commands.has_permissions(administrator=True)
async def set_welcome(ctx, channel: discord.TextChannel = None):
    """Set or update the welcome channel (Admin only)"""
    if channel is None:
        channel = ctx.channel
    
    global WELCOME_CHANNEL_ID
    WELCOME_CHANNEL_ID = channel.id
    
    embed = discord.Embed(
        title="✅ WELCOME CHANNEL UPDATED",
        description=f"```\n> WELCOME CHANNEL SET TO: #{channel.name}\n> CHANNEL ID: {channel.id}\n> STATUS: ACTIVE\n```",
        color=discord.Color.green()
    )
    
    # Check permissions
    permissions = channel.permissions_for(ctx.guild.me)
    perm_text = f"```\nSend Messages: {'✅' if permissions.send_messages else '❌'}\nEmbed Links: {'✅' if permissions.embed_links else '❌'}\nAttach Files: {'✅' if permissions.attach_files else '❌'}\n```"
    
    embed.add_field(name="PERMISSIONS CHECK", value=perm_text, inline=False)
    
    if not permissions.send_messages or not permissions.embed_links:
        embed.add_field(
            name="⚠️ WARNING",
            value="```\nBot lacks required permissions in this channel!\nPlease ensure the bot has:\n- Send Messages\n- Embed Links\n```",
            inline=False
        )
    
    embed.add_field(
        name="NEXT STEPS",
        value="```\nWelcome channel updated for this session.\nTo make permanent, update your .env file with:\nWELCOME_CHANNEL_ID=" + str(channel.id) + "\nUse !test_welcome to verify functionality\n```",
        inline=False
    )
    
    await ctx.send(embed=embed)

# TEST COMMANDS
@bot.command(name='test_welcome')
@commands.has_permissions(administrator=True)
async def test_welcome(ctx):
    """Test the welcome system"""
    await ctx.send("```\n🧪 TESTING WELCOME SYSTEM\nSimulating member join event...\n```")
    try:
        await bot.on_member_join(ctx.author)
        await ctx.send("```\n✅ Test complete! Check for welcome message above.\n```")
    except Exception as e:
        await ctx.send(f"```\n❌ Test failed: {str(e)}\n```")
        print(f"Test welcome error: {e}")
        import traceback
        traceback.print_exc()

@bot.command(name='debug_channels')
@commands.has_permissions(administrator=True)
async def debug_channels(ctx):
    """Debug channel information"""
    embed = discord.Embed(title="📊 CHANNEL DEBUG INFO", color=0x599cff)
    
    # Show configured welcome channel
    config_info = f"```\nWELCOME_CHANNEL_ID: {WELCOME_CHANNEL_ID}\n"
    if WELCOME_CHANNEL_ID:
        channel = ctx.guild.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            config_info += f"Channel Found: #{channel.name}\n"
            perms = channel.permissions_for(ctx.guild.me)
            config_info += f"Send Messages: {'✅' if perms.send_messages else '❌'}\n"
            config_info += f"Embed Links: {'✅' if perms.embed_links else '❌'}\n"
        else:
            config_info += "Channel Found: ❌ NOT FOUND\n"
    config_info += "```"
    
    embed.add_field(name="CONFIGURED CHANNEL", value=config_info, inline=False)
    
    # Show available channels
    available_channels = "```\n"
    for i, channel in enumerate(ctx.guild.text_channels[:10]):  # Show first 10
        perms = channel.permissions_for(ctx.guild.me)
        status = "✅" if (perms.send_messages and perms.embed_links) else "❌"
        available_channels += f"{status} #{channel.name} (ID: {channel.id})\n"
    available_channels += "```"
    
    embed.add_field(name="AVAILABLE CHANNELS (First 10)", value=available_channels, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='mission')
async def mission(ctx):
    """View current mission objectives"""
    embed = discord.Embed(
        title="📋 CURRENT MISSION OBJECTIVES",
        description="```\n> MISSION BRIEFING\n> CLASSIFICATION: TOP SECRET\n```",
        color=0x599cff
    )
    
    objectives = [
        "🎯 Build Mother Base reputation (+{} GMP/XP per message)".format(ACTIVITY_REWARDS["message"]["gmp"]),
        "🎤 Maintain communication networks (+{} GMP/XP per voice minute)".format(ACTIVITY_REWARDS["voice_minute"]["gmp"]),
        "🤝 Support fellow operatives (+{} GMP/XP per reaction given)".format(ACTIVITY_REWARDS["reaction"]["gmp"]),
        "📦 Collect daily supply drops (+{} GMP/XP daily bonus)".format(ACTIVITY_REWARDS["daily_bonus"]["gmp"]),
        "🎯 Use tactical vocabulary (+{} GMP/XP per tactical word)".format(ACTIVITY_REWARDS["tactical_word"]["gmp"])
    ]
    
    objectives_text = "```\n"
    for i, obj in enumerate(objectives, 1):
        objectives_text += f"{i}. {obj}\n"
    objectives_text += "```"
    
    embed.add_field(name="PRIMARY OBJECTIVES", value=objectives_text, inline=False)
    
    embed.add_field(
        name="TACTICAL VOCABULARY",
        value="```\nUse words like: tactical, stealth, operation, infiltrate, extract, intel, recon, mission, metal gear, mgs, snake, foxhound, and more tactical terms to earn bonus rewards.\n```",
        inline=False
    )
    
    embed.add_field(
        name="MISSION STATUS",
        value="```\n> ONGOING\n> DIFFICULTY: MODERATE\n> REWARDS: ACTIVE\n```",
        inline=False
    )
    
    embed.set_footer(text="Good luck out there, soldier. The fate of Mother Base depends on you.")
    await ctx.send(embed=embed)

# ENHANCED HELP COMMAND
@bot.command(name='help')
async def help_command(ctx):
    """Enhanced help command with categories"""
    embed = discord.Embed(
        title="📡 TACTICAL OPERATIONS CENTER - COMMAND MANUAL",
        description="```\n> COMMAND SYSTEM ACCESS GRANTED\n> SECURITY STATUS: {}\n> TYPE: COMPREHENSIVE MANUAL\n```".format('🔒 RAID MODE' if security_tracker.raid_mode else '🟢 SECURE'),
        color=0x599cff if not security_tracker.raid_mode else discord.Color.orange()
    )
    
    # Basic Operations
    embed.add_field(
        name="🔰 BASIC OPERATIONS",
        value="""```
!codec       - Codec communication test
!intel       - Basic intelligence report (US)
!mission     - View current objectives
!info        - Quick command reference
!help        - This comprehensive manual
```""",
        inline=False
    )
    
    # GMP & Progression System
    embed.add_field(
        name="💰 GMP & PROGRESSION SYSTEM",
        value="""```
!gmp         - Check GMP balance and rank
!daily       - Claim daily supply drop
!rank [@user] - View rank status
!leaderboard [category] - View rankings
  Categories: gmp, xp, tactical, messages
```""",
        inline=False
    )
    
    # Intelligence Network
    embed.add_field(
        name="🌍 INTELLIGENCE NETWORK",
        value="""```
!news_us     - US intelligence reports
!news_au     - Australian intelligence
!news_in     - Indian intelligence  
!news_de     - German intelligence
```""",
        inline=False
    )
    
    # Utility & Server Management
    embed.add_field(
        name="🛠 UTILITY OPERATIONS",
        value="""```
!stats       - Server statistics
!clear <num> - Delete messages (Mod+)
/ping        - Test bot connection (Slash)
/update      - Developer badge update (Slash)
```""",
        inline=False
    )
    
    # Moderation (if user has permissions)
    if ctx.author.guild_permissions.kick_members:
        embed.add_field(
            name="🛡️ MODERATOR OPERATIONS",
            value="""```
!kick <user> [reason]  - Remove personnel
!ban <user> [reason]   - Eliminate threats
!alert <message>       - Priority alert (Admin)
```""",
            inline=False
        )
    
    # Admin Commands (if user is admin)
    if ctx.author.guild_permissions.administrator:
        embed.add_field(
            name="⚠️ ADMINISTRATOR OPERATIONS",
            value="""```
!security_status       - Security report
!force_raid_mode [on/off] - Control raid mode
!set_welcome [#channel] - Set welcome channel
!test_welcome          - Test welcome system
```""",
            inline=False
        )
    
    # Progression Guide
    embed.add_field(
        name="📈 PROGRESSION GUIDE",
        value="""```
RANK UP BY EARNING GMP & XP:
• Send messages (+10 GMP, +2 XP)
• Voice activity (+5 GMP, +1 XP/min)
• Give reactions (+2 GMP, +0.5 XP)
• Receive reactions (+5 GMP, +1 XP) 
• Daily bonus (+100 GMP, +20 XP)
• Tactical words (+15 GMP, +5 XP each)
```""",
        inline=False
    )
    
    embed.add_field(
        name="🎯 PRO TIPS",
        value="""```
• Use tactical vocabulary for bonus rewards
• Participate in voice channels for XP
• Check !mission for current objectives
• Claim !daily bonus every 24 hours
• Support teammates with reactions
• Use !gmp to track your progress
```""",
        inline=False
    )
    
    embed.set_footer(text="🎖️ Remember: Tactical Espionage Action is a team effort, Comrade!")
    await ctx.send(embed=embed)

# Run the bot
def main():
    try:
        if not TOKEN:
            print("❌ CRITICAL ERROR: DISCORD_TOKEN not found!")
            print("Please add DISCORD_TOKEN=your_bot_token to your .env file")
            return
            
        if not WELCOME_CHANNEL_ID:
            print("⚠️ WARNING: WELCOME_CHANNEL_ID not set!")
            print("Add WELCOME_CHANNEL_ID=your_channel_id to your .env file")
        else:
            print(f"✅ Welcome Channel ID loaded: {WELCOME_CHANNEL_ID}")
            
        print("🚀 Starting MGS Discord Bot...")
        bot.run(TOKEN)
    except Exception as e:
        print(f"Mission failed! Error: {e}")

if __name__ == "__main__":
    main()
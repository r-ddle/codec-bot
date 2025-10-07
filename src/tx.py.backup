import discord
from discord.ext import tasks, commands
import requests
import asyncio
import os
from collections import defaultdict
import datetime
from dotenv import load_dotenv
import random
import json
import re
from datetime import datetime, timedelta, timezone
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
    "This is good... isn't it?",
    "A weapon to surpass Metal Gear!",
    "Brother!",
    "You're pretty good.",
    "The future is not some place we are going, but one we are creating."
]

MGS_CODEC_SOUNDS = [
    "*codec ring*",
    "*codec beep*",
    "*codec static*",
]

# Codec conversation responses
CODEC_RESPONSES = [
    "Snake, can you hear me?",
    "This is Colonel Campbell. What's your status?",
    "Stay alert, Snake. Enemy activity detected in your area.",
    "Remember, this is a stealth mission.",
    "Keep your guard up out there.",
    "Good work so far. Continue the mission.",
    "Be careful, Snake. We're counting on you.",
    "That's what I like to hear, soldier.",
    "Mission parameters remain unchanged.",
    "I can talk now well... Let's continue this operation.",
    "Solid copy, Snake. Campbell out."
]

# XP-BASED RANK PROGRESSION SYSTEM
MGS_RANKS = [
    {"name": "Rookie", "required_xp": 0, "icon": "🔰", "role_name": None},
    {"name": "Private", "required_xp": 100, "icon": "⭐", "role_name": "Private"},
    {"name": "Specialist", "required_xp": 200, "icon": "⭐", "role_name": "Specialist"},
    {"name": "Corporal", "required_xp": 350, "icon": "⭐⭐", "role_name": "Corporal"},
    {"name": "Sergeant", "required_xp": 500, "icon": "⭐⭐⭐", "role_name": "Sergeant"},
    {"name": "Lieutenant", "required_xp": 750, "icon": "🥉", "role_name": "Lieutenant"},
    {"name": "Captain", "required_xp": 1000, "icon": "🥈", "role_name": "Captain"},
    {"name": "Major", "required_xp": 1500, "icon": "🥇", "role_name": "Major"},
    {"name": "Colonel", "required_xp": 2500, "icon": "💎", "role_name": "Colonel"},
    {"name": "FOXHOUND", "required_xp": 4000, "icon": "🦊", "role_name": "FOXHOUND"}
]

# Activity rewards
ACTIVITY_REWARDS = {
    "message": {"gmp": 15, "xp": 3},
    "voice_minute": {"gmp": 8, "xp": 2},
    "reaction": {"gmp": 3, "xp": 1},
    "reaction_received": {"gmp": 8, "xp": 2},
    "daily_bonus": {"gmp": 200, "xp": 50},
    "tactical_word": {"gmp": 25, "xp": 8}
}

# Tactical vocabulary for bonus detection
TACTICAL_WORDS = [
    "tactical", "stealth", "operation", "infiltrate", "extract", "intel", 
    "recon", "mission", "target", "objective", "deploy", "enemy", "patrol",
    "metal gear", "foxhound", "shadow moses", "outer heaven", "snake",
    "ocelot", "motherbase", "phantom pain", "peace walker", "mg", "mgs",
    "nanomachines", "revolver", "diamond dogs", "boss", "tactic", 
    "espionage", "alert", "caution", "silencer", "weapon", "gear", "military",
    "soldier", "warfare", "combat", "strategy", "sniper", "assault", "defense",
    "artillery", "ammunition", "camouflage", "surveillance", "reconnaissance",
    "elimination", "extraction", "insertion", "breach", "secure", "hostile",
    "friendly", "neutral", "contact", "engage", "disengage", "retreat",
    "advance", "flank", "cover", "suppression", "overwatch", "backup",
    "reinforcement", "casualty", "wounded", "medic", "evac", "rendezvous",
    "cipher", "patriot", "codec", "operative", "commander",
    "colonel", "major", "captain", "lieutenant", "sergeant", "private"
]

def format_number(number):
    """Format numbers with commas"""
    return f"{number:,}"

def make_progress_bar(current, maximum, length=10):
    """Create progress bar for rank progression"""
    current = min(current, maximum)
    percentage = int((current / maximum) * 100) if maximum > 0 else 100
    filled = int((current / maximum) * length) if maximum > 0 else length
    empty = length - filled
    bar = ''.join(['■' for _ in range(filled)] + ['□' for _ in range(empty)])
    return f"[{bar}] {percentage}%"

def get_rank_data_by_name(rank_name):
    """Get rank data by rank name"""
    for rank in MGS_RANKS:
        if rank["name"] == rank_name:
            return rank
    return MGS_RANKS[0]

def calculate_rank_from_xp(xp):
    """Calculate rank based on XP only"""
    current_rank = MGS_RANKS[0]
    
    # Find the highest rank the user qualifies for based on XP only
    for rank_data in reversed(MGS_RANKS):
        if xp >= rank_data["required_xp"]:
            current_rank = rank_data
            break
    
    return current_rank["name"], current_rank["icon"]

async def update_member_roles(member, new_rank):
    """Update member Discord roles based on rank"""
    try:
        guild = member.guild
        
        # Get the role name for the new rank
        new_role_name = None
        for rank_data in MGS_RANKS:
            if rank_data["name"] == new_rank:
                new_role_name = rank_data["role_name"]
                break
        
        # Get all rank role names for removal
        rank_role_names = [rank["role_name"] for rank in MGS_RANKS if rank["role_name"]]
        roles_to_remove = []
        
        # Find current rank roles to remove
        for role in member.roles:
            if role.name in rank_role_names:
                roles_to_remove.append(role)
        
        # Remove old rank roles
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason="Rank role update")
            logger.info(f"Removed old rank roles from {member.name}")
        
        # Add new role if not Rookie
        if new_role_name:
            new_role = discord.utils.get(guild.roles, name=new_role_name)
            
            if new_role:
                await member.add_roles(new_role, reason=f"Promoted to {new_rank}")
                logger.info(f"Added {new_role_name} role to {member.name}")
                return True
            else:
                logger.error(f"Role '{new_role_name}' not found in server!")
                return False
        else:
            logger.info(f"{member.name} is Rookie - no role assigned")
            return True
            
    except discord.Forbidden:
        logger.error(f"No permission to manage roles for {member.name}")
        return False
    except Exception as e:
        logger.error(f"Error updating roles for {member.name}: {e}")
        return False

class MemberData:
    """Handles all member data storage and progression"""
    def __init__(self):
        self.data = self.load_data()
        self._save_lock = asyncio.Lock()
        self._pending_saves = False
        logger.info(f"Loaded data for {len(self.data)} guild(s)")

    def load_data(self):
        """Load data from JSON file"""
        try:
            if os.path.exists(DATABASE_FILE):
                with open(DATABASE_FILE, 'r') as f:
                    raw_data = json.load(f)
                    
                if not raw_data:
                    logger.info("Empty database file found, starting fresh")
                    return {}
                
                if isinstance(raw_data, dict):
                    guild_like_keys = [k for k in raw_data.keys() if k.isdigit() and len(k) > 10]
                    
                    if guild_like_keys:
                        logger.info(f"Found existing guild data for {len(guild_like_keys)} guild(s)")
                        return raw_data
                    else:
                        logger.info("No valid guild data found in file")
                        return {}
                else:
                    logger.warning("Invalid data format in database file")
                    return {}
            else:
                logger.info("No database file found, starting fresh")
                return {}
                
        except Exception as e:
            logger.error(f"Error loading member data: {e}")
            return {}

    async def save_data_async(self, force=False):
        """Save data with atomic write"""
        async with self._save_lock:
            try:
                if os.path.exists(DATABASE_FILE):
                    backup_file = f"{DATABASE_FILE}.backup"
                    import shutil
                    shutil.copy2(DATABASE_FILE, backup_file)
                
                temp_file = f"{DATABASE_FILE}.tmp"
                with open(temp_file, 'w') as f:
                    json.dump(self.data, f, indent=2)
                
                os.replace(temp_file, DATABASE_FILE)
                self._pending_saves = False
                logger.info("Member data saved successfully")
                
            except Exception as e:
                logger.error(f"Error saving member data: {e}")
                if os.path.exists(f"{DATABASE_FILE}.tmp"):
                    os.remove(f"{DATABASE_FILE}.tmp")

    def schedule_save(self):
        self._pending_saves = True

    def get_member_data(self, member_id, guild_id):
        """Get member data for specific guild"""
        guild_key = str(guild_id)
        member_key = str(member_id)
        
        # Ensure guild exists in data
        if guild_key not in self.data:
            self.data[guild_key] = {}
            logger.info(f"Created new guild data for {guild_key}")
        
        # Check if member exists
        if member_key in self.data[guild_key]:
            existing_data = self.data[guild_key][member_key]
            # Ensure rank matches XP
            correct_rank, correct_icon = calculate_rank_from_xp(existing_data.get("xp", 0))
            existing_data["rank"] = correct_rank
            existing_data["rank_icon"] = correct_icon
            return existing_data
        else:
            # New member, create default data
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
                "verified": False,
                "total_tactical_words": 0,
                "last_message_time": 0,
                "last_tactical_bonus": 0
            }
            
            self.data[guild_key][member_key] = default_member.copy()
            self.schedule_save()
            logger.info(f"Created new member {member_key} in guild {guild_key}")
            return self.data[guild_key][member_key]

    def add_xp_and_gmp(self, member_id, guild_id, gmp_change, xp_change, activity_type=None):
        """Add XP and GMP to member and check for rank changes"""
        member_data = self.get_member_data(member_id, guild_id)
        
        # Store old values
        old_rank = member_data["rank"]
        old_xp = member_data["xp"]
        
        # Update stats based on activity type
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
                member_data["tactical_words_used"] += 1
                member_data["total_tactical_words"] += 1
                member_data["last_tactical_bonus"] = time.time()
        
        # Add GMP and XP
        member_data["gmp"] += gmp_change
        member_data["xp"] += xp_change
        
        # Recalculate rank based on new XP
        new_rank, new_icon = calculate_rank_from_xp(member_data["xp"])
        member_data["rank"] = new_rank
        member_data["rank_icon"] = new_icon
        
        # Schedule save
        self.schedule_save()
        
        # Log the change
        logger.debug(f"Member {member_id}: +{xp_change} XP ({old_xp} -> {member_data['xp']}), Rank: {old_rank} -> {new_rank}")
        
        # Return whether rank changed
        return old_rank != new_rank, new_rank

    def award_daily_bonus(self, member_id, guild_id):
        """Award daily bonus"""
        member_data = self.get_member_data(member_id, guild_id)
        today = datetime.now().strftime('%Y-%m-%d')
        
        if member_data["last_daily"] != today:
            member_data["last_daily"] = today
            
            gmp_bonus = ACTIVITY_REWARDS["daily_bonus"]["gmp"]
            xp_bonus = ACTIVITY_REWARDS["daily_bonus"]["xp"]
            
            rank_changed, new_rank = self.add_xp_and_gmp(
                member_id, guild_id, gmp_bonus, xp_bonus
            )
            
            return True, gmp_bonus, xp_bonus, rank_changed, new_rank
        
        return False, 0, 0, False, None

    def get_next_rank_info(self, member_id, guild_id):
        """Get next rank information"""
        member_data = self.get_member_data(member_id, guild_id)
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
            "xp_needed": max(0, next_rank["required_xp"] - member_data["xp"]),
            "current_xp": member_data["xp"],
            "next_xp": next_rank["required_xp"],
            "current_rank_xp": current_rank_data["required_xp"]
        }

    def get_leaderboard(self, guild_id, sort_by="xp", limit=10):
        """Get leaderboard for specific guild"""
        guild_key = str(guild_id)
        
        if guild_key not in self.data:
            return []
        
        valid_sort_options = ["gmp", "xp", "tactical_words_used", "messages_sent", "total_tactical_words"]
        if sort_by not in valid_sort_options:
            sort_by = "xp"
        
        active_members = {k: v for k, v in self.data[guild_key].items() 
                         if v.get('messages_sent', 0) > 0 or v.get('xp', 0) > 0}
            
        sorted_members = sorted(
            active_members.items(),
            key=lambda x: x[1].get(sort_by, 0),
            reverse=True
        )
        
        return sorted_members[:limit]

    def mark_member_verified(self, member_id, guild_id):
        member_data = self.get_member_data(member_id, guild_id)
        member_data["verified"] = True
        self.schedule_save()

class MGSBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
        self.member_data = MemberData()
        self.remove_command('help')
        self.codec_conversations = {}
        
    async def setup_hook(self):
        self.check_alerts.start()
        self.track_voice_activity.start()
        self.backup_data.start()
        self.auto_save_data.start()
        
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Error syncing slash commands: {e}")

    @tasks.loop(minutes=60)
    async def check_alerts(self):
        """Random codec calls"""
        for guild in self.guilds:
            if random.random() < 0.2:
                general = discord.utils.get(guild.text_channels, name='general')
                if general:
                    sound = random.choice(MGS_CODEC_SOUNDS)
                    quote = random.choice(MGS_QUOTES)
                    await general.send(f"{sound}\nColonel: {quote}")

    @tasks.loop(minutes=10)
    async def track_voice_activity(self):
        """Track voice activity"""
        for guild in self.guilds:
            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    if member.bot:
                        continue
                    if not member.voice.self_deaf and not member.voice.self_mute:
                        self.member_data.add_xp_and_gmp(
                            member.id, guild.id, 
                            ACTIVITY_REWARDS["voice_minute"]["gmp"],
                            ACTIVITY_REWARDS["voice_minute"]["xp"],
                            "voice_minute"
                        )
    
    @tasks.loop(hours=12)
    async def backup_data(self):
        await self.member_data.save_data_async()

    @tasks.loop(minutes=5)
    async def auto_save_data(self):
        if self.member_data._pending_saves:
            await self.member_data.save_data_async()

    def check_tactical_words(self, message_content):
        """Detect tactical words in message"""
        count = 0
        words_found = set()
        lower_content = message_content.lower()
        
        for word in TACTICAL_WORDS:
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            matches = re.findall(pattern, lower_content)
            if matches:
                count += len(matches)
                words_found.add(word)
                
        if count > 0:
            logger.info(f"Tactical words found: {list(words_found)} (Total: {count})")
                
        return min(count, 10)

bot = MGSBot()

# NEWS SYSTEM
async def get_country_news(country_code, country_name):
    """Get news for specific country with fallback options"""
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
                return news
        
        fallback_params = {
            'apiKey': NEWS_API_KEY,
            'q': country_name,
            'sortBy': 'publishedAt',
            'pageSize': 5,
            'language': 'en'
        }
        fallback_response = requests.get('https://newsapi.org/v2/everything', params=fallback_params, timeout=10)
        
        if fallback_response.status_code == 200:
            return fallback_response.json().get('articles', [])
        
        return []
        
    except Exception as e:
        logger.error(f"Error fetching {country_name} news: {e}")
        return []

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is now online and ready!")
    print(f"🏗️ Connected to {len(bot.guilds)} guilds")
    
    for guild in bot.guilds:
        guild_key = str(guild.id)
        if guild_key in bot.member_data.data:
            member_count = len(bot.member_data.data[guild_key])
            print(f"📊 Guild '{guild.name}' ({guild.id}): {member_count} members loaded")
        else:
            print(f"📊 Guild '{guild.name}' ({guild.id}): New guild, no existing data")
    
    print("🚀 Bot is fully ready and operational!")
    print("🎖️ XP-based ranking system active!")

@bot.event
async def on_member_join(member):
    """Welcome system"""
    print(f"🎖️ NEW MEMBER JOINED: {member.name} (ID: {member.id}) in {member.guild.name}")
    
    try:
        bot.member_data.get_member_data(member.id, member.guild.id)
        bot.member_data.mark_member_verified(member.id, member.guild.id)
        
        welcome_channel = None
        
        if WELCOME_CHANNEL_ID:
            welcome_channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        
        if not welcome_channel:
            for channel_name in ['welcome', 'general', 'main', 'chat']:
                welcome_channel = discord.utils.get(member.guild.text_channels, name=channel_name)
                if welcome_channel:
                    break
        
        if not welcome_channel:
            for channel in member.guild.text_channels:
                if channel.permissions_for(member.guild.me).send_messages:
                    welcome_channel = channel
                    break
        
        if not welcome_channel:
            print(f"❌ No suitable welcome channel found in {member.guild.name}")
            return
        
        embed = discord.Embed(
            title="🔰 NEW OPERATIVE DETECTED",
            description=f"**{member.display_name}** has joined Mother Base!",
            color=0x5865F2
        )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        embed.add_field(
            name="STARTING RESOURCES",
            value="```\n🔰 Rank: Rookie\n💰 GMP: 1,000\n⚡ XP: 0\n```",
            inline=True
        )
        
        embed.add_field(
            name="QUICK START",
            value="```\n!gmp - Check status\n!daily - Get bonus\n!info - Commands\n```",
            inline=True
        )
        
        embed.add_field(
            name="RANK UP INFO",
            value="**Earn XP to unlock Discord roles!**\nFirst promotion: **Private** role at 100 XP",
            inline=False
        )
        
        embed.set_image(url="https://images-ext-1.discordapp.net/external/znqAGtNjrN09-n-59N5jJGCNJSBIJwYB31d8qzAzXYI/https/media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExdzVqMTFjZXNyZWh6cDA3eGc3YjJuMmUxdjl0Yml6cnhobjlxZzZrMyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/CacxhprRlavR0AveWN/giphy.gif?width=960&height=540")
        
        embed.set_footer(text=f"Joined: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        await welcome_channel.send(f"🟢 **Welcome to Mother Base, {member.mention}!**", embed=embed)
        print(f"✅ Welcome sent to #{welcome_channel.name} for {member.name}")
        
        await bot.member_data.save_data_async()
        
    except Exception as e:
        print(f"❌ Error in welcome system: {e}")
        import traceback
        traceback.print_exc()

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Ignore DM messages (no guild)
    if message.guild is None:
        return
    
    # Check for codec conversation responses
    if message.channel.id in bot.codec_conversations and bot.codec_conversations[message.channel.id]['active']:
        codec_data = bot.codec_conversations[message.channel.id]
        
        if time.time() - codec_data['start_time'] < 300:
            response = random.choice(CODEC_RESPONSES)
            
            if codec_data['messages'] >= 3:
                response = "I can talk now well... *codec static* Campbell out."
                bot.codec_conversations[message.channel.id]['active'] = False
            
            await asyncio.sleep(2)
            await message.channel.send(response)
            codec_data['messages'] += 1
        else:
            bot.codec_conversations[message.channel.id]['active'] = False
        
        return
        
    member_id = message.author.id
    guild_id = message.guild.id
    current_time = time.time()
    
    member_data = bot.member_data.get_member_data(member_id, guild_id)
    last_msg_time = member_data.get("last_message_time", 0)
    
    # Store old rank for comparison  
    old_rank = member_data["rank"]
    rank_changed = False
    new_rank = old_rank
    
    # ALWAYS check for tactical words regardless of cooldown
    tactical_count = bot.check_tactical_words(message.content)
    if tactical_count > 0:
        for _ in range(tactical_count):
            tactical_rank_changed, tactical_new_rank = bot.member_data.add_xp_and_gmp(
                member_id, guild_id,
                ACTIVITY_REWARDS["tactical_word"]["gmp"],
                ACTIVITY_REWARDS["tactical_word"]["xp"],
                "tactical_word"
            )
            if tactical_rank_changed:
                rank_changed = True
                new_rank = tactical_new_rank
    
    # Message rewards only if cooldown has passed (30 seconds)
    if current_time - last_msg_time > 30:
        member_data["last_message_time"] = current_time
        
        # Give base message rewards
        message_rank_changed, message_new_rank = bot.member_data.add_xp_and_gmp(
            member_id, guild_id,
            ACTIVITY_REWARDS["message"]["gmp"],
            ACTIVITY_REWARDS["message"]["xp"],
            "message"
        )
        
        if message_rank_changed:
            rank_changed = True
            new_rank = message_new_rank
        
        # ONLY notify if there's a genuine rank change
        if rank_changed and old_rank != new_rank:
            try:
                await message.add_reaction("🎖️")
                role_updated = await update_member_roles(message.author, new_rank)
                
                embed = discord.Embed(
                    title="🎖️ RANK PROMOTION",
                    description=f"**{message.author.display_name}** promoted from **{old_rank}** to **{new_rank}**!",
                    color=0x599cff
                )
                
                if role_updated:
                    rank_data = get_rank_data_by_name(new_rank)
                    role_name = rank_data.get("role_name", new_rank)
                    embed.add_field(name="🎖️ ROLE ASSIGNED", value=f"Discord role **{role_name}** granted!", inline=False)
                else:
                    embed.add_field(name="⚠️ ROLE UPDATE", value="Role assignment failed - contact admin", inline=False)
                
                # Show current stats
                updated_member_data = bot.member_data.get_member_data(member_id, guild_id)
                embed.add_field(
                    name="CURRENT STATUS", 
                    value=f"```\nRank: {new_rank}\nXP: {format_number(updated_member_data['xp'])}\nGMP: {format_number(updated_member_data['gmp'])}\n```", 
                    inline=False
                )
                
                await message.channel.send(embed=embed)
                await bot.member_data.save_data_async(force=True)
                
                logger.info(f"PROMOTION: {message.author.name} promoted from {old_rank} to {new_rank}")
                
            except Exception as e:
                logger.error(f"Error in promotion system: {e}")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
        
    guild_id = reaction.message.guild.id
    
    # Give XP to reaction giver
    bot.member_data.add_xp_and_gmp(
        user.id, guild_id,
        ACTIVITY_REWARDS["reaction"]["gmp"],
        ACTIVITY_REWARDS["reaction"]["xp"],
        "reaction"
    )
    
    # Give XP to message author if different person
    if not reaction.message.author.bot and reaction.message.author.id != user.id:
        bot.member_data.add_xp_and_gmp(
            reaction.message.author.id, guild_id,
            ACTIVITY_REWARDS["reaction_received"]["gmp"],
            ACTIVITY_REWARDS["reaction_received"]["xp"],
            "reaction_received"
        )

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❗ Insufficient security clearance!")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❓ Unknown codec frequency")
    else:
        await ctx.send("❗ Operation failed.")
        logger.error(f"Command error: {error}")

# COMMANDS
@bot.command(name='codec')
async def codec(ctx):
    """Interactive MGS codec conversation"""
    messages = [
        "*codec ring*",
        "Snake, do you copy?",
        f"I read you, {ctx.author.name}.",
        "Mission briefing incoming...",
    ]
    
    msg = await ctx.send(messages[0])
    for i in range(1, len(messages)):
        await asyncio.sleep(1.5)
        await msg.edit(content='\n'.join(messages[:i+1]))
    
    bot.codec_conversations[ctx.channel.id] = {
        'active': True,
        'start_time': time.time(),
        'messages': 0
    }
    
    await asyncio.sleep(2)
    await ctx.send("**You can now respond to continue the codec conversation...**")

@bot.command(name='gmp')
async def gmp(ctx):
    """Check GMP balance, rank, and stats"""
    member_id = ctx.author.id
    guild_id = ctx.guild.id
    member_data = bot.member_data.get_member_data(member_id, guild_id)
    next_rank = bot.member_data.get_next_rank_info(member_id, guild_id)
    
    embed = discord.Embed(
        title=f"{member_data.get('rank_icon', '🔰')} {ctx.author.display_name}",
        description=f"**Rank:** {member_data['rank']}\n**GMP:** {format_number(member_data['gmp'])}\n**XP:** {format_number(member_data['xp'])}",
        color=0x599cff
    )
    
    if ctx.author.avatar:
        embed.set_thumbnail(url=ctx.author.avatar.url)
    
    embed.add_field(
        name="ACTIVITY STATS",
        value=f"```\nMessages: {format_number(member_data['messages_sent'])}\nVoice: {format_number(member_data['voice_minutes'])} min\nTactical Words: {format_number(member_data.get('total_tactical_words', 0))}\n```",
        inline=False
    )
    
    if next_rank:
        xp_progress = member_data["xp"] - next_rank["current_rank_xp"]
        xp_total = next_rank["next_xp"] - next_rank["current_rank_xp"]
        
        xp_bar = make_progress_bar(xp_progress, xp_total)
        xp_needed = max(0, next_rank["next_xp"] - member_data["xp"])
        
        rank_data = get_rank_data_by_name(next_rank["name"])
        role_name = rank_data.get("role_name", next_rank["name"])
        
        progress_text = f"```\nNext Rank: {next_rank['name']} {next_rank['icon']}\nDiscord Role: {role_name}\n\n"
        progress_text += f"XP: {format_number(member_data['xp'])} / {format_number(next_rank['next_xp'])} {xp_bar}\n\n"
        
        if xp_needed > 0:
            progress_text += f"NEEDED FOR PROMOTION:\nXP: {format_number(xp_needed)}\n"
        else:
            progress_text += "🎖️ READY FOR PROMOTION!\n"
        
        progress_text += "```"
        
        embed.add_field(name="RANK PROGRESS", value=progress_text, inline=False)
    else:
        embed.add_field(name="MAXIMUM RANK", value="```\nFOXHOUND operative - highest rank achieved!\n```", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='rank')
async def rank(ctx, member: discord.Member = None):
    """Check rank status of yourself or another member"""
    if member is None:
        member = ctx.author
    
    if member.bot:
        await ctx.send("❌ Bots don't have ranks.")
        return
    
    member_id = member.id
    guild_id = ctx.guild.id
    member_data = bot.member_data.get_member_data(member_id, guild_id)
    
    embed = discord.Embed(
        title=f"{member_data.get('rank_icon', '🔰')} {member.display_name}",
        description=f"**Rank:** {member_data['rank']}\n**GMP:** {format_number(member_data['gmp'])}\n**XP:** {format_number(member_data['xp'])}",
        color=0x599cff
    )
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    embed.add_field(
        name="ACTIVITY STATS",
        value=f"```\nMessages: {format_number(member_data['messages_sent'])}\nVoice: {format_number(member_data['voice_minutes'])} min\nTactical Words: {format_number(member_data.get('total_tactical_words', 0))}\n```",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='leaderboard', aliases=['lb'])
async def leaderboard(ctx, category: str = "xp"):
    """View server leaderboard"""
    guild_id = ctx.guild.id
    
    valid_categories = {
        "gmp": "GMP Ranking",
        "xp": "Experience Points",
        "tactical": "Tactical Words",
        "messages": "Messages Sent"
    }
    
    category_mapping = {
        "gmp": "gmp",
        "xp": "xp", 
        "tactical": "total_tactical_words",
        "messages": "messages_sent"
    }
    
    if category.lower() not in category_mapping:
        category = "xp"
    
    sort_field = category_mapping[category.lower()]
    title = valid_categories[category.lower()]
    
    leaderboard_data = bot.member_data.get_leaderboard(guild_id, sort_by=sort_field, limit=10)
    
    embed = discord.Embed(
        title=f"🏆 LEADERBOARD: {title.upper()}",
        color=0x599cff
    )
    
    if not leaderboard_data:
        embed.add_field(name="NO DATA", value="No operatives found.", inline=False)
        await ctx.send(embed=embed)
        return
    
    leaderboard_text = ""
    for i, (member_id, data) in enumerate(leaderboard_data, 1):
        try:
            member = ctx.guild.get_member(int(member_id))
            name = member.display_name if member else f"Unknown ({member_id})"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            value = data.get(sort_field, 0)
            rank_icon = data.get("rank_icon", "🔰")
            
            leaderboard_text += f"{medal} **{name}** - {format_number(value)} {category.upper()} {rank_icon}\n"
        except Exception:
            continue
    
    embed.add_field(name="TOP OPERATIVES", value=leaderboard_text, inline=False)
    
    categories_help = "\n".join([f"`!lb {cat}` - {name}" for cat, name in valid_categories.items()])
    embed.add_field(name="CATEGORIES", value=categories_help, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='daily')
async def daily(ctx):
    """Claim daily bonus"""
    member_id = ctx.author.id
    guild_id = ctx.guild.id
    
    success, gmp, xp, rank_changed, new_rank = bot.member_data.award_daily_bonus(member_id, guild_id)
    
    if success:
        embed = discord.Embed(
            title="📦 DAILY SUPPLY DROP",
            description=f"**+{format_number(gmp)} GMP** and **+{format_number(xp)} XP** received!",
            color=0x00ff00
        )
        
        # Get updated member data
        member_data = bot.member_data.get_member_data(member_id, guild_id)
        
        embed.add_field(
            name="UPDATED STATS",
            value=f"```\nGMP: {format_number(member_data['gmp'])}\nXP: {format_number(member_data['xp'])}\nRank: {member_data['rank']}\n```",
            inline=False
        )
        
        if rank_changed:
            role_updated = await update_member_roles(ctx.author, new_rank)
            embed.add_field(name="🎖️ PROMOTION!", value=f"New rank: **{new_rank}**", inline=False)
            
            if role_updated:
                rank_data = get_rank_data_by_name(new_rank)
                role_name = rank_data.get("role_name", new_rank)
                embed.add_field(name="🎖️ ROLE ASSIGNED", value=f"Discord role **{role_name}** granted!", inline=False)
        
        embed.set_footer(text="Come back tomorrow for another supply drop!")
        await ctx.send(embed=embed)
        
        # Force save
        await bot.member_data.save_data_async(force=True)
        
    else:
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time_left = tomorrow - now
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds // 60) % 60
        
        embed = discord.Embed(
            title="❌ SUPPLY DROP UNAVAILABLE",
            description=f"Already claimed today.\nNext drop in **{hours:02d}:{minutes:02d}**",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='tactical_test')
async def tactical_test(ctx, *, message=""):
    """Test tactical word detection"""
    if not message:
        await ctx.send("**Usage:** `!tactical_test <your message>`\n**Example:** `!tactical_test infiltrate the enemy base`")
        return
    
    tactical_count = bot.check_tactical_words(message)
    
    embed = discord.Embed(
        title="🎯 TACTICAL ANALYSIS",
        color=0x00ff00 if tactical_count > 0 else 0xff0000
    )
    
    embed.add_field(name="MESSAGE", value=f"```\n{message}\n```", inline=False)
    
    if tactical_count > 0:
        potential_gmp = tactical_count * ACTIVITY_REWARDS["tactical_word"]["gmp"]
        potential_xp = tactical_count * ACTIVITY_REWARDS["tactical_word"]["xp"]
        
        embed.add_field(
            name="✅ TACTICAL WORDS DETECTED",
            value=f"**Words Found:** {tactical_count}\n**Bonus:** +{potential_gmp} GMP, +{potential_xp} XP",
            inline=False
        )
    else:
        embed.add_field(
            name="❌ NO TACTICAL WORDS",
            value="Try using military, stealth, or MGS-related terms.",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Enhanced help command with categories"""
    embed = discord.Embed(
        title="📡 TACTICAL OPERATIONS CENTER - COMMAND MANUAL",
        description="```\n> XP-BASED RANKING SYSTEM ACTIVE\n> SECURITY STATUS: 🟢 SECURE\n> TYPE: COMPREHENSIVE MANUAL\n```",
        color=0x599cff
    )
    
    # Basic Operations
    embed.add_field(
        name="🔰 BASIC OPERATIONS",
        value="""```
!codec       - Interactive codec communication
!gmp         - Check status & rank
!rank [@user] - View rank status
!daily       - Daily supply drop
!tactical_test - Test tactical word detection
!info        - Quick command reference
```""",
        inline=False
    )
    
    # Ranking System
    embed.add_field(
        name="🎖️ XP-BASED RANKING GUIDE",
        value="""```
EARN DISCORD ROLES BY REACHING XP LEVELS:
• Private: 100 XP
• Specialist: 200 XP  
• Corporal: 350 XP
• Sergeant: 500 XP
• Lieutenant: 750 XP
• Captain: 1,000 XP
• Major: 1,500 XP
• Colonel: 2,500 XP
• FOXHOUND: 4,000 XP

⚠️ AUTOMATIC: Roles assigned when you 
reach the XP requirement!
```""",
        inline=False
    )
    
    # Leaderboard
    embed.add_field(
        name="🏆 LEADERBOARDS",
        value="""```
!leaderboard [category] - View rankings
  Categories: 
  xp, gmp, tactical, messages
  
Example: !lb xp
```""",
        inline=False
    )
    
    # Admin Commands
    if ctx.author.guild_permissions.kick_members or ctx.author.guild_permissions.administrator:
        embed.add_field(
            name="🛡️ MODERATION COMMANDS",
            value="""```
!kick <user> [reason]     - Remove operative
!ban <user> [reason]      - Permanently terminate
!clear <amount>           - Delete messages (1-100)
!auto_promote             - Auto-assign roles by XP
!fix_all_roles            - Sync roles with database
!check_roles              - Verify Discord roles
!test_promotion [@user]   - Test promotion system
```""",
            inline=False
        )
    
    # Progression Guide
    embed.add_field(
        name="📈 HOW TO EARN XP",
        value="""```
• Send messages (+3 XP every 30 sec)
• Voice activity (+2 XP per minute)
• Give reactions (+1 XP)
• Receive reactions (+2 XP) 
• Daily bonus (+50 XP)
• Tactical words (+8 XP each)

⭐ Ranking based on XP only!
GMP is for stats and activities.
```""",
        inline=False
    )
    
    embed.set_footer(text="🎖️ XP-Based Ranking: Earn Discord roles through progression!")
    await ctx.send(embed=embed)

@bot.command(name='info')
async def info(ctx):
    """Show bot information and commands"""
    embed = discord.Embed(
        title="📡 MOTHER BASE COMMAND CENTER",
        description="Available operations for all personnel:",
        color=0x599cff
    )
    
    embed.add_field(
        name="🔰 BASIC COMMANDS",
        value="""```
!gmp         - Check status & rank
!rank [@user] - View rank info
!daily       - Daily supply drop
!leaderboard - Top operatives
!codec       - Interactive communication
!tactical_test - Test tactical words
```""",
        inline=False
    )
    
    # Show moderation commands if user has permissions
    if ctx.author.guild_permissions.kick_members or ctx.author.guild_permissions.manage_messages:
        embed.add_field(
            name="🛡️ MODERATION TOOLS",
            value="""```
!kick <user> [reason]  - Remove member
!ban <user> [reason]   - Ban member
!clear <amount>        - Delete messages
```""",
            inline=False
        )
    
    # Show admin commands if user has admin permissions
    if ctx.author.guild_permissions.administrator:
        embed.add_field(
            name="⚙️ ADMIN TOOLS",
            value="""```
!auto_promote      - Auto-assign roles
!test_promotion    - Test rank system
!check_roles       - Verify roles exist
```""",
            inline=False
        )
    
    embed.add_field(
        name="🎖️ XP-BASED RANKING",
        value="""```
Private: 100 XP
Specialist: 200 XP
Corporal: 350 XP
Sergeant: 500 XP
Lieutenant: 750 XP
Captain: 1,000 XP
...and more ranks!

Earn Discord roles automatically!
```""",
        inline=False
    )
    
    embed.add_field(
        name="💰 HOW TO EARN XP",
        value="""```
📝 Send messages      +3 XP
🎤 Voice activity     +2 XP/min
👍 Reactions          +1-2 XP
📦 Daily bonus        +50 XP
🎯 Tactical words     +8 XP each

Ranking based on XP only!
```""",
        inline=False
    )
    
    embed.set_footer(text="Use !help for complete command manual")
    
    await ctx.send(embed=embed)

# MODERATION COMMANDS
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """Kick a member with MGS-style message and DM"""
    if member is None:
        await ctx.send("❌ Please specify a member to kick!")
        return
    
    if member == ctx.author:
        await ctx.send("❌ You cannot kick yourself!")
        return
    
    if member.guild_permissions.administrator:
        await ctx.send("❌ Cannot kick administrators!")
        return
    
    if member.top_role >= ctx.guild.me.top_role:
        await ctx.send("❌ Cannot kick this member - they have higher or equal role!")
        return
    
    # Contact information
    contact_admins = [
        "solid.ninja",
        "rip_carti", 
        "ahab_in_rehab",
        "*outer.heaven*"
    ]
    
    try:
        # Send DM first
        dm_sent = False
        try:
            dm_embed = discord.Embed(
                title="🚨 EXTRACTION NOTICE",
                description=f"```\n> MISSION STATUS: TERMINATED\n> OPERATIVE EXTRACTED FROM MOTHER BASE\n> SERVER: {ctx.guild.name}\n> OPERATOR: {ctx.author.name}\n```",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
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
            
            # Add contact information
            contact_list = "\n".join([f"• {admin}" for admin in contact_admins])
            dm_embed.add_field(
                name="📞 CONTACT FOR REINSTATEMENT",
                value=f"```\nIf you believe this extraction was an error,\ncontact any of these Mother Base commanders:\n\n{contact_list}\n```",
                inline=False
            )
            
            dm_embed.add_field(
                name="COMMANDER MESSAGE",
                value="```\nYour mission at Mother Base has been terminated.\nContact command if you believe this is an error.\n```",
                inline=False
            )
            
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
            timestamp=datetime.now(timezone.utc)
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
            value=f"```\nExtracted by: {ctx.author.display_name}\nDM Notification: {'✅ Sent' if dm_sent else '❌ Failed'}\nTime: {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC\n```",
            inline=False
        )
        
        # Add contact info to public message
        contact_list = " • ".join(contact_admins)
        public_embed.add_field(
            name="📞 REINSTATEMENT CONTACTS",
            value=f"```\nFor appeals or reinstatement:\n{contact_list}\n```",
            inline=False
        )
        
        # Add the kick GIF
        public_embed.set_image(url="https://i.gifer.com/5ZJM.gif")
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

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """Ban a member with MGS-style message"""
    if member is None:
        await ctx.send("❌ Please specify a member to ban!")
        return
    
    if member == ctx.author:
        await ctx.send("❌ You cannot ban yourself!")
        return
    
    if member.guild_permissions.administrator:
        await ctx.send("❌ Cannot ban administrators!")
        return
    
    if member.top_role >= ctx.guild.me.top_role:
        await ctx.send("❌ Cannot ban this member - they have higher or equal role!")
        return
    
    try:
        # Try to send DM first
        try:
            dm_embed = discord.Embed(
                title="⚠️ TERMINATION NOTICE",
                description=f"```\n> MISSION STATUS: PERMANENTLY TERMINATED\n> OPERATIVE BANNED FROM MOTHER BASE\n> SERVER: {ctx.guild.name}\n> OPERATOR: {ctx.author.name}\n```",
                color=discord.Color.dark_red(),
                timestamp=datetime.now(timezone.utc)
            )
            
            if reason:
                dm_embed.add_field(
                    name="TERMINATION REASON",
                    value=f"```\n{reason}\n```",
                    inline=False
                )
            else:
                dm_embed.add_field(
                    name="TERMINATION REASON",
                    value="```\nNo specific reason provided\n```",
                    inline=False
                )
            
            dm_embed.add_field(
                name="FINAL MESSAGE",
                value="```\nYour access to Mother Base has been permanently revoked.\nThis decision is final.\n```",
                inline=False
            )
            
            await member.send(embed=dm_embed)
            dm_sent = True
            
        except:
            dm_sent = False
        
        # Ban the member
        ban_reason = f"Banned by {ctx.author.name}" + (f" - {reason}" if reason else "")
        await member.ban(reason=ban_reason)
        
        # Send public embed
        embed = discord.Embed(
            title="⚠️ OPERATIVE TERMINATED",
            description=f"```\n> TERMINATION COMPLETE\n> TARGET: {member.name}#{member.discriminator}\n> USER ID: {member.id}\n> STATUS: PERMANENTLY BANNED\n```",
            color=discord.Color.dark_red(),
            timestamp=datetime.now(timezone.utc)
        )
        
        if reason:
            embed.add_field(
                name="TERMINATION REASON",
                value=f"```\n{reason}\n```",
                inline=False
            )
        
        embed.add_field(
            name="OPERATION DETAILS",
            value=f"```\nTerminated by: {ctx.author.display_name}\nDM Notification: {'✅ Sent' if dm_sent else '❌ Failed'}\nTime: {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC\n```",
            inline=False
        )
        
        embed.set_footer(text="Mother Base security protocol - permanent termination")
        
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        await ctx.send("❌ **OPERATION FAILED**: I don't have permission to ban this member!")
    except discord.HTTPException as e:
        await ctx.send(f"❌ **TERMINATION FAILED**: {str(e)}")
    except Exception as e:
        await ctx.send(f"❌ **UNEXPECTED ERROR**: {str(e)}")

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    """Clear messages with MGS-style confirmation"""
    if amount < 1 or amount > 100:
        await ctx.send("❌ Amount must be between 1 and 100!")
        return
    
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
        
        embed = discord.Embed(
            title="🧹 DATA PURGE COMPLETE",
            description=f"```\n> OPERATION: MESSAGE ELIMINATION\n> TARGET CHANNEL: #{ctx.channel.name}\n> RECORDS DELETED: {len(deleted) - 1}\n> OPERATOR: {ctx.author.display_name}\n> STATUS: SUCCESS\n```",
            color=0x00ff00
        )
        
        confirmation = await ctx.send(embed=embed)
        await confirmation.delete(delay=5)
        
    except discord.Forbidden:
        await ctx.send("❌ **OPERATION FAILED**: I don't have permission to delete messages!")
    except Exception as e:
        await ctx.send(f"❌ **PURGE FAILED**: {str(e)}")

@bot.command(name='test_promotion')
@commands.has_permissions(administrator=True)
async def test_promotion(ctx, member: discord.Member = None):
    """Test rank promotion system (Admin only)"""
    if member is None:
        member = ctx.author
    
    if member.bot:
        await ctx.send("❌ Cannot promote bots.")
        return
    
    try:
        member_data = bot.member_data.get_member_data(member.id, ctx.guild.id)
        current_rank = member_data['rank']
        current_xp = member_data['xp']
        
        # Find current rank index
        current_index = 0
        for i, rank_data in enumerate(MGS_RANKS):
            if rank_data["name"] == current_rank:
                current_index = i
                break
        
        # Check if can be promoted
        if current_index >= len(MGS_RANKS) - 1:
            await ctx.send(f"❌ {member.display_name} is already at maximum rank: {current_rank}")
            return
        
        # Get next rank
        next_rank = MGS_RANKS[current_index + 1]
        old_roles = [role.name for role in member.roles if role.name in [r["role_name"] for r in MGS_RANKS if r["role_name"]]]
        
        # Force promote by setting XP to required amount
        member_data["xp"] = next_rank["required_xp"]
        member_data["rank"] = next_rank["name"]
        member_data["rank_icon"] = next_rank["icon"]
        
        # Update Discord role
        role_updated = await update_member_roles(member, next_rank["name"])
        new_roles = [role.name for role in member.roles if role.name in [r["role_name"] for r in MGS_RANKS if r["role_name"]]]
        
        # Show results
        embed = discord.Embed(
            title="🧪 RANK PROMOTION TEST",
            description=f"Testing promotion system for {member.mention}",
            color=0x00ff00
        )
        
        embed.add_field(
            name="RANK CHANGE",
            value=f"```\n{current_rank} → {next_rank['name']} {next_rank['icon']}\n```",
            inline=False
        )
        
        embed.add_field(
            name="ROLE CHANGE",
            value=f"```\nOld Roles: {', '.join(old_roles) if old_roles else 'None'}\nNew Roles: {', '.join(new_roles) if new_roles else 'None'}\nUpdated: {'✅ Yes' if role_updated else '❌ No'}\n```",
            inline=False
        )
        
        embed.add_field(
            name="XP ADJUSTMENT",
            value=f"```\nOld XP: {current_xp}\nNew XP: {member_data['xp']}\nRequirement: {next_rank['required_xp']} XP\n```",
            inline=False
        )
        
        embed.add_field(
            name="TEST RESULTS",
            value="**Role Assignment:** Discord roles granted based on XP level\n**System Status:** XP-based ranking working correctly",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Save the test changes
        await bot.member_data.save_data_async(force=True)
        
    except Exception as e:
        await ctx.send(f"❌ Test failed: {str(e)}")
        logger.error(f"Error in test_promotion: {e}")

# ADMIN COMMANDS
@bot.command(name='auto_promote')
@commands.has_permissions(administrator=True)
async def auto_promote(ctx):
    """Auto-promote all members based on their database XP"""
    status_msg = await ctx.send("```\n🔄 AUTO-PROMOTION SYSTEM ACTIVE...\nScanning database XP levels...\n```")
    
    try:
        promoted_count = 0
        processed_count = 0
        promotions = []
        
        guild_key = str(ctx.guild.id)
        if guild_key not in bot.member_data.data:
            await status_msg.edit(content="```\n❌ No member data found for this guild.\n```")
            return
        
        existing_members = bot.member_data.data[guild_key]
        
        for member in ctx.guild.members:
            if member.bot:
                continue
                
            processed_count += 1
            member_key = str(member.id)
            
            try:
                if member_key not in existing_members:
                    continue
                
                member_data = existing_members[member_key]
                current_xp = member_data.get('xp', 0)
                stored_rank = member_data.get('rank', 'Rookie')
                
                # Calculate correct rank based on XP
                correct_rank, correct_icon = calculate_rank_from_xp(current_xp)
                
                # Check if they need promotion
                if stored_rank != correct_rank:
                    # Update database rank
                    member_data['rank'] = correct_rank
                    member_data['rank_icon'] = correct_icon
                    
                    # Update Discord role
                    role_updated = await update_member_roles(member, correct_rank)
                    
                    if role_updated:
                        promoted_count += 1
                        rank_data = get_rank_data_by_name(correct_rank)
                        role_name = rank_data.get("role_name", correct_rank)
                        promotions.append(f"{member.display_name}: {stored_rank} → {correct_rank} ({role_name})")
                        print(f"✅ AUTO-PROMOTED: {member.name} from {stored_rank} to {correct_rank} ({current_xp} XP)")
                
                await asyncio.sleep(0.2)
                    
            except Exception as e:
                print(f"❌ Error processing {member.name}: {e}")
        
        # Save database changes
        await bot.member_data.save_data_async(force=True)
        
        embed = discord.Embed(
            title="✅ AUTO-PROMOTION COMPLETE",
            description="```\n> DATABASE XP SCAN COMPLETE\n> PROMOTIONS APPLIED\n> STATUS: SUCCESS\n```",
            color=0x00ff00
        )
        
        embed.add_field(
            name="OPERATION RESULTS",
            value=f"```\nProcessed: {processed_count} members\nPromoted: {promoted_count} members\nDatabase Members: {len(existing_members)}\n```",
            inline=False
        )
        
        if promotions:
            promotion_text = "```\n" + "\n".join(promotions[:10]) + "\n```"
            if len(promotions) > 10:
                promotion_text += f"\n*...and {len(promotions) - 10} more promotions*"
            
            embed.add_field(
                name="RECENT PROMOTIONS",
                value=promotion_text,
                inline=False
            )
        
        embed.add_field(
            name="RANK REQUIREMENTS",
            value="""```
Private: 100 XP       | Captain: 1,000 XP
Specialist: 200 XP    | Major: 1,500 XP  
Corporal: 350 XP      | Colonel: 2,500 XP
Sergeant: 500 XP      | FOXHOUND: 4,000 XP
Lieutenant: 750 XP
```""",
            inline=False
        )
        
        await status_msg.edit(content="", embed=embed)
        
    except Exception as e:
        await status_msg.edit(content=f"```\n❌ Auto-promotion failed: {str(e)}\n```")
        print(f"Error in auto_promote command: {e}")

@bot.command(name='fix_all_roles')
@commands.has_permissions(administrator=True)
async def fix_all_roles(ctx):
    """Fix all member roles based on current database ranks (Admin only)"""
    status_msg = await ctx.send("```\n🔄 FIXING ALL MEMBER ROLES...\nSyncing Discord roles with database ranks...\n```")
    
    try:
        updated_count = 0
        failed_count = 0
        processed_count = 0
        
        guild_key = str(ctx.guild.id)
        if guild_key not in bot.member_data.data:
            await status_msg.edit(content="```\n❌ No member data found for this guild.\n```")
            return
        
        existing_members = bot.member_data.data[guild_key]
        
        for member in ctx.guild.members:
            if member.bot:
                continue
                
            processed_count += 1
            member_key = str(member.id)
            
            try:
                if member_key not in existing_members:
                    continue
                
                # Get member's current rank from database
                member_data = existing_members[member_key]
                current_rank = member_data.get('rank', 'Rookie')
                
                # Update Discord roles to match database rank
                role_updated = await update_member_roles(member, current_rank)
                
                if role_updated:
                    updated_count += 1
                    print(f"✅ Fixed roles for {member.name} -> {current_rank}")
                else:
                    failed_count += 1
                    print(f"❌ Failed to fix roles for {member.name}")
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.3)
                    
            except Exception as e:
                failed_count += 1
                print(f"❌ Error fixing {member.name}: {e}")
        
        embed = discord.Embed(
            title="✅ ROLE FIX COMPLETE",
            description="```\n> ROLE SYNCHRONIZATION COMPLETE\n> STATUS: SUCCESS\n```",
            color=0x00ff00
        )
        
        embed.add_field(
            name="OPERATION RESULTS",
            value=f"```\nProcessed: {processed_count} members\nFixed: {updated_count} roles\nFailed: {failed_count} members\nDatabase Members: {len(existing_members)}\n```",
            inline=False
        )
        
        embed.add_field(
            name="WHAT THIS DOES",
            value="```\n• Reads each member's rank from database\n• Removes incorrect Discord roles\n• Assigns correct Discord roles\n• Does NOT change XP or ranks\n• Only syncs roles with stored data\n```",
            inline=False
        )
        
        embed.add_field(
            name="ROLE REQUIREMENTS",
            value="```\nRequired Discord roles:\nPrivate, Specialist, Corporal, Sergeant,\nLieutenant, Captain, Major, Colonel,\nFOXHOUND\n\nBot needs 'Manage Roles' permission!\n```",
            inline=False
        )
        
        await status_msg.edit(content="", embed=embed)
        
    except Exception as e:
        await status_msg.edit(content=f"```\n❌ Role fix failed: {str(e)}\n```")
        print(f"Error in fix_all_roles command: {e}")

@bot.command(name='check_roles')
@commands.has_permissions(administrator=True) 
async def check_roles(ctx):
    """Check if all required rank roles exist"""
    required_roles = [rank["role_name"] for rank in MGS_RANKS if rank["role_name"]]
    
    embed = discord.Embed(title="🔍 ROLE VERIFICATION", color=0x599cff)
    
    missing_roles = []
    existing_roles = []
    
    for role_name in required_roles:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            existing_roles.append(f"✅ {role_name}")
        else:
            missing_roles.append(f"❌ {role_name}")
    
    if existing_roles:
        embed.add_field(
            name="EXISTING ROLES", 
            value="\n".join(existing_roles), 
            inline=False
        )
    
    if missing_roles:
        embed.add_field(
            name="MISSING ROLES", 
            value="\n".join(missing_roles) + "\n\n**Create these roles manually!**", 
            inline=False
        )
        embed.color = 0xff0000
    else:
        embed.add_field(
            name="STATUS", 
            value="```\n✅ All rank roles found!\n✅ Ready for role-based ranking\n```", 
            inline=False
        )
    
    embed.add_field(
        name="BOT PERMISSIONS",
        value=f"```\nManage Roles: {'✅' if ctx.guild.me.guild_permissions.manage_roles else '❌'}\n```",
        inline=False
    )
    
    await ctx.send(embed=embed)

# NEWS COMMANDS
@bot.command(name='intel')
async def intel(ctx):
    """Get latest news as intelligence reports (US)"""
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

# SLASH COMMANDS
@bot.tree.command(name="ping", description="Test connection")
async def ping(interaction: discord.Interaction):
    """Test connection slash command"""
    embed = discord.Embed(
        title="📡 CODEC CONNECTION TEST",
        description=f"**Latency:** {round(bot.latency * 1000)}ms\n**Status:** 🟢 OPERATIONAL\n**XP System:** 🎖️ ACTIVE",
        color=0x599cff
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="status", description="Check your MGS rank and XP status")
async def status_slash(interaction: discord.Interaction):
    """Quick status check via slash command"""
    member_id = interaction.user.id
    guild_id = interaction.guild.id
    member_data = bot.member_data.get_member_data(member_id, guild_id)
    
    embed = discord.Embed(
        title=f"{member_data.get('rank_icon', '🔰')} OPERATIVE STATUS",
        description=f"**{interaction.user.display_name}**",
        color=0x599cff
    )
    
    embed.add_field(
        name="CURRENT STATS",
        value=f"```\nRank: {member_data['rank']}\nGMP: {format_number(member_data['gmp'])}\nXP: {format_number(member_data['xp'])}\n```",
        inline=True
    )
    
    embed.add_field(
        name="ACTIVITY",
        value=f"```\nMessages: {format_number(member_data['messages_sent'])}\nTactical Words: {format_number(member_data.get('total_tactical_words', 0))}\n```",
        inline=True
    )
    
    # Show current Discord role if any
    rank_roles = [rank["role_name"] for rank in MGS_RANKS if rank["role_name"]]
    current_role = None
    for role in interaction.user.roles:
        if role.name in rank_roles:
            current_role = role.name
            break
    
    embed.add_field(
        name="DISCORD ROLE",
        value=f"```\n{current_role if current_role else 'None (Rookie)'}\n```",
        inline=False
    )
    
    if interaction.user.avatar:
        embed.set_thumbnail(url=interaction.user.avatar.url)
    
    embed.set_footer(text="Use !gmp for detailed rank progress")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Run the bot
def main():
    try:
        if not TOKEN:
            print("❌ CRITICAL ERROR: DISCORD_TOKEN not found!")
            print("Please add DISCORD_TOKEN=your_bot_token to your .env file")
            return
            
        print("🚀 Starting MGS Discord Bot with XP-Based Ranking...")
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Mission failed! Error: {e}")

if __name__ == "__main__":
    main()
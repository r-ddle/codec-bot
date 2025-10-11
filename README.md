# Outer Heaven: Exiled Soldiers - Discord Bot

A Metal Gear Solid-themed Discord bot built exclusively for the Outer Heaven: Exiled Soldiers server. Features an XP-based ranking system with automatic role assignment, tactical word detection, daily bonuses, and server-wide leaderboards.

## Overview

This bot provides a complete progression and engagement system for server members. Players earn experience points (XP) through various activities including messaging, voice chat participation, and using tactical vocabulary from the Metal Gear Solid series. As members accumulate XP, they automatically receive Discord role promotions that reflect their rank within the server hierarchy.

## Core Features

### XP-Based Ranking System
The bot tracks member activity and awards XP for engagement. When members reach specific XP thresholds, they are automatically promoted to higher ranks and receive corresponding Discord roles. The system supports legacy progression for existing members while implementing balanced requirements for new members.

### Activity Tracking
Members earn XP through multiple channels:
- Sending messages in text channels (with cooldown to prevent spam)
- Participating in voice channels
- Giving and receiving reactions on messages
- Daily bonus claims with streak tracking
- Using tactical vocabulary from the Metal Gear Solid universe

### Word-Up Game Moderation
A dedicated word chain game where players must type words starting with the last letter of the previous word. The bot automatically monitors the game channel, validates submissions, and provides helpful feedback when players make mistakes. The system is case-insensitive and allows players to send GIFs alongside their words.

### Codec-Style Interface
All bot interactions use authentic Metal Gear Solid codec-style visual elements, including:
- Green monochrome aesthetic with scan lines
- Military-style status reports and briefings
- MGS-themed quotes and responses
- Tactical operation terminology

### Server Events
Periodic server-wide events where members compete to reach collective goals. Events track participation and reward top contributors with bonus XP.

## Available Commands

### Player Commands
- `!status` - Check your rank, XP, and progression stats
- `!rank [@user]` - View detailed rank card with statistics
- `!daily` - Claim daily XP bonus with streak tracking
- `!leaderboard [category]` - View server rankings (categories: xp, tactical, messages)
- `!tactical_test <message>` - Test tactical word detection on a message
- `!help` - Complete command manual
- `!profile [@user]` - View member profile card
- `!setbio <text>` - Set your profile biography (150 character limit)

### Word-Up Game Commands
- `!wordup_status` - Check current word and next required letter
- `!wordup_reset` - Reset the word chain (Admin only)
- `!wordup_set <word>` - Manually set current word (Admin only)

### Admin Commands
- `!test_promotion [@user]` - Test rank promotion system
- `!auto_promote` - Auto-assign Discord roles based on current XP
- `!fix_all_roles` - Sync all Discord roles with database
- `!check_roles` - Verify required Discord roles exist

### Moderation Commands
- `!kick <user> [reason]` - Remove a member from the server
- `!ban <user> [reason]` - Ban a member from the server
- `!clear <amount>` - Delete messages (1-100)

### Slash Commands
- `/ping` - Test bot connection and response time
- `/status` - Check your status (ephemeral message)

## Rank Progression

The bot uses a balanced XP progression system for new members, while maintaining legacy thresholds for existing members who joined before October 8, 2025.

### Current Rank Thresholds (New Members)

| Rank | Required XP | Discord Role |
|------|-------------|--------------|
| Rookie | 0 | None |
| Private | 200 | Private |
| Specialist | 500 | Specialist |
| Corporal | 1,000 | Corporal |
| Sergeant | 1,800 | Sergeant |
| Lieutenant | 3,000 | Lieutenant |
| Captain | 5,000 | Captain |
| Major | 8,000 | Major |
| Colonel | 12,000 | Colonel |
| FOXHOUND | 18,000 | FOXHOUND |

### XP Earning Methods

- Send messages: +3 XP (30 second cooldown between messages)
- Voice channel activity: +2 XP per minute
- Give reactions: +1 XP per reaction
- Receive reactions: +2 XP per reaction received
- Daily bonus: +50 XP (claimable once per day)
- Tactical words: +8 XP per word (bot detects MGS-related vocabulary)

### Tactical Vocabulary

The bot recognizes over 100 tactical and Metal Gear Solid-related words including military terms, stealth operations vocabulary, and character names. Using these words in your messages grants bonus XP. Examples include: tactical, stealth, operation, infiltrate, metal gear, snake, foxhound, and many more.

## Word-Up Game

The bot includes automated moderation for the Word-Up word chain game in the dedicated Word-Up channel. Players must continue the chain by starting their word with the last letter of the previous word.

### Game Rules

- Each word must start with the last letter of the previous word
- Words are case-insensitive
- The bot tracks the current word and enforces the chain
- Violations result in a warning embed showing the expected letter

### Game Commands

- `!wordup_status` - Shows the current word and next required letter
- `!wordup_reset` - Resets the game chain (Admin only)
- `!wordup_set <word>` - Manually sets the current word (Admin only)

## Database

Member data is stored in `member_data.json` with automatic backups every 12 hours. The database tracks:

- XP and current rank
- Message count, voice minutes, reaction statistics
- Tactical word usage counter
- Daily bonus cooldown and streak
- Custom profile biography

Example member record:

```json
{
  "guild_id": {
    "member_id": {
      "xp": 5000,
      "rank": "Captain",
      "messages_sent": 1234,
      "voice_minutes": 567,
      "reactions_given": 89,
      "reactions_received": 123,
      "total_tactical_words": 45,
      "last_daily": "2025-01-15T12:00:00",
      "last_message_time": 1705324800.0,
      "verified": true,
      "bio": "Soldier of Outer Heaven"
    }
  }
}
```

## Required Permissions

The bot requires the following Discord permissions:

- Read Messages/View Channels
- Send Messages
- Embed Links
- Add Reactions
- Manage Roles (for automatic rank role assignment)
- Kick Members (for moderation commands)
- Ban Members (for moderation commands)
- Manage Messages (for message clearing)

## Technical Information

The bot is built using discord.py with a modular cog-based architecture. Core features include:

- Automatic XP tracking and rank progression
- Discord role synchronization with rank system
- JSON-based member data persistence with atomic writes
- Automated backup system with scheduled saves
- Event-driven message processing with cooldown management
- MGS Codec-style image generation for rank cards and daily bonuses

## Credits

Metal Gear Solid franchise by Konami. Bot developed exclusively for the Outer Heaven: Exiled Soldiers Discord server.

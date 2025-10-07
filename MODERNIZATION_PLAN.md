# 🎮 TXRails Bot Modernization Plan

## 🎯 Core Philosophy
- **Preserve existing data** - No changes to current members' stats
- **MGS-themed** - Stay true to Metal Gear Solid universe
- **Modern Discord features** - Buttons, Select Menus, Modals, Thread support
- **Make GMP useful** - Currency system with actual value

---

## 📊 Current State Analysis

### What Works Well ✅
- XP-based rank progression
- Tactical word detection
- Discord role assignment
- Message/Voice activity tracking
- Daily bonus system

### What Needs Improvement ❌
- **GMP is useless** - Just a number, no real purpose
- **Commands are text-only** - No modern Discord UI (buttons, menus)
- **No economy system** - Nothing to spend GMP on
- **No member engagement features** - No missions, challenges, or events
- **Limited social features** - No profiles, achievements, or badges
- **No gamification** - Beyond XP grinding

---

## 🚀 Proposed Improvements

### Phase 1: Make GMP Useful (GMP Economy) 💰

#### 1.1 **GMP Shop System**
Create an MGS-themed shop where members can spend GMP.

**Items to Purchase:**
```
🎖️ COSMETICS
- Custom rank titles ($500 GMP) - "Big Boss", "The Patriot", etc.
- Profile backgrounds ($300 GMP) - Shadow Moses, Mother Base themes
- Profile badges ($200 GMP) - FOXHOUND emblem, Codec icon, etc.
- Name colors in rank cards ($400 GMP)

🎭 ROLES & PERKS
- Temporary special roles ($1000 GMP / 7 days)
  - "Legendary Soldier" (gold name)
  - "FOXHOUND Operative" (exclusive color)
  - "Outer Heaven VIP" (special permissions)

- Channel access ($1500 GMP / month)
  - #classified-intel (exclusive discussions)
  - #mother-base-lounge (VIP chat)

🎲 BOOSTERS & ITEMS
- XP Boost 2x (1 hour) - $300 GMP
- XP Boost 2x (24 hours) - $2000 GMP
- Daily Bonus multiplier - $500 GMP
- Tactical Word Bonus 2x - $400 GMP

🎁 SPECIAL ITEMS
- "Get Out of Jail Free" card - $5000 GMP (cancel 1 timeout/mute)
- Custom codec message - $800 GMP (bot says your message)
- Server-wide announcement - $3000 GMP (special message)
- Unlock secret channels - $10,000 GMP
```

**Implementation:**
- Use Discord Buttons for shop navigation
- Select Menus for item categories
- Modals for custom inputs
- Inventory system tracking purchases

---

#### 1.2 **GMP Transfer & Trading**
```
!transfer @user <amount> - Send GMP to another member
!trade @user - Initiate trade modal with offers
```

**Rules:**
- Minimum 100 GMP per transfer
- 5% transaction fee (prevents abuse)
- Trade history tracked
- Daily transfer limit (prevents alt abuse)

---

### Phase 2: Modern Discord UI 🎨

#### 2.1 **Button-Based Navigation**
Replace text commands with interactive buttons:

**Example: !shop command**
```
┌─────────────────────────────────┐
│      🏪 MOTHER BASE SHOP        │
├─────────────────────────────────┤
│  Your GMP: 5,420                │
└─────────────────────────────────┘

[🎖️ Cosmetics] [🎭 Roles] [🎲 Boosters]
[🎁 Special] [📦 Inventory] [❌ Close]
```

**Example: Rank Card with Actions**
```
┌─────────────────────────────────┐
│  🎖️ Captain - riddle            │
│  GMP: 5,420 | XP: 1,234         │
└─────────────────────────────────┘

[📊 Full Stats] [🏪 Shop] [🎁 Daily]
[🏆 Leaderboard] [🎯 Missions]
```

---

#### 2.2 **Slash Commands**
Modern Discord commands with autocomplete:

```
/rank [user] - View rank card
/shop [category] - Browse shop
/daily - Claim bonus
/missions - View active missions
/inventory - Check your items
/transfer <user> <amount> - Send GMP
```

**Benefits:**
- Cleaner interface
- Autocomplete suggestions
- Better mobile experience
- Native Discord integration

---

#### 2.3 **Context Menus**
Right-click user actions:

```
Right-click User → Apps →
  - View Rank
  - Send GMP
  - Challenge to Trivia
  - Award Commendation
```

---

### Phase 3: Missions & Challenges 🎯

#### 3.1 **Daily/Weekly Missions**
MGS-themed challenges with GMP rewards:

**Daily Missions (Reset 24h):**
```
🎯 "Shadow Moses Protocol"
├─ Send 20 messages - 100 GMP + 10 XP
├─ Use 5 tactical words - 150 GMP + 15 XP
├─ React to 10 messages - 50 GMP + 5 XP
└─ Claim your daily bonus - 50 GMP

🎯 "Infiltration Training"
├─ Be in voice for 30 min - 200 GMP + 20 XP
├─ Help 3 members (react/reply) - 100 GMP + 10 XP
└─ Complete a trivia question - 150 GMP
```

**Weekly Missions (Reset Monday):**
```
🎖️ "Operation: OUTER HEAVEN"
├─ Send 100 messages - 1000 GMP + 100 XP
├─ Use 50 tactical words - 1500 GMP + 150 XP
├─ Win 3 trivia challenges - 800 GMP + 80 XP
├─ Spend 2 hours in voice - 1200 GMP + 120 XP
└─ Complete all daily missions 5 times - 2000 GMP + 200 XP

REWARD: Legendary Soldier role (7 days) + 5000 GMP
```

**Tracking:**
- Separate mission progress storage
- Visual progress bars
- Notification on completion
- Bonus rewards for streaks

---

#### 3.2 **Community Events**
Server-wide collaborative missions:

**Example: "Metal Gear Rising"**
```
🌍 COMMUNITY MISSION ACTIVE
Goal: Collectively send 10,000 messages
Progress: ████████░░ 8,234 / 10,000

Rewards when complete:
- Everyone: 500 GMP + 50 XP
- Top 10 contributors: 2000 GMP + Special role
- #1 contributor: 5000 GMP + Legendary Badge

Time remaining: 3 days 14h 32m
```

---

### Phase 4: Social Features 👥

#### 4.1 **Enhanced Profiles**
Customizable member profiles:

```
╔═══════════════════════════════════╗
║  🎖️ Captain riddle              ║
║  Member since: Sept 2024          ║
╠═══════════════════════════════════╣
║  STATS                            ║
║  GMP: 5,420 | XP: 1,234          ║
║  Messages: 456 | Voice: 12h       ║
║  Tactical Words: 89               ║
╠═══════════════════════════════════╣
║  ACHIEVEMENTS 🏆                  ║
║  ⭐ Early Adopter                 ║
║  🎯 Mission Master (10/10)        ║
║  💬 Chatterbox (500+ messages)    ║
║  🎤 Voice Champion (50+ hours)    ║
╠═══════════════════════════════════╣
║  EQUIPPED ITEMS                   ║
║  Title: "The Legendary Soldier"   ║
║  Badge: FOXHOUND Emblem          ║
║  Background: Shadow Moses         ║
╠═══════════════════════════════════╣
║  BIO                              ║
║  "A Hind D?!"                     ║
╚═══════════════════════════════════╝

[✏️ Edit Bio] [🎨 Customize] [🏪 Shop]
```

**Custom Bio:**
- `/bio set <text>` - Set custom bio (50 chars max)
- Costs 200 GMP to set/change
- Profanity filter enabled

---

#### 4.2 **Achievement System**
Unlock badges and titles:

**Achievements:**
```
🏆 COMBAT ACHIEVEMENTS
├─ "First Blood" - Send first message
├─ "Chatterbox" - 500 messages sent
├─ "Legendary Talker" - 5,000 messages sent
├─ "Tactical Genius" - Use 100 tactical words
├─ "Voice of FOXHOUND" - 50 hours in voice

🎯 PROGRESSION ACHIEVEMENTS
├─ "Rising Through Ranks" - Reach Sergeant
├─ "Elite Operative" - Reach Colonel
├─ "Legendary Soldier" - Reach FOXHOUND
├─ "XP Hunter" - Earn 5,000 XP
├─ "Millionaire" - Earn 100,000 total GMP

🌟 SPECIAL ACHIEVEMENTS
├─ "Early Adopter" - Joined before Oct 2025
├─ "Mission Master" - Complete 100 missions
├─ "Perfect Week" - Complete all dailies for 7 days
├─ "Community Hero" - Top 3 in community event
├─ "Generous Soldier" - Transfer 10,000 GMP to others

🎁 RARE ACHIEVEMENTS
├─ "Diamond Dog" - Daily streak of 30 days
├─ "Big Boss" - #1 on leaderboard for 7 days
├─ "The Boss" - Reach max rank with 50,000 XP
└─ "Legendary Soldier" - All achievements unlocked
```

**Rewards:**
- Each achievement = Badge for profile
- Some give GMP/XP rewards
- Rare achievements = Special roles
- Display up to 5 favorite badges

---

#### 4.3 **Leaderboard Enhancements**
Multiple leaderboard categories with rewards:

```
/leaderboard <type>
- xp - Total XP ranking
- gmp - Total GMP ranking
- weekly - This week's most active
- monthly - This month's stats
- missions - Most missions completed
- tactical - Most tactical words used
- generous - Most GMP donated
- voice - Most voice time
```

**Weekly Rewards:**
- Top 1: 2000 GMP + Special role (7 days)
- Top 2-3: 1000 GMP
- Top 4-10: 500 GMP

---

### Phase 5: MGS Mini-Games 🎮

#### 5.1 **Metal Gear Trivia**
Challenge others to MGS trivia:

```
/trivia challenge @user <wager>
- Random MGS question
- First to answer correctly wins
- Winner gets wager amount from loser
- 10 second time limit
- Questions from MGS lore database
```

**Categories:**
- MGS1-5 plot/characters
- Game mechanics
- Famous quotes
- Timeline events
- Boss fights

---

#### 5.2 **Codec Roulette**
Interactive mini-game:

```
/codec play <wager>
- Bot gives codec-style clues
- You guess the character speaking
- 3 tries to guess correctly
- Win = 2x wager
- Lose = lose wager
```

---

#### 5.3 **Daily Challenges**
Random daily task:

```
TODAY'S CHALLENGE 🎯
"Use the word 'tactical' in 5 different messages"

Reward: 500 GMP + 50 XP
Time Left: 8h 34m

[View Progress] [See Rules]
```

---

### Phase 6: Enhanced Moderation 🛡️

#### 6.1 **Warning System with Consequences**
```
/warn @user <reason> - Issue warning
- 1st warning: Notification only
- 2nd warning: 10 min timeout + lose 100 GMP
- 3rd warning: 1 hour timeout + lose 500 GMP
- 4th warning: 1 day timeout + lose 2000 GMP
- 5th warning: Kick from server

/warnings @user - View warning history
/unwarn @user - Remove last warning (admin only)
```

**Redemption:**
- Clean record for 30 days = warnings reset
- Can buy warning removal (5000 GMP)
- "Get Out of Jail Free" card from shop

---

#### 6.2 **Reputation System**
Members can give +rep or -rep:

```
/rep @user [reason] - Give reputation point
- Can give +rep once per user per week
- Good behavior = +rep
- Helps build community trust
- High rep = special badge

Reputation Tiers:
- 0-9: Regular Member
- 10-24: Trusted Soldier
- 25-49: Veteran Operative
- 50-99: Elite FOXHOUND
- 100+: Legendary Hero (special role)
```

---

## 🔧 Technical Implementation Plan

### Database Changes (Safe for existing members)

**New Tables:**
```sql
-- Shop items
CREATE TABLE shop_items (
    item_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    category VARCHAR(50),
    price INTEGER,
    duration_days INTEGER, -- for temporary items
    item_type VARCHAR(50) -- 'cosmetic', 'role', 'booster', etc.
);

-- Member inventory
CREATE TABLE inventory (
    member_id BIGINT,
    guild_id BIGINT,
    item_id INTEGER,
    purchased_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_equipped BOOLEAN DEFAULT FALSE
);

-- Missions
CREATE TABLE missions (
    mission_id SERIAL PRIMARY KEY,
    type VARCHAR(20), -- 'daily' or 'weekly'
    name VARCHAR(100),
    description TEXT,
    requirements JSONB,
    rewards JSONB
);

-- Mission progress
CREATE TABLE mission_progress (
    member_id BIGINT,
    guild_id BIGINT,
    mission_id INTEGER,
    progress JSONB,
    completed BOOLEAN,
    completed_at TIMESTAMP
);

-- Achievements
CREATE TABLE achievements (
    achievement_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    requirement TEXT,
    reward_gmp INTEGER,
    reward_xp INTEGER,
    badge_icon VARCHAR(50)
);

-- Member achievements
CREATE TABLE member_achievements (
    member_id BIGINT,
    guild_id BIGINT,
    achievement_id INTEGER,
    unlocked_at TIMESTAMP,
    is_favorite BOOLEAN DEFAULT FALSE
);

-- Transactions
CREATE TABLE gmp_transactions (
    transaction_id SERIAL PRIMARY KEY,
    from_member_id BIGINT,
    to_member_id BIGINT,
    guild_id BIGINT,
    amount INTEGER,
    transaction_type VARCHAR(50), -- 'transfer', 'purchase', 'mission_reward'
    timestamp TIMESTAMP
);

-- Profiles
CREATE TABLE member_profiles (
    member_id BIGINT PRIMARY KEY,
    guild_id BIGINT,
    custom_bio VARCHAR(200),
    custom_title VARCHAR(50),
    equipped_badge VARCHAR(50),
    equipped_background VARCHAR(50)
);
```

**IMPORTANT:** All new tables don't touch existing member_data!
- Existing members keep all their stats
- New features are opt-in
- Default values ensure backward compatibility

---

### Migration Strategy (Safe)

```python
# When bot starts:
1. Load existing member_data.json (unchanged)
2. Create new tables only if they don't exist
3. Populate default achievements/missions
4. Don't modify existing member stats
5. New features activate gradually

# For old members:
- They keep all existing XP, GMP, ranks
- New features available when they use them
- Inventory starts empty (no loss)
- Achievements unlock retroactively based on current stats
```

---

## 📅 Implementation Timeline

### Week 1-2: Foundation
- [ ] Update database schema (add new tables)
- [ ] Create shop system backend
- [ ] Build inventory system
- [ ] Test with new members only

### Week 3-4: UI Modernization
- [ ] Convert commands to slash commands
- [ ] Add button-based navigation
- [ ] Implement select menus
- [ ] Create modern embeds

### Week 5-6: GMP Economy
- [ ] Build shop interface
- [ ] Add item purchasing
- [ ] Implement GMP transfers
- [ ] Create transaction logging

### Week 7-8: Missions & Achievements
- [ ] Create mission system
- [ ] Add daily/weekly missions
- [ ] Build achievement tracker
- [ ] Add progress tracking

### Week 9-10: Social Features
- [ ] Enhanced profiles
- [ ] Custom bios
- [ ] Badge system
- [ ] Reputation system

### Week 11-12: Polish & Testing
- [ ] Bug fixes
- [ ] Performance optimization
- [ ] Documentation
- [ ] Community feedback

---

## 💡 Quick Wins (Start with these)

### Priority 1: Make GMP Useful
```
1. Add basic shop with 3-5 items
2. Add /shop command with buttons
3. Let members buy XP boosters
4. Add GMP transfer
```

### Priority 2: Missions
```
1. Add 3 daily missions
2. Track progress automatically
3. Award GMP on completion
4. Show with /missions command
```

### Priority 3: Slash Commands
```
1. Convert existing commands to slash
2. Keep ! commands for backward compat
3. Add autocomplete
4. Better mobile UX
```

---

## ⚠️ Safety Checks

### For Existing Members:
✅ All current XP, GMP, ranks preserved
✅ No forced participation in new features
✅ Can opt-in to new systems gradually
✅ No retroactive penalties
✅ Achievements unlock based on current progress

### Database Safety:
✅ New tables separate from member_data
✅ Migrations are additive only
✅ Rollback plan if issues occur
✅ Regular backups before updates

---

## 🤔 Questions for Discussion

1. **Shop Items Priority**: Which items should we add first?
   - Custom titles?
   - XP boosters?
   - Special roles?
   - Cosmetics?

2. **Pricing**: Are these GMP prices reasonable?
   - Too cheap = no value
   - Too expensive = frustrating

3. **Missions**: Should they be:
   - Auto-tracked (invisible until completed)?
   - Visible in command (see progress)?
   - Both options?

4. **New Members vs Old**:
   - Give old members retroactive achievements?
   - Or everyone starts fresh with achievements?

5. **Roles & Permissions**:
   - Should shop roles give actual perks?
   - Or purely cosmetic?

6. **Economy Balance**:
   - Current GMP earning rate good?
   - Need to adjust rewards?

---

## 🎯 Success Metrics

Track these to see if improvements work:

- Daily active users (increase expected)
- Messages sent per day (engagement)
- GMP shop purchases (economy health)
- Mission completion rate (fun factor)
- Time in voice channels (activity)
- Member retention (staying power)

---

**Let's discuss which features excite you most and prioritize from there!** 🚀

What aspects should we implement first?

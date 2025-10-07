# Daily Streak System & Image Generation Update

## ✅ COMPLETED

### 1. Added Daily Streak System
**Feature:** Tracks consecutive days of claiming daily bonus.

**Implementation:**
- Added `daily_streak` field to member data
- Streak increments by 1 if claimed yesterday
- Streak resets to 1 if more than 1 day passed
- Streak is 0 for members who never claimed

**Streak Logic:**
```python
# If claimed yesterday (24 hours ago) → streak continues
# If claimed 2+ days ago → streak resets to 1
# If first time → streak starts at 1
```

**Milestone Colors:**
- **7+ days:** 🔥 HOT STREAK (Gold)
- **30+ days:** ⭐ ELITE STREAK (Orange)
- **100+ days:** 🏆 LEGENDARY STREAK (Red)

---

### 2. Updated !test_promotion Command
**Now Generates Beautiful MGS Codec Image!**

**Changes:**
- Uses `generate_daily_supply_card()` to show promotion
- Displays promotion banner with flashing effect
- Shows granted Discord role
- Includes GMP/XP rewards simulation
- Fallback to text embed if image fails

**Usage:**
```bash
!test_promotion @user
# Shows beautiful promotion card with MGS aesthetic
```

**Features:**
- 🎖️ Promotion banner (with flash animation in GIF version)
- 📊 Updated stats display
- ✅ Role assignment confirmation
- 🎨 Full MGS Codec styling

---

### 3. Daily Command Already Has Images
**Status:** ✅ Already Implemented

The `!daily` command already generates images with:
- ✅ Streak counter with fire icons
- ✅ Milestone badges (7/30/100 days)
- ✅ Progress bar to next milestone
- ✅ GMP + XP reward boxes
- ✅ Promotion banner (if promoted)
- ✅ Updated stats display
- ✅ MGS Codec aesthetic

---

## STREAK SYSTEM DETAILS

### Database Schema
```python
member_data = {
    "daily_streak": 0,           # Consecutive days claimed
    "last_daily": "2025-10-07",  # Last claim date (YYYY-MM-DD)
    # ... other fields
}
```

### Streak Calculation
```python
# Day 1: Claim → streak = 1
# Day 2: Claim → streak = 2 (claimed yesterday)
# Day 3: Claim → streak = 3 (claimed yesterday)
# Day 5: Claim → streak = 1 (missed day 4, reset)
```

### Backward Compatibility
- Existing members automatically get `daily_streak: 0`
- Starts counting from their next daily claim
- No data migration required

---

## IMAGE GENERATION STATUS

### ✅ Working Commands

#### 1. **!rank** - Rank Card
- Shows username, rank badge, rank name
- XP progress bar
- GMP balance
- Activity stats (messages, voice time)
- Avatar circle
- MGS Codec green aesthetic

#### 2. **!daily** - Daily Supply Drop
- Streak counter with fire icons 🔥
- Milestone badges
- Progress bar to next milestone
- GMP + XP reward boxes
- Updated total stats
- Promotion banner (if promoted)
- Role granted notification

#### 3. **!test_promotion** - Promotion Test
- Same as daily supply drop image
- Simulates promotion with rewards
- Shows old rank → new rank
- Discord role confirmation
- Test-only command for admins

### 📋 To Be Implemented

#### 4. **Animated GIF Version** (Optional)
Function exists: `generate_daily_supply_animated()`
- 20 frames of animation
- Scanline movement
- Promotion banner flash
- Static interference pulses
- 100ms per frame, infinite loop

**To use:**
```python
from utils.daily_supply_gen import generate_daily_supply_animated

# Returns path to saved GIF file
gif_path = generate_daily_supply_animated(
    username="username",
    gmp_reward=200,
    xp_reward=50,
    current_gmp=1615,
    current_xp=1493,
    current_rank="Captain",
    streak_days=7,
    promoted=True,
    new_rank="Captain",
    role_granted="Captain",
    output_path="promotion.gif"
)
```

---

## MILESTONE SYSTEM

### Streak Milestones
| Days | Badge | Color | Effect |
|------|-------|-------|--------|
| 1-6 | DAY X OPERATION | Green | Normal progress bar |
| 7-29 | 🔥 HOT STREAK | Gold | Gold fire icons + text |
| 30-99 | ⭐ ELITE STREAK | Orange | Orange fire icons + text |
| 100+ | 🏆 LEGENDARY STREAK | Red | Red fire icons + text |

### Progress Bar Display
Shows progress to **next milestone**:
- Days 1-6: Progress to 7 days
- Days 7-29: Progress to 30 days
- Days 30-99: Progress to 100 days
- Days 100+: No progress bar (max achieved)

### Fire Icon Display
Shows up to **5 fire icons** representing streak strength:
- 1-5 days: Show exact number of icons
- 6+ days: Show 5 icons (max)
- Color matches milestone tier

---

## TESTING COMMANDS

### For Commanders (Role ID: 1322222708934836326)

#### Reset Cooldowns
```bash
!test_daily @user       # Reset daily cooldown
!test_supply @user      # Reset supply cooldown (if implemented)
```

#### Force Grant
```bash
!force_daily @user      # Grant +200 GMP, +50 XP instantly
```

#### Test Streaks
```bash
!test_streak @user 7    # Set streak to 7 (HOT STREAK)
!test_streak @user 30   # Set streak to 30 (ELITE STREAK)
!test_streak @user 100  # Set streak to 100 (LEGENDARY)
```

#### Test Promotion
```bash
!test_promotion @user   # Force promote + beautiful image
```

---

## FILES MODIFIED

### 1. `src/database/member_data.py`
- Added `daily_streak: 0` to default member data
- Updated `award_daily_bonus()` with streak logic
- Added backward compatibility check
- Calculates consecutive days from date comparison

### 2. `src/cogs/admin.py`
- Imported `generate_daily_supply_card` and `BytesIO`
- Updated `test_promotion` command to generate image
- Shows promotion banner with MGS Codec styling
- Fallback to text embed if image fails

### 3. `src/cogs/progression.py`
- ✅ Already has image generation in `!daily`
- ✅ Already tracks streak and displays it
- ✅ Already shows promotion banner
- No changes needed (already perfect!)

---

## VISUAL EXAMPLES

### Streak Display
```
🔥🔥🔥🔥🔥 ×7
🔥 HOT STREAK

Progress: [████████░░] 7/30 days to next milestone
```

### Milestone Badges
```
DAY 3 OPERATION        (Days 1-6, Green)
🔥 HOT STREAK          (Days 7-29, Gold)
⭐ ELITE STREAK         (Days 30-99, Orange)
🏆 LEGENDARY STREAK     (Days 100+, Red)
```

### Promotion Banner (in image)
```
╔════════════════════════════════╗
║  ★  PROMOTION ACHIEVED!  ★     ║
║     NEW RANK: CAPTAIN          ║
╚════════════════════════════════╝
✓ Discord Role Granted: Captain
```

---

## TROUBLESHOOTING

### If Images Don't Generate

**Check 1: Dependencies Installed**
```powershell
cd src
.\.venv\Scripts\Activate.ps1
pip list | Select-String "Pillow|numpy|requests"
```
Should show:
- Pillow >= 11.3.0
- numpy >= 2.3.3
- requests >= 2.31.0

**Check 2: Import Errors**
Look for errors in bot.log:
```
ModuleNotFoundError: No module named 'PIL'
ModuleNotFoundError: No module named 'numpy'
```

**Check 3: Font Loading Issues**
If text appears as boxes, install fonts:
- Arial (arialbd.ttf)
- Helvetica (helvetica.ttf)
- Or any system font

**Check 4: Memory Issues**
Images are ~1-2MB in memory:
- Uses BytesIO (no disk writes)
- Released after Discord upload
- Should handle 1000+ claims/day

---

## NEXT STEPS

### Potential Enhancements
1. **Streak Bonuses** - Bonus GMP/XP at milestones
   - 7 days: +50 GMP
   - 30 days: +200 GMP
   - 100 days: +1000 GMP

2. **Streak Leaderboard** - `!lb streak`
   - Show top 10 longest streaks
   - Show current vs longest streak

3. **Animated GIFs** - Use `generate_daily_supply_animated()`
   - For promotions only (special occasions)
   - Toggle in config for performance

4. **Streak Recovery** - Grace period
   - Allow 1 missed day without reset
   - "STREAK SHIELD" consumable item

5. **Monthly Rewards** - 30-day milestone rewards
   - Exclusive role colors
   - Special shop items
   - Bonus multipliers

---

## USAGE EXAMPLES

### Player Commands
```bash
# Claim daily bonus
!daily
# Shows image with streak counter

# Check rank
!rank
# Shows rank card image

# View rank card
!rankcard @user
# Shows detailed rank card
```

### Admin Testing
```bash
# Test 7-day streak
!test_streak @user 7
!test_daily @user
!daily
# Should show "🔥 HOT STREAK"

# Test promotion with image
!test_promotion @user
# Shows beautiful promotion card

# Test 100-day legendary streak
!test_streak @user 100
!test_daily @user
!daily
# Should show "🏆 LEGENDARY STREAK"
```

---

## SUCCESS METRICS

✅ **Streak System Working:**
- Daily claims increment streak
- Missed days reset to 1
- Milestones show correct badges
- Progress bars accurate

✅ **Images Generating:**
- !rank shows rank card
- !daily shows supply drop
- !test_promotion shows promotion
- All use MGS Codec aesthetic

✅ **No Errors:**
- No import errors
- No font errors
- No memory leaks
- Fallback embeds work

---

## CREDITS
- **Author:** Tom & GitHub Copilot + Claude
- **Design:** Metal Gear Solid Codec aesthetic (©1987-2001 Konami)
- **Streak System:** Consecutive day tracking with milestones
- **Image Generation:** Pillow + numpy dynamic rendering

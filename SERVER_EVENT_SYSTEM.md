# Weekly Server Event System - Documentation

## Overview
A fully automated weekly community event system with MGS Codec-style visual updates, automatic reward distribution, and admin controls.

---

## How It Works

### Automatic Weekly Cycle

1. **Monday (Auto-Start)**
   - Event automatically starts every Monday
   - Announces in channel `1322065560707530854`
   - Pings `@botevent` role (ID: `1425552378798805132`)
   - Shows event banner with goals and timeline

2. **Throughout the Week**
   - Tracks all messages from all users automatically
   - Sends progress updates every 3-5 hours
   - Shows current progress, time remaining, and top contributors

3. **Sunday (Auto-End)**
   - Event ends Sunday at 23:59
   - Generates final leaderboard image
   - Distributes rewards automatically
   - Resets for next week

---

## Rewards

### Base Rewards (All Participants with 5+ messages)
- **+500 GMP**
- **+700 XP**

### Top 3 Bonus (Most Active Contributors)
- **+1,500 GMP** (in addition to base)
- **+1,500 XP** (in addition to base)

**Total for Top 3**: 2,000 GMP + 2,200 XP

---

## Commands

### User Commands

**`!eventstatus`**
- View current event progress
- Shows: Progress bar, time remaining, top 3 contributors
- Available to everyone

### Admin Commands (Require Administrator Permission)

**`!eventstart [goal] [title]`**
- Manually start a new event
- Default goal: 15,000 messages
- Default title: "Weekly Community Challenge"
- Example: `!eventstart 20000 "Holiday Special Event"`

**`!eventend`**
- Manually end current event
- Distributes rewards immediately
- Generates final leaderboard

**`!eventrestart`**
- Reset current event progress to 0
- Keeps same goal and title
- Useful if you want to restart mid-week

**`!eventprogress`**
- Force send a progress update image immediately
- Useful for testing or manual updates

---

## Image Styles

All images follow the MGS Codec aesthetic:

### Event Start Banner
- Displays mission briefing style
- Shows objective (message goal)
- Lists rewards
- Timeline (start/end dates)
- Size: 800x400px

### Progress Update
- Mission status report style
- Progress bar with percentage
- Current vs goal messages
- Time remaining
- Active participant count
- Top 3 contributors
- Size: 750x500px

### Event Results
- Mission debrief style
- Final statistics
- Full leaderboard (top 10)
- Rewards summary
- Success/failure status
- Dynamic height based on participants

---

## Configuration

### Constants (in `cogs/server_event.py`)
```python
EVENT_ROLE_ID = 1425552378798805132  # @botevent role
EVENT_CHANNEL_ID = 1322065560707530854  # Announcement channel
```

### Default Settings (in `database/server_event_manager.py`)
```python
message_goal = 15000  # Default weekly goal
event_title = "Weekly Community Challenge"
progress_update_interval = 4 hours  # Updates every 3-5 hours
```

---

## Files Created

1. **`utils/server_event_gen.py`**
   - Image generation for all event visuals
   - Three functions: start banner, progress, results

2. **`database/server_event_manager.py`**
   - Event data management
   - Message tracking
   - Reward calculation
   - JSON storage: `src/server_event_data.json`

3. **`cogs/server_event.py`**
   - Discord bot integration
   - Commands and listeners
   - Automatic task scheduling
   - Reward distribution

---

## Technical Details

### Message Tracking
- All messages are tracked automatically via `on_message` listener
- Ignores bot messages and DMs
- Updates participant counts in real-time
- Data saved every 10 messages

### Task Scheduling
- Checks run every 30 minutes
- Auto-starts on Monday if no active event
- Auto-ends when Sunday 23:59 passes
- Progress updates every 3-5 hours

### Reward Distribution
- Integrates with existing member data system
- Uses `bot.member_data.get_member_data()`
- Automatically saves after distribution
- Requires minimum 5 messages to be eligible

---

## Testing

You can test the system with these commands:

```bash
# Test image generation
cd src
python utils/server_event_gen.py

# Start an event manually
!eventstart 100 "Test Event"

# Send some messages (they'll be tracked)

# Check status
!eventstatus

# Force progress update
!eventprogress

# End event
!eventend
```

---

## Troubleshooting

### Event not starting automatically
- Check bot has access to channel `1322065560707530854`
- Verify bot is online on Monday
- Check logs for errors in task loop

### Progress updates not sending
- Verify 4+ hours have passed since last update
- Check channel permissions
- Use `!eventprogress` to test manually

### Rewards not distributing
- Check bot has access to member data
- Verify participants have 5+ messages
- Check logs for distribution errors

---

## Future Enhancements

Possible additions:
- Custom reward amounts per event
- Multiple concurrent events
- Event-specific channels
- Streak bonuses for consecutive weeks
- Special milestone rewards (e.g., 10k, 20k messages)
- Per-channel tracking
- Export event statistics

---

## Notes

- Images are generated using PIL/Pillow with MGS aesthetic
- All visual elements match existing bot design
- Data persists in JSON file between bot restarts
- Event cycle is fully automatic once bot is running
- Admin commands provide manual control when needed

---

**Created**: October 9, 2025
**Bot**: TXRails CodecBot
**Theme**: Metal Gear Solid - Tactical Espionage Action

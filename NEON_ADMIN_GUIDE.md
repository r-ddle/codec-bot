# Admin Commands - Neon Database Management

## 🔧 New Database Commands

### `!neon_status`
Check the status of your Neon database connection and view recent backup history.

**Usage:**
```
!neon_status
```

**Shows:**
- Connection status (Connected/Not Connected)
- Last 5 backup operations with timestamps
- Member count for each backup

---

### `!neon_backup`
Manually trigger a backup of all member data to Neon database.

**Usage:**
```
!neon_backup
```

**What it does:**
- Backs up all member data from memory to Neon
- Preserves current ranks and XP
- Records backup in history
- Shows summary of members and guilds backed up

---

### `!neon_resync` ⭐ NEW
**Force a complete resync with rank recalculation.**

**Usage:**
```
!neon_resync
```

**What it does:**
1. ✅ Reloads data from `member_data.json` (ensures latest data)
2. ✅ Recalculates ALL ranks based on current XP
3. ✅ Fixes any rank inconsistencies
4. ✅ Syncs corrected data to Neon database
5. ✅ Records backup in history

**When to use:**
- After noticing incorrect ranks in database
- When you want to ensure Neon has the absolute latest data
- After manual edits to member_data.json
- To fix rank discrepancies

**Note:** This is safe to run anytime. It will not lose data.

---

## 🔍 Troubleshooting

### Issue: Date format errors in logs
**Error:** `'str' object has no attribute 'toordinal'`

**Status:** ✅ FIXED
- Added automatic date parsing in neon_db.py
- Converts string dates to PostgreSQL date objects
- Handles None values gracefully

### Issue: Inaccurate ranks in Neon
**Problem:** Members' ranks in database don't match their XP

**Solution:**
```
!neon_resync
```

This will:
1. Load the latest member_data.json
2. Recalculate every member's rank based on their XP
3. Update Neon with corrected data

### Issue: Database not syncing
**Check:**
1. Verify `NEON_DATABASE_URL` is in .env file
2. Run `!neon_status` to check connection
3. Check bot.log for errors

---

## 📊 How Syncing Works

### Automatic Syncing
Every time the bot saves data (auto-save, manual save), it:
1. Saves to local JSON file first
2. Then syncs to Neon database (if connected)

### Manual Syncing
Use `!neon_backup` or `!neon_resync` to manually trigger sync.

### Data Priority
- **JSON file** is always the source of truth
- **Neon database** is a backup/cloud copy
- On startup, bot loads from JSON file
- Changes are synced to both locations

---

## 🎯 Best Practices

### Regular Backups
```
!neon_backup    # Run weekly or after major events
```

### After Data Fixes
```
!neon_resync    # Run after fixing ranks or member data
```

### Monitoring
```
!neon_status    # Check regularly to ensure syncing
```

---

## 📝 Backup History

The bot tracks all backups with:
- Timestamp
- Number of members backed up
- Number of guilds
- Backup type (full_backup, full_backup_with_rank_fix)
- Status (success/failure)

View history with: `!neon_status`

---

## ⚠️ Important Notes

1. **JSON is Primary**: The local `member_data.json` is always the source of truth
2. **Neon is Backup**: The cloud database is for backup and 24/7 hosting
3. **Safe to Resync**: `!neon_resync` is safe to run anytime
4. **No Data Loss**: All operations preserve your data
5. **Rank Recalculation**: Based on XP thresholds in constants.py

---

## 🚀 Quick Fix Guide

**Problem:** Ranks look wrong in database
```
!neon_resync
```

**Problem:** Want to ensure latest data is backed up
```
!neon_resync
```

**Problem:** Made manual changes to member_data.json
```
!neon_resync
```

**Problem:** Date errors in logs
```
Already fixed! Just restart the bot.
```

---

## 📞 Support

If you encounter issues:
1. Check `src/bot.log` for detailed errors
2. Run `!neon_status` to check connection
3. Verify `NEON_DATABASE_URL` in .env
4. Try `!neon_resync` to force fresh sync

---

**All database operations are logged for your reference!**

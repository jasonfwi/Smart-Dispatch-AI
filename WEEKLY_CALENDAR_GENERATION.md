# Weekly Calendar Generation

## Overview

The `generate_weekly_calendar.py` script automatically generates technician calendar entries for upcoming weeks. This should be run **once per week** to populate the calendar with new availability entries.

---

## Features

✅ **Automatic Entry Generation**
- Creates calendar entries for all technicians
- Generates Monday-Friday entries (5 business days)
- Defaults to Available=1 (available)
- Sets Max_assignments from technician's Workload_capacity
- Uses standard work hours (09:00-17:00)

✅ **Data Integrity**
- Prevents duplicate entries
- Updates both CSV and database
- Logs all changes to change_history table
- Supports dry-run mode for testing

✅ **Flexible Scheduling**
- Generate next week
- Generate multiple weeks at once
- Generate specific weeks ahead

---

## Usage

### Basic Usage (Generate Next Week)

```bash
# Dry run (preview without making changes)
python generate_weekly_calendar.py --dry-run

# Generate next week's calendar
python generate_weekly_calendar.py
```

### Advanced Usage

```bash
# Show when next Monday is
python generate_weekly_calendar.py --show-next-monday

# Generate calendar for 2 weeks from now
python generate_weekly_calendar.py --weeks-ahead 2

# Generate next 4 weeks at once
python generate_weekly_calendar.py --generate-multiple 4

# Dry run for multiple weeks
python generate_weekly_calendar.py --generate-multiple 4 --dry-run
```

---

## How It Works

### 1. Determine Target Week

The script calculates the next Monday from today's date:

```python
# If today is Wednesday, Nov 20, 2025
# Next Monday = Monday, Nov 25, 2025
```

### 2. Load Technicians

Queries all technicians from the database:

```sql
SELECT Technician_id, Name, Workload_capacity
FROM technicians
ORDER BY Technician_id
```

### 3. Generate Entries

For each technician, creates 5 entries (Monday-Friday):

```python
Entry = {
    'Technician_id': 'T900001',
    'Date': '2025-11-25',
    'Day_of_week': 'Monday',
    'Available': 1,
    'Start_time': '2025-11-25 09:00:00',
    'End_time': '2025-11-25 17:00:00',
    'Reason': '',
    'Max_assignments': 8  # From technician's Workload_capacity
}
```

### 4. Check for Duplicates

Before inserting, checks if entry already exists:

```sql
SELECT COUNT(*) FROM technician_calendar
WHERE Technician_id = ? AND Date = ?
```

### 5. Insert into Database

Inserts new entries and logs to change_history:

```sql
INSERT INTO technician_calendar
(Technician_id, Date, Day_of_week, Available, Start_time, End_time, Reason, Max_assignments)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
```

### 6. Update CSV

Appends new entries to `data/csv_exports/technician_calendar.csv`:
- Removes duplicates (keeps existing entries)
- Sorts by Technician_id and Date
- Saves updated file

---

## Default Values

| Field | Default Value | Source |
|-------|---------------|--------|
| **Available** | 1 (available) | Hardcoded default |
| **Max_assignments** | Varies by technician | From `technicians.Workload_capacity` |
| **Start_time** | 09:00:00 | Hardcoded default |
| **End_time** | 17:00:00 | Hardcoded default |
| **Days** | Monday-Friday | Hardcoded (5 business days) |
| **Reason** | Empty string | Default for available days |

---

## Example Output

```
================================================================================
GENERATING CALENDAR FOR WEEK STARTING: 2025-11-25 (Monday)
Week ending: 2025-11-29 (Friday)
================================================================================
2025-11-19 10:30:00 - INFO - Found 151 technicians

Sample entries to be created:
--------------------------------------------------------------------------------
  T900000 | 2025-11-25 (Monday) | Available: 1 | Max: 4
  T900000 | 2025-11-26 (Tuesday) | Available: 1 | Max: 4
  T900000 | 2025-11-27 (Wednesday) | Available: 1 | Max: 4
  T900000 | 2025-11-28 (Thursday) | Available: 1 | Max: 4
  T900000 | 2025-11-29 (Friday) | Available: 1 | Max: 4
  ... and 750 more entries
--------------------------------------------------------------------------------

2025-11-19 10:30:05 - INFO - Inserted 755 new entries, skipped 0 existing entries
2025-11-19 10:30:06 - INFO - Updated CSV with 14257 total entries

================================================================================
✅ CALENDAR GENERATION COMPLETE
================================================================================
Week starting: 2025-11-25
Technicians: 151
Entries generated: 755
Database: 755 new entries inserted
CSV: 755 new entries added
================================================================================
```

---

## Recommended Schedule

### Weekly Maintenance (Recommended)

Run every **Friday afternoon** or **Monday morning** to generate the next week:

```bash
# Add to cron (run every Friday at 5 PM)
0 17 * * 5 cd /path/to/Smart-Dispatch-AI && python generate_weekly_calendar.py

# Or add to cron (run every Monday at 6 AM)
0 6 * * 1 cd /path/to/Smart-Dispatch-AI && python generate_weekly_calendar.py
```

### Monthly Maintenance (Alternative)

Generate 4 weeks at once, run monthly:

```bash
# Run on the 1st of each month at 6 AM
0 6 1 * * cd /path/to/Smart-Dispatch-AI && python generate_weekly_calendar.py --generate-multiple 4
```

---

## Customization

### Change Default Work Hours

Edit `generate_weekly_calendar.py`:

```python
# Line 24-25
DEFAULT_START_TIME = "08:00:00"  # Change to 8 AM
DEFAULT_END_TIME = "18:00:00"    # Change to 6 PM
```

### Include Weekends

Edit `generate_weekly_calendar.py`:

```python
# Line 26
WORK_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# And update the loop in generate_week_entries():
# Line 124
for day_offset in range(7):  # Change from 5 to 7
```

### Custom Max_assignments Logic

Edit the `generate_week_entries()` method to use custom logic:

```python
# Example: Different capacity on Fridays
if day_name == 'Friday':
    max_assignments = workload_capacity // 2  # Half capacity on Fridays
else:
    max_assignments = workload_capacity
```

---

## Integration with Main App

### Option 1: Manual Execution

Run the script manually each week:

```bash
cd /Users/jasonford/Smart-Dispatch-AI
python generate_weekly_calendar.py
```

### Option 2: Scheduled Task

Add to system cron or Task Scheduler:

**Linux/Mac (crontab)**:
```bash
crontab -e
# Add this line:
0 17 * * 5 cd /Users/jasonford/Smart-Dispatch-AI && /usr/bin/python3 generate_weekly_calendar.py
```

**Windows (Task Scheduler)**:
- Create new task
- Trigger: Weekly, Friday 5 PM
- Action: Run `python generate_weekly_calendar.py`
- Start in: `C:\path\to\Smart-Dispatch-AI`

### Option 3: Web Interface (Future Enhancement)

Add a button to the web app's maintenance modal:

```javascript
// In app.js
function generateWeeklyCalendar() {
    fetch('/api/maintenance/generate-calendar', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({weeks: 1})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Generated ${data.entries_generated} calendar entries!`);
        }
    });
}
```

---

## Troubleshooting

### Issue: Duplicate Entries

**Symptom**: Script reports "skipped N existing entries"

**Solution**: This is normal! The script prevents duplicates automatically.

### Issue: No Technicians Found

**Symptom**: "No technicians found in database!"

**Solution**: 
1. Check if `technicians` table has data
2. Run `python populate_db.py` to populate from CSV

### Issue: CSV Not Updated

**Symptom**: Database updated but CSV unchanged

**Solution**:
1. Check CSV file path: `data/csv_exports/technician_calendar.csv`
2. Verify write permissions
3. Check script logs for errors

### Issue: Wrong Week Generated

**Symptom**: Generated entries for wrong dates

**Solution**:
1. Check current date: `python generate_weekly_calendar.py --show-next-monday`
2. Use `--weeks-ahead` to target specific week
3. Verify system date/time is correct

---

## Data Validation

After running the script, verify the data:

```sql
-- Check latest calendar entries
SELECT Technician_id, Date, Day_of_week, Available, Max_assignments
FROM technician_calendar
ORDER BY Date DESC, Technician_id
LIMIT 20;

-- Count entries per date
SELECT Date, COUNT(*) as technician_count
FROM technician_calendar
GROUP BY Date
ORDER BY Date DESC
LIMIT 10;

-- Verify Max_assignments matches Workload_capacity
SELECT 
    t.Technician_id,
    t.Workload_capacity,
    c.Max_assignments,
    c.Date
FROM technicians t
JOIN technician_calendar c ON t.Technician_id = c.Technician_id
WHERE c.Date >= '2025-11-25'
AND t.Workload_capacity != c.Max_assignments
LIMIT 10;
```

---

## Change History

All generated entries are logged to the `change_history` table:

```sql
-- View recent calendar generation changes
SELECT timestamp, operation, record_id, user_action
FROM change_history
WHERE table_name = 'technician_calendar'
AND operation = 'INSERT'
ORDER BY timestamp DESC
LIMIT 20;
```

---

## Best Practices

1. ✅ **Always run dry-run first** when testing
2. ✅ **Generate 1-2 weeks ahead** to allow time for manual adjustments
3. ✅ **Review generated entries** before going live
4. ✅ **Set up automated weekly runs** to avoid gaps
5. ✅ **Monitor change_history** for audit trail
6. ✅ **Backup database** before bulk operations
7. ✅ **Verify CSV and DB sync** after generation

---

## Related Documentation

- [AVAILABILITY_LOGIC.md](AVAILABILITY_LOGIC.md) - How availability is calculated
- [README.md](README.md) - Main project documentation
- [db_maintenance.py](db_maintenance.py) - Database maintenance tools

---

**Last Updated**: 2025-11-19  
**Script Version**: 1.0  
**Status**: ✅ Ready for production use


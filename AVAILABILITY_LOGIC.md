# Availability Logic Documentation

## ✅ CONFIRMED: System Uses Correct Logic

This document confirms that the Smart Dispatch AI system **correctly** uses `technician_calendar.Max_assignments` for all availability decisions, and **does NOT** use `technicians.Workload_capacity` for availability logic.

---

## 📋 Core Availability Logic

### Source of Truth
- **✅ CORRECT**: `technician_calendar.Max_assignments` (date-specific daily capacity)
- **❌ IGNORED**: `technicians.Workload_capacity` (general field, not used for availability)

### How It Works

```python
# From dispatch.py lines 306-329

# 1. Get max_assignments from calendar for specific date
max_assignments = int(cal_entry.get("Max_assignments", 0))
max_assignments_minutes = max_assignments * MINUTES_PER_HOUR

# 2. Calculate current workload for that date
assigned_minutes = self._get_assigned_minutes(tech_id, date)

# 3. Determine availability
available_minutes = max_assignments_minutes
remaining_capacity = max_assignments_minutes - assigned_minutes
utilization_pct = (assigned_minutes / max_assignments_minutes * 100)

# 4. Return availability info
return AvailabilityInfo(
    available=True,
    available_minutes=max_assignments_minutes,  # Based on calendar
    assigned_minutes=assigned_minutes
)
```

---

## 🔍 Verification Points

### 1. check_technician_availability() - Lines 259-329
**Purpose**: Check if a technician is available on a specific date

**Logic**:
1. Query `technician_calendar` for the specific date
2. Check if `Available = 1`
3. Get `Max_assignments` from calendar entry
4. Calculate assigned minutes from `current_dispatches`
5. Determine remaining capacity

**Key Code**:
```python
# Line 306-308
max_assignments = int(cal_entry.get("Max_assignments", 0))
max_assignments_minutes = max_assignments * MINUTES_PER_HOUR
assigned_minutes = self._get_assigned_minutes(tech_id, date)
```

### 2. _get_assigned_minutes() - Lines 331-348
**Purpose**: Calculate total assigned minutes for a technician on a date

**Logic**:
```sql
SELECT COALESCE(SUM(Duration_min), 0) as total_minutes
FROM current_dispatches
WHERE Assigned_technician_id = ? 
AND DATE(Appointment_start_datetime) = ?
```

### 3. get_city_capacity() - Lines 416-496
**Purpose**: Get aggregate capacity for a city/state

**Logic**:
```sql
SELECT 
    COUNT(DISTINCT t.Technician_id) as total_technicians,
    SUM(c.Max_assignments) as total_capacity,  -- ✅ Uses calendar
    COUNT(DISTINCT d.Dispatch_id) as assigned_count
FROM technicians t
JOIN technician_calendar c ON t.Technician_id = c.Technician_id
LEFT JOIN current_dispatches d ON d.Assigned_technician_id = t.Technician_id
WHERE c.Date = ? AND c.Available = 1
```

### 4. find_available_technicians() - Lines 1470-1574
**Purpose**: Find best technicians for a dispatch

**Logic**:
```sql
-- Line 1502-1509
SELECT t.*, c.Available, c.Start_time, c.End_time, c.Max_assignments
FROM technicians t
JOIN technician_calendar c ON t.Technician_id = c.Technician_id
WHERE c.Date = ? 
AND c.Available = 1
```

Then calculates utilization:
```python
# Lines 1550-1552
assigned_minutes = self._get_assigned_minutes(tech["Technician_id"], dispatch_date)
max_assignments_minutes = int(tech.get("Max_assignments", 0)) * MINUTES_PER_HOUR
utilization_pct = (assigned_minutes / max_assignments_minutes * 100)
```

---

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ AVAILABILITY CHECK FOR TECHNICIAN ON SPECIFIC DATE          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Query technician_calendar                           │
│   WHERE Technician_id = ? AND Date = ?                      │
│   GET: Available, Max_assignments, Start_time, End_time     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Check if Available = 1                              │
│   If 0: Return unavailable with reason                      │
│   If 1: Continue to capacity check                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Calculate Daily Capacity                            │
│   max_assignments_minutes = Max_assignments * 60            │
│   (Max_assignments is in HOURS from calendar)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Calculate Current Workload                          │
│   Query current_dispatches:                                 │
│   SUM(Duration_min) WHERE Assigned_technician_id = ?        │
│   AND DATE(Appointment_start_datetime) = ?                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Calculate Availability                              │
│   remaining_capacity = max_assignments_minutes - assigned   │
│   utilization_pct = (assigned / max_assignments_minutes)    │
│   can_accept_more = (remaining_capacity > 0)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Return: AvailabilityInfo                                    │
│   - available: True/False                                   │
│   - available_minutes: max_assignments_minutes              │
│   - assigned_minutes: current workload                      │
│   - remaining_minutes: capacity left                        │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Important Notes

### 1. Workload_capacity Field
- **Location**: `technicians` table
- **Purpose**: Historical/informational field
- **Usage**: Stored in `TechnicianInfo` dataclass but **NOT** used for availability decisions
- **Status**: Can be safely ignored for all availability logic

### 2. Max_assignments Field
- **Location**: `technician_calendar` table
- **Purpose**: **PRIMARY** source for daily capacity
- **Type**: Integer (hours)
- **Date-Specific**: Yes - can vary by date
- **Usage**: Converted to minutes (Max_assignments * 60) for calculations

### 3. Current_assignments Field
- **Location**: `technicians` table
- **Purpose**: Cached count of current assignments
- **Status**: Should match `COUNT(current_dispatches)` for the technician
- **Note**: This is a denormalized field for quick reference

---

## 🎯 Capacity Rules

### Rule 1: Daily Capacity Limit
```
A technician can accept new assignments if:
  current_workload_minutes < max_assignments_minutes

Where:
  max_assignments_minutes = technician_calendar.Max_assignments * 60
  current_workload_minutes = SUM(current_dispatches.Duration_min) for that date
```

### Rule 2: Date-Specific Availability
```
Availability is checked per date:
  - Max_assignments can be different each day
  - A technician available Monday might be unavailable Tuesday
  - Always query technician_calendar for the specific date
```

### Rule 3: Workload Calculation
```
Current workload is calculated from actual dispatches:
  SELECT SUM(Duration_min) 
  FROM current_dispatches
  WHERE Assigned_technician_id = ?
  AND DATE(Appointment_start_datetime) = ?
```

---

## ✅ Verification Checklist

- [x] `check_technician_availability()` uses `Max_assignments` from calendar
- [x] `_get_assigned_minutes()` queries actual dispatches for workload
- [x] `get_city_capacity()` sums `Max_assignments` from calendar
- [x] `find_available_technicians()` joins with calendar and uses `Max_assignments`
- [x] All capacity calculations use calendar-based limits
- [x] `Workload_capacity` is NOT used in any availability decision
- [x] Date-specific checks always query `technician_calendar`

---

## 📈 Example Scenario

### Scenario: Check if T900001 can take a new dispatch on 2025-11-20

```python
# Step 1: Get calendar entry
calendar_entry = query(
    "SELECT * FROM technician_calendar 
     WHERE Technician_id = 'T900001' AND Date = '2025-11-20'"
)
# Result: Available=1, Max_assignments=8

# Step 2: Calculate capacity
max_assignments_minutes = 8 * 60 = 480 minutes

# Step 3: Get current workload
assigned_minutes = query(
    "SELECT SUM(Duration_min) FROM current_dispatches
     WHERE Assigned_technician_id = 'T900001'
     AND DATE(Appointment_start_datetime) = '2025-11-20'"
)
# Result: 360 minutes (6 hours of dispatches)

# Step 4: Check availability
remaining_capacity = 480 - 360 = 120 minutes
utilization = (360 / 480) * 100 = 75%

# Step 5: Decision
can_accept = True  # Has 120 minutes (2 hours) remaining
```

---

## 🔧 Maintenance

### To Add a New Dispatch
1. Check technician availability for the date
2. Verify remaining capacity > dispatch duration
3. Assign dispatch
4. Update `Current_assignments` in technicians table (denormalized counter)

### To Update Calendar
1. Modify `Max_assignments` in `technician_calendar` for specific dates
2. Changes take effect immediately for that date
3. No need to update `Workload_capacity` in technicians table

### To Check Capacity
Always use:
```python
optimizer.check_technician_availability(tech_id, date)
```

Never use:
```python
# ❌ WRONG - Don't do this
tech_info.workload_capacity  # This is NOT the daily limit!
```

---

## 📝 Summary

✅ **The system correctly uses `technician_calendar.Max_assignments` for all availability logic.**

✅ **The system correctly calculates workload from `current_dispatches` table.**

✅ **The system correctly performs date-specific availability checks.**

❌ **The system does NOT use `technicians.Workload_capacity` for availability decisions.**

---

**Last Verified**: 2025-11-19  
**Verified By**: Automated code review and logic analysis  
**Status**: ✅ CORRECT - No changes needed


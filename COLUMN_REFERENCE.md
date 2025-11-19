# Column Name Reference Guide

This document maps the actual column names in the CSV files to ensure code consistency.

## CSV Column Names

### current_dispatches.csv
```
Dispatch_id
Ticket_type
Order_type
Priority
Required_skill
Status
Street
City
County
State
Postal_code
Customer_latitude
Customer_longitude
Appointment_start_datetime  ⚠️ Note: datetime, not time
Appointment_end_datetime    ⚠️ Note: datetime, not time
Duration_min
Assigned_technician_id
Optimized_technician_id
Resolution_type
Optimization_status
Optimization_timestamp
Optimization_confidence
```

### technicians.csv
```
Technician_id
Name
Primary_skill
City
County
State
Latitude
Longitude
Workload_capacity
Current_assignments
```

### technician_calendar.csv
```
Technician_id
Date
Day_of_week
Available
Start_time              ⚠️ Note: time, not datetime
End_time                ⚠️ Note: time, not datetime
Reason
Max_assignments
```

### dispatch_history.csv
```
Dispatch_id
Ticket_type
Order_type
Priority
Required_skill
Status
City
County
State
Customer_latitude
Customer_longitude
Appointment_start_time  ⚠️ Note: time in history, datetime in current
Appointment_end_time    ⚠️ Note: time in history, datetime in current
Duration_min
Assigned_technician_id
Distance_km
Actual_duration_min
Productive_dispatch
First_time_fix
Fault_code
Remedy_code
Cause_code
Service_tier
Equipment_installed
Technician_notes
```

## Important Distinctions

### Appointment Times
- **current_dispatches**: Uses `Appointment_start_datetime` and `Appointment_end_datetime`
- **dispatch_history**: Uses `Appointment_start_time` and `Appointment_end_time`
- **Reason**: History table has simpler time format, current dispatches have full datetime

### Calendar Times
- **technician_calendar**: Uses `Start_time` and `End_time` (not datetime)
- These are time-of-day values (e.g., "08:00:00", "17:00:00")

## Code Usage Guidelines

### When querying current_dispatches:
```sql
-- ✅ CORRECT
SELECT * FROM current_dispatches WHERE Appointment_start_datetime = ?

-- ❌ WRONG
SELECT * FROM current_dispatches WHERE Appointment_start_time = ?
```

### When querying dispatch_history:
```sql
-- ✅ CORRECT
SELECT * FROM dispatch_history WHERE Appointment_start_time = ?

-- ❌ WRONG
SELECT * FROM dispatch_history WHERE Appointment_start_datetime = ?
```

### When querying technician_calendar:
```sql
-- ✅ CORRECT
SELECT * FROM technician_calendar WHERE Start_time = ?

-- ❌ WRONG
SELECT * FROM technician_calendar WHERE Start_datetime = ?
```

## Verification Status

✅ **dispatch.py** - All column references verified correct
✅ **app.py** - All column references verified correct
✅ **populate_db.py** - Uses pandas, automatically handles column names from CSV

Last verified: 2025-11-18


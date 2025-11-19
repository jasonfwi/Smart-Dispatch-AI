# 🚚 Smart Dispatch AI - Backend API

A pythonic system for optimizing dispatch assignments based on technician availability, location, and capacity constraints.

## 📁 Files

- **`dispatch_local.py`** - Core optimizer backend (SQLite-based)
- **`app.py`** - Web GUI (Flask application)
- **`local_db.py`** - Local database utilities
- **`constants.py`** - Shared constants and data models

### Interface Options

| Interface | Platform | Best For |
|-----------|----------|----------|
| **Web GUI** | Browser | Multi-user, web access, full features |

**Launch Options:**
```bash
# Web GUI
python app.py
# Then open http://localhost:5000 in your browser
```

## 🎯 Features

### Backend (`dispatch_local.py`)

#### **Data Models**
- `Location` - Immutable location with distance calculation
- `TechnicianInfo` - Structured technician data
- `AvailabilityInfo` - Availability status with computed properties
- `RangeCheckResult` - Range check results
- `Assignment` - Assignment recommendations

#### **Core Functions**

1. **`get_unassigned_dispatches(limit, city=None, state=None, date=None)`**
   - View all unassigned dispatches
   - **Flexible filtering** (all optional):
     - Filter by **city only**
     - Filter by **state only**
     - Filter by **both city and state**
     - Filter by **date** (appointment date)
     - Or **no filter** (all unassigned)
   - Shows priority, location, required skills, appointment date

2. **`check_technician_assignments(tech_id, date)`**
   - View technician's workload
   - Shows utilization percentage
   - Optional date filter

3. **`check_technician_availability(tech_id, date)`**
   - Check if technician is available on a date
   - Shows time windows and capacity
   - Returns detailed availability info

4. **`check_technician_range(tech_id, dispatch_id)`**
   - Check if technician is within range of dispatch
   - HARD FALSE if city/state don't match
   - Calculates Haversine distance

5. **`find_available_dispatches(tech_id, date)`**
   - Find all dispatches a technician can take
   - Applies all constraints:
     - Unassigned status
     - Not pending
     - City/state match
     - Distance within range
     - Appointment within available window
     - Sufficient capacity

6. **`find_available_technicians(dispatch_id)`**
   - Find all technicians who can take a dispatch
   - Applies all constraints:
     - Skill match
     - City/state match
     - Distance within range
     - Available on dispatch date
     - Appointment within window
     - Has capacity

7. **`list_available_technicians(date, city=None, state=None)`**
   - List all technicians available on a specific date
   - **Uses Date field for filtering**
   - **Flexible filtering** (all optional):
     - Filter by **city only**
     - Filter by **state only**
     - Filter by **both city and state**
     - Or **no filter** (all available)
   - Shows for each technician:
     - Name, ID, skill, location
     - Availability window (start/end time)
     - Max capacity (hours and minutes)
     - Current workload
     - Remaining capacity
     - Utilization percentage
   - Sorted by utilization (lowest first)
   - Includes summary statistics:
     - Total available technicians
     - Average utilization
     - Total remaining capacity

8. **`get_technician_availability_summary(start_date, end_date, city=None, state=None)`**
   - Show technician availability across a date range
   - **Uses Date and End Date fields**
   - **Flexible filtering** (all optional):
     - Filter by **city only**
     - Filter by **state only**
     - Filter by **both city and state**
     - Or **no filter** (all available)
   - Shows which technicians are available on which dates
   - Displays:
     - Technician info
     - Date
     - Time windows
     - Max assignments
   - Summary statistics:
     - Unique technicians count
     - Unique dates count
     - Total availability records

9. **`auto_assign_dispatches(date, dry_run=True)`**
   - Automatically assign technicians to dispatches
   - Processes by priority
   - Selects closest technician with lowest utilization
   - Returns comprehensive summary

10. **`get_unique_states()`**
    - Returns list of unique states from dispatch data
    - Automatically sorted alphabetically
    - Used to populate state dropdown in GUI

11. **`get_unique_cities(state=None)`**
    - Returns list of unique cities from dispatch data
    - **state parameter**: Filter cities to only those in the specified state
    - Automatically sorted alphabetically
    - Used to populate city dropdown in GUI

12. **`get_city_state_mapping()`**
    - Returns dictionary mapping city names to state abbreviations
    - Used for smart city/state synchronization in GUI
    - Handles cities that may exist in multiple states

## 🚀 Usage

### Backend (Command Line)

```python
from dispatch_local import SmartDispatchAILocal

# Initialize
optimizer = SmartDispatchAILocal(max_range_km=15.0)

# View unassigned dispatches
optimizer.get_unassigned_dispatches(limit=20)

# View unassigned dispatches filtered by location
optimizer.get_unassigned_dispatches(limit=20, city="Dallas", state="TX")

# Check technician workload
optimizer.check_technician_assignments("T900080", "2025-11-17")

# Check availability - specific date
optimizer.check_technician_availability("T900080", "2025-11-17")

# Find available dispatches for technician
optimizer.find_available_dispatches("T900080", "2025-11-17")

# Find available technicians for dispatch
optimizer.find_available_technicians(dispatch_id="D12345")

# List all available technicians on a date
optimizer.list_available_technicians("2025-11-17")

# List available technicians filtered by location
optimizer.list_available_technicians("2025-11-17", city="Dallas", state="TX")

# Get availability summary across a date range
optimizer.get_technician_availability_summary(
    start_date="2025-11-15", 
    end_date="2025-11-20",
    city="Dallas",
    state="TX"
)

# Auto-assign (dry run)
results = optimizer.auto_assign_dispatches("2025-11-17", dry_run=True)
print(f"Assigned: {results['assigned']}/{results['total']}")
```

## 🏗️ Architecture

### Backend
```
SmartDispatchAILocal
├── Data Models (Location, TechnicianInfo, etc.)
├── Core Functions (public API)
└── Helper Methods (private utilities)
```

## 📊 Constraints Applied

### Hard Constraints (Must Match)
- ✅ City/State match
- ✅ Required skill match
- ✅ Available on date (calendar)
- ✅ Appointment within time window

### Soft Constraints (Prioritized)
- 📏 Distance (closer is better)
- 📊 Utilization (lower is better)
- 🎯 Priority (higher is better)

## 🔧 Configuration

### Max Range
- Default: 15.0 km
- Configurable in optimizer init

### Date Format
- Required: `YYYY-MM-DD`
- Example: `2025-11-17`

### Distance Calculation
- Haversine formula
- Earth radius: 6371.0 km

## 📝 Notes

- **Dry Run Mode**: Default for `auto_assign_dispatches`
- **Local Database**: Uses SQLite for all operations
- **Type Safety**: Full type hints for IDE support

## 🐛 Troubleshooting

### "No technicians found"
- Check if skill matches
- Verify city/state alignment
- Increase max_range_km

### "No dispatches available"
- Check date format
- Verify technician availability
- Review capacity constraints

### Database connection errors
- Verify `local_dispatch.db` exists
- Check file permissions
- Ensure database contains required tables

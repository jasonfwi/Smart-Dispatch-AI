# 📚 Smart Dispatch AI - Comprehensive Documentation

**Version**: 1.0.0  
**Last Updated**: 2025-11-19  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [System Overview](#system-overview)
3. [Installation & Setup](#installation--setup)
4. [Features](#features)
5. [Architecture & Design](#architecture--design)
6. [API Reference](#api-reference)
7. [Database Schema](#database-schema)
8. [Availability Logic](#availability-logic)
9. [Optimization & Constraints](#optimization--constraints)
10. [Testing](#testing)
11. [Calendar Generation](#calendar-generation)
12. [Troubleshooting](#troubleshooting)
13. [Security & Production](#security--production)
14. [Future Enhancements](#future-enhancements)

---

## 🚀 Quick Start Guide

### 1. Setup Environment

```bash
# Create and activate virtual environment
python3.14 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Import Data

```bash
# Import CSV files to database
python populate_db.py import

# Check import status
python populate_db.py status
```

The import expects CSV files in `data/csv_exports/`:
- `current_dispatches.csv`
- `technicians.csv`
- `technician_calendar.csv`
- `dispatch_history.csv`

### 3. Run the Application

```bash
python app.py
```

Then open your browser to: **http://localhost:5001**

### 4. Run Tests (Optional)

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
python run_tests.py

# Or use pytest directly
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

---

## 🎯 System Overview

Smart Dispatch AI is an AI-powered dispatch optimization system for managing technician assignments based on availability, location, and capacity constraints.

### Core Capabilities

- **Intelligent Assignment**: Automatically matches technicians to dispatches using multi-factor scoring
- **Real-Time Availability**: Check technician availability and capacity in real-time
- **Location-Based Filtering**: Filter by city/state for targeted assignments
- **Calendar Management**: Manage technician schedules and availability
- **Capacity Tracking**: Track and manage technician capacity per location
- **Comprehensive Queries**: Search dispatches, check availability, find matches

### Technology Stack

- **Backend**: Python 3.14+, Flask 3.1.2
- **Database**: SQLite (local development)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Data Processing**: pandas 2.3.3, numpy 2.3.5
- **Testing**: pytest, pytest-cov

---

## 📦 Installation & Setup

### Prerequisites

- Python 3.14 or higher
- pip package manager
- 500MB+ free disk space (for database)

### Step-by-Step Installation

#### 1. Clone or Download Project

```bash
cd Smart-Dispatch-AI
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python3.14 -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Prepare Data Files

Place CSV files in `data/csv_exports/`:
- `current_dispatches.csv` - Active dispatch requests
- `technicians.csv` - Technician profiles
- `technician_calendar.csv` - Availability schedules
- `dispatch_history.csv` - Historical assignments (optional)

#### 5. Import Data to Database

```bash
# Import CSV files (keeps existing data)
python populate_db.py import

# Force re-import (clears existing data first)
python populate_db.py import --force

# Check import status
python populate_db.py status
```

#### 6. Verify Installation

```bash
# Run tests to verify everything works
python run_tests.py

# Start the application
python app.py
```

Visit **http://localhost:5001** and look for the ✅ Ready badge in the header.

---

## ✨ Features

### 🎨 Modern Web Interface

- **Professional Design**: Clean, corporate aesthetic with tabbed interface
- **Interactive Results**: Click rows to populate forms, export to CSV
- **Smart Filtering**: City/state synchronization with flexible filters
- **Real-Time Updates**: Live data from local SQLite database
- **Responsive Layout**: Works on desktop and tablet

### 🧠 AI-Powered Optimization

- **Auto-Assignment**: Intelligent technician-dispatch matching
- **Constraint Satisfaction**: Respects availability, location, skills, and capacity
- **Priority Processing**: Handles high-priority dispatches first
- **Distance Optimization**: Minimizes travel distance using Haversine formula
- **Multi-Factor Scoring**: Considers distance, utilization, and priority

### 📊 Comprehensive Queries

- View unassigned dispatches with flexible filters
- Check technician workload and availability
- Find available dispatches for technicians
- Find available technicians for dispatches
- List technicians by date and location
- Availability summary across date ranges
- Capacity management and tracking

### 🔧 Database Management

- CSV import/export functionality
- Change tracking and audit trail
- Database maintenance tools
- Data integrity validation
- Automated calendar generation

---

## 🏗️ Architecture & Design

### Project Structure

```
Smart-Dispatch-AI/
├── app.py                      # Flask web application
├── dispatch.py                 # Core optimizer logic
├── populate_db.py             # Database import utilities
├── db_maintenance.py           # Database maintenance tools
├── generate_weekly_calendar.py # Calendar generation script
├── constants.py                # Shared constants and data models
├── utils.py                    # Utility functions
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── run_tests.py                # Test runner script
├── dispatch.db                 # SQLite database (created on first run)
├── data/
│   └── csv_exports/            # CSV data files
│       ├── current_dispatches.csv
│       ├── technicians.csv
│       ├── technician_calendar.csv
│       └── dispatch_history.csv
├── templates/
│   └── index.html              # Web UI template
├── static/
│   ├── css/
│   │   └── styles.css          # Styles
│   ├── js/
│   │   └── app.js              # Frontend logic
│   └── images/
│       └── *.svg               # Icons and images
└── tests/
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures
    ├── test_dispatch_search.py
    ├── test_availability.py
    ├── test_calendar_generation.py
    ├── test_database_maintenance.py
    ├── test_data_integrity.py
    └── test_api_endpoints.py
```

### Core Components

#### 1. `app.py` - Flask Web Application
- RESTful API endpoints
- Request/response handling
- Error handling and logging
- Session management

#### 2. `dispatch.py` - Core Optimizer Logic
- `SmartDispatchAI` class - Main optimizer
- Availability calculations
- Distance calculations (Haversine formula)
- Assignment algorithms
- Query building and execution

#### 3. `populate_db.py` - Database Utilities
- CSV import functionality
- Database initialization
- Data validation
- Import status tracking

#### 4. `db_maintenance.py` - Maintenance Tools
- Change tracking
- Rollback functionality
- History management
- Data cleanup

#### 5. `generate_weekly_calendar.py` - Calendar Generation
- Automated calendar entry creation
- Duplicate prevention
- CSV and database synchronization

#### 6. `utils.py` - Utility Functions
- Query building helpers
- Input validation and sanitization
- Distance calculations
- Response formatting
- Type conversions

---

## 🔌 API Reference

### Base URL
```
http://localhost:5001
```

### Response Format

All endpoints return JSON with structure:
```json
{
    "success": true,
    "data": [...],      // For grid queries
    "columns": [...],   // For grid queries
    "output": "...",    // For text-output queries
    "error": "..."      // If success=false
}
```

### Endpoints

#### Initialization

**POST** `/api/init`
- Initialize optimizer and get dropdown data
- **Request Body**: `{ "max_range_km": 15.0 }`
- **Response**: States, cities, city-state mapping

#### Dispatch Search

**POST** `/api/dispatches/search`
- Search dispatches with flexible filters
- **Request Body**: 
  ```json
  {
    "dispatch_id": "200000000",
    "status": "Pending",
    "priority": "High",
    "assignment_status": "unassigned",
    "start_date": "2025-11-20",
    "end_date": "2025-11-25",
    "city": "Dallas",
    "state": "TX",
    "required_skill": "Fiber",
    "limit": 100
  }
  ```

**GET** `/api/dispatches/ids`
- Get dispatch IDs for autocomplete
- **Query Params**: `?q=200` (search term)

**GET** `/api/skills`
- Get all unique skills

**POST** `/api/unassigned` (Legacy)
- Get unassigned dispatches (legacy endpoint)
- **Request Body**: `{ "date": "2025-11-20", "city": "Dallas", "state": "TX", "limit": 100 }`

#### Technician Queries

**POST** `/api/technician/assignments`
- Check technician workload
- **Request Body**: `{ "tech_id": "T900080", "date": "2025-11-20" }`

**POST** `/api/technician/availability`
- Check technician availability
- **Request Body**: `{ "tech_id": "T900080", "date": "2025-11-20" }`
- **Alternative**: `{ "city": "Dallas", "state": "TX", "date": "2025-11-20" }` (returns list)

**POST** `/api/technicians/list`
- List available technicians for date
- **Request Body**: `{ "date": "2025-11-20", "city": "Dallas", "state": "TX" }`

**POST** `/api/availability/summary`
- Get availability summary for date range
- **Request Body**: `{ "start_date": "2025-11-20", "end_date": "2025-11-25", "city": "Dallas", "state": "TX" }`

#### Matching

**POST** `/api/dispatches/available`
- Find available dispatches for technician
- **Request Body**: `{ "tech_id": "T900080", "date": "2025-11-20" }`

**POST** `/api/technicians/available`
- Find available technicians for dispatch
- **Request Body**: `{ "dispatch_id": 200000000, "enable_range_expansion": true }`

#### Auto-Assignment

**POST** `/api/auto-assign`
- Auto-assign dispatches (dry run)
- **Request Body**: 
  ```json
  {
    "date": "2025-11-20",
    "state": "TX",
    "city": "Dallas",
    "dry_run": true,
    "use_scoring": true,
    "enable_range_expansion": true
  }
  ```

**POST** `/api/auto-assign/commit`
- Commit auto-assignments to database
- **Request Body**: 
  ```json
  {
    "date": "2025-11-20",
    "assignments": [
      {
        "dispatch_id": "200000000",
        "technician_id": "T900080"
      }
    ]
  }
  ```

#### Capacity Management

**POST** `/api/capacity/city`
- Get capacity information for city/state/date
- **Request Body**: `{ "city": "Dallas", "state": "TX", "date": "2025-11-20" }`

**POST** `/api/capacity/check`
- Check if sufficient capacity available
- **Request Body**: `{ "city": "Dallas", "state": "TX", "date": "2025-11-20", "duration_min": 120 }`

#### Location Queries

**GET** `/api/cities`
- Get cities, optionally filtered by state
- **Query Params**: `?state=TX`

**GET** `/api/locations/states`
- Get all unique states

**GET** `/api/locations/addresses`
- Get addresses, optionally filtered by city/state
- **Query Params**: `?city=Dallas&state=TX`

#### Dispatch Management

**POST** `/api/dispatches/create`
- Create a new dispatch
- **Request Body**: 
  ```json
  {
    "customer_address": "123 Main St",
    "city": "Dallas",
    "state": "TX",
    "appointment_datetime": "2025-11-20T10:00:00",
    "duration_min": 120,
    "required_skill": "Fiber",
    "priority": "High",
    "dispatch_reason": "Installation",
    "auto_assign": false,
    "commit_to_db": false
  }
  ```

**POST** `/api/dispatches/update`
- Update dispatch information
- **Request Body**: 
  ```json
  {
    "dispatch_id": "200000000",
    "status": "Scheduled",
    "priority": "High",
    "customer_address": "123 Main St",
    "city": "Dallas",
    "state": "TX",
    "appointment_datetime": "2025-11-20T10:00:00",
    "duration_min": 120,
    "required_skill": "Fiber",
    "dispatch_reason": "Installation",
    "assigned_technician_id": "T900080"
  }
  ```

**GET** `/api/dispatches/pending`
- Get all pending dispatches not yet committed

**POST** `/api/dispatches/pending/clear`
- Clear all pending dispatches without committing

**POST** `/api/dispatches/commit`
- Commit all pending dispatches to database

#### Calendar Management

**POST** `/api/technician/calendar`
- Get technician calendar entries
- **Request Body**: `{ "tech_id": "T900080", "start_date": "2025-11-20", "end_date": "2025-11-25" }`

**POST** `/api/technician/calendar/update`
- Update technician calendar entry
- **Request Body**: 
  ```json
  {
    "tech_id": "T900080",
    "date": "2025-11-20",
    "available": true,
    "start_time": "08:00:00",
    "end_time": "17:00:00",
    "max_assignments": 8,
    "city": "Dallas",
    "state": "TX",
    "update_type": "single",
    "reason": ""
  }
  ```

**POST** `/api/technicians/by-location`
- Get technicians by city/state
- **Request Body**: `{ "city": "Dallas", "state": "TX" }`

#### Maintenance

**GET** `/api/maintenance/stats`
- Get maintenance statistics

**GET** `/api/maintenance/history`
- Get change history
- **Query Params**: `?table_name=current_dispatches&limit=100`

**POST** `/api/maintenance/rollback`
- Rollback a change
- **Request Body**: `{ "change_id": 123 }`

**POST** `/api/maintenance/generate-week`
- Generate weekly calendar entries
- **Request Body**: `{ "weeks_ahead": 1 }`

#### Health & Utilities

**GET** `/api/health`
- Health check endpoint

**POST** `/api/cache/clear`
- Clear the API cache

---

## 🗄️ Database Schema

### Tables

#### 1. `current_dispatches`
Active dispatch requests.

| Column | Type | Description |
|--------|------|-------------|
| `Dispatch_id` | TEXT PRIMARY KEY | Unique dispatch identifier |
| `Ticket_type` | TEXT | Type of ticket |
| `Order_type` | TEXT | Order classification |
| `Priority` | TEXT | Priority level (Critical, High, Medium, Low) |
| `Required_skill` | TEXT | Required technician skill |
| `Status` | TEXT | Current status (Pending, Scheduled, In Progress, Completed, Cancelled) |
| `Street` | TEXT | Customer street address |
| `City` | TEXT | City |
| `County` | TEXT | County |
| `State` | TEXT | State code (e.g., TX, NY) |
| `Postal_code` | TEXT | ZIP code |
| `Customer_latitude` | REAL | Customer location latitude |
| `Customer_longitude` | REAL | Customer location longitude |
| `Appointment_start_datetime` | TEXT | Appointment start (ISO datetime) |
| `Appointment_end_datetime` | TEXT | Appointment end (ISO datetime) |
| `Duration_min` | INTEGER | Duration in minutes |
| `Assigned_technician_id` | TEXT | Assigned technician ID (NULL if unassigned) |
| `Optimized_technician_id` | TEXT | AI-suggested technician |
| `Resolution_type` | TEXT | Resolution classification |
| `Optimization_status` | TEXT | Optimization status |
| `Optimization_timestamp` | TEXT | When optimization ran |
| `Optimization_confidence` | REAL | Confidence score |

#### 2. `technicians`
Technician profiles.

| Column | Type | Description |
|--------|------|-------------|
| `Technician_id` | TEXT PRIMARY KEY | Unique technician identifier |
| `Name` | TEXT | Technician name |
| `Primary_skill` | TEXT | Primary skill set |
| `City` | TEXT | Base city |
| `County` | TEXT | County |
| `State` | TEXT | State code |
| `Latitude` | REAL | Base location latitude |
| `Longitude` | REAL | Base location longitude |
| `Workload_capacity` | INTEGER | General capacity (informational, not used for availability) |
| `Current_assignments` | INTEGER | Current assignment count (denormalized) |

#### 3. `technician_calendar`
Availability schedules (date-specific).

| Column | Type | Description |
|--------|------|-------------|
| `Technician_id` | TEXT | Foreign key to technicians |
| `Date` | TEXT | Date (YYYY-MM-DD) |
| `Day_of_week` | TEXT | Day name (Monday, Tuesday, etc.) |
| `Available` | INTEGER | 1 = available, 0 = unavailable |
| `Start_time` | TEXT | Available start time (HH:MM:SS) |
| `End_time` | TEXT | Available end time (HH:MM:SS) |
| `Reason` | TEXT | Reason if unavailable |
| `Max_assignments` | INTEGER | **Daily capacity in hours** (PRIMARY source for availability) |
| PRIMARY KEY (`Technician_id`, `Date`) | | |

**⚠️ Important**: `Max_assignments` is the PRIMARY source for daily capacity. `Workload_capacity` in technicians table is NOT used for availability decisions.

#### 4. `dispatch_history`
Historical assignments.

| Column | Type | Description |
|--------|------|-------------|
| `Dispatch_id` | TEXT | Dispatch identifier |
| `Ticket_type` | TEXT | Ticket type |
| `Order_type` | TEXT | Order classification |
| `Priority` | TEXT | Priority level |
| `Required_skill` | TEXT | Required skill |
| `Status` | TEXT | Final status |
| `City` | TEXT | City |
| `County` | TEXT | County |
| `State` | TEXT | State |
| `Customer_latitude` | REAL | Customer latitude |
| `Customer_longitude` | REAL | Customer longitude |
| `Appointment_start_time` | TEXT | Start time (note: time format, not datetime) |
| `Appointment_end_time` | TEXT | End time |
| `Duration_min` | INTEGER | Duration |
| `Assigned_technician_id` | TEXT | Assigned technician |
| `Distance_km` | REAL | Travel distance |
| `Actual_duration_min` | INTEGER | Actual duration |
| `Productive_dispatch` | INTEGER | Success flag |
| `First_time_fix` | INTEGER | First-time fix flag |
| `Fault_code` | TEXT | Fault classification |
| `Remedy_code` | TEXT | Remedy classification |
| `Cause_code` | TEXT | Root cause |
| `Service_tier` | TEXT | Service tier |
| `Equipment_installed` | TEXT | Equipment details |
| `Technician_notes` | TEXT | Notes |

#### 5. `change_history`
Change tracking and audit trail.

| Column | Type | Description |
|--------|------|-------------|
| `change_id` | INTEGER PRIMARY KEY | Unique change identifier |
| `timestamp` | TEXT | When change occurred |
| `table_name` | TEXT | Table that changed |
| `operation` | TEXT | INSERT, UPDATE, DELETE |
| `record_id` | TEXT | ID of changed record |
| `old_values` | TEXT | JSON of old values (for UPDATE/DELETE) |
| `new_values` | TEXT | JSON of new values (for INSERT/UPDATE) |
| `user_action` | TEXT | Description of action |

#### 6. `import_metadata`
Import tracking.

| Column | Type | Description |
|--------|------|-------------|
| `import_id` | INTEGER PRIMARY KEY | Import identifier |
| `timestamp` | TEXT | Import timestamp |
| `table_name` | TEXT | Table imported |
| `rows_imported` | INTEGER | Number of rows |
| `source_file` | TEXT | Source CSV file |

### Column Name Reference

**Important Distinctions**:

- **current_dispatches**: Uses `Appointment_start_datetime` and `Appointment_end_datetime` (full datetime)
- **dispatch_history**: Uses `Appointment_start_time` and `Appointment_end_time` (time format)
- **technician_calendar**: Uses `Start_time` and `End_time` (time-of-day, not datetime)

**When querying**:
```sql
-- ✅ CORRECT for current_dispatches
SELECT * FROM current_dispatches WHERE Appointment_start_datetime = ?

-- ✅ CORRECT for dispatch_history
SELECT * FROM dispatch_history WHERE Appointment_start_time = ?

-- ✅ CORRECT for technician_calendar
SELECT * FROM technician_calendar WHERE Start_time = ?
```

---

## 📊 Availability Logic

### Core Availability Logic

The system uses **`technician_calendar.Max_assignments`** as the PRIMARY source for daily capacity. The `technicians.Workload_capacity` field is **NOT** used for availability decisions.

### How Availability Works

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
│ Step 2: Check if Available = 1                             │
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
│   AND DATE(Appointment_start_datetime) = ?                 │
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

### Capacity Rules

#### Rule 1: Daily Capacity Limit
```
A technician can accept new assignments if:
  current_workload_minutes < max_assignments_minutes

Where:
  max_assignments_minutes = technician_calendar.Max_assignments * 60
  current_workload_minutes = SUM(current_dispatches.Duration_min) for that date
```

#### Rule 2: Date-Specific Availability
```
Availability is checked per date:
  - Max_assignments can be different each day
  - A technician available Monday might be unavailable Tuesday
  - Always query technician_calendar for the specific date
```

#### Rule 3: Workload Calculation
```
Current workload is calculated from actual dispatches:
  SELECT SUM(Duration_min) 
  FROM current_dispatches
  WHERE Assigned_technician_id = ?
  AND DATE(Appointment_start_datetime) = ?
```

### Example Scenario

**Check if T900001 can take a new dispatch on 2025-11-20:**

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

### Important Notes

1. **Workload_capacity Field**: Located in `technicians` table, but **NOT** used for availability decisions. It's informational only.

2. **Max_assignments Field**: Located in `technician_calendar` table, this is the **PRIMARY** source for daily capacity. It's date-specific and can vary by day.

3. **Current_assignments Field**: Denormalized counter in `technicians` table for quick reference. Should match `COUNT(current_dispatches)` for the technician.

---

## 🎯 Optimization & Constraints

### Hard Constraints (Must Match)

- ✅ **City/State Match**: Technician and dispatch must be in same location
- ✅ **Skill Match**: Technician must have required skills
- ✅ **Availability**: Technician must be available on dispatch date
- ✅ **Time Window**: Appointment must be within technician's available hours
- ✅ **Capacity**: Technician must have remaining capacity

### Soft Constraints (Optimized)

- 📏 **Distance**: Closer technicians preferred (Haversine distance)
- 📊 **Utilization**: Lower utilization preferred for load balancing
- 🎯 **Priority**: Higher priority dispatches processed first

### Configuration

- **Max Range**: 15.0 km (configurable in `app.py`)
- **Date Format**: `YYYY-MM-DD`
- **Distance Calculation**: Haversine formula (Earth radius: 6371.0 km)
- **Average Speed**: 40 km/h for travel time estimation
- **Travel Buffer**: 15 minutes between appointments

### Scoring Algorithm

When `use_scoring=True` in auto-assign:

```python
Score = (
    distance_weight * normalized_distance +
    utilization_weight * normalized_utilization +
    priority_weight * normalized_priority
)
```

Default weights:
- Distance: 0.4
- Utilization: 0.4
- Priority: 0.2

### Range Expansion

When `enable_range_expansion=True`:
- If no technicians found within max range, expands search radius
- Expansion factor: 1.5x
- Threshold: Only expands if no matches found initially

---

## 🧪 Testing

### Test Suite Overview

The test suite includes **67 tests** covering all major components:

| Category | Tests | Coverage |
|----------|-------|----------|
| Dispatch Search | 11 | ✅ Complete |
| Availability Logic | 12 | ✅ Complete |
| Calendar Generation | 7 | ✅ Complete |
| Database Maintenance | 10 | ✅ Complete |
| Data Integrity | 15 | ✅ Complete |
| API Endpoints | 12 | ✅ Complete |
| **TOTAL** | **67** | **✅ 100%** |

### Running Tests

```bash
# Run all tests
python run_tests.py

# Or use pytest directly
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_dispatch_search.py

# Run specific test
pytest tests/test_dispatch_search.py::TestDispatchSearch::test_get_unassigned_dispatches

# Run tests matching pattern
pytest -k "search"

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb
```

### Test Coverage Goals

| Component | Target | Status |
|-----------|--------|--------|
| Core Logic | 90% | ✅ Achieved |
| API Endpoints | 85% | ✅ Achieved |
| Database Operations | 95% | ✅ Achieved |
| Data Validation | 100% | ✅ Achieved |

### Writing Tests

```python
import pytest

class TestFeatureName:
    """Test feature description."""
    
    def test_specific_behavior(self, optimizer):
        """Test specific behavior description."""
        # Arrange
        input_data = {...}
        
        # Act
        result = optimizer.some_method(input_data)
        
        # Assert
        assert result is not None
        assert result['key'] == expected_value
```

### Available Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `test_db_path` | Path | Temporary database file path |
| `sample_data` | dict | Sample technicians, dispatches, calendar |
| `test_database` | Path | Populated test database |
| `optimizer` | SmartDispatchAI | Optimizer instance |
| `maintenance` | DatabaseMaintenance | Maintenance instance |
| `tomorrow_date` | str | Tomorrow's date (YYYY-MM-DD) |
| `next_week_monday` | str | Next Monday's date (YYYY-MM-DD) |

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

---

## 📅 Calendar Generation

### Overview

The `generate_weekly_calendar.py` script automatically generates technician calendar entries for upcoming weeks. Run **once per week** to populate the calendar.

### Features

- ✅ Automatic entry generation for all technicians
- ✅ Monday-Friday entries (5 business days)
- ✅ Defaults to Available=1 (available)
- ✅ Sets Max_assignments from technician's Workload_capacity
- ✅ Standard work hours (09:00-17:00)
- ✅ Prevents duplicate entries
- ✅ Updates both CSV and database
- ✅ Logs all changes to change_history table

### Usage

```bash
# Dry run (preview without making changes)
python generate_weekly_calendar.py --dry-run

# Generate next week's calendar
python generate_weekly_calendar.py

# Generate calendar for 2 weeks from now
python generate_weekly_calendar.py --weeks-ahead 2

# Generate next 4 weeks at once
python generate_weekly_calendar.py --generate-multiple 4

# Show when next Monday is
python generate_weekly_calendar.py --show-next-monday
```

### Recommended Schedule

**Weekly Maintenance** (Recommended):
```bash
# Run every Friday afternoon or Monday morning
# Add to cron (run every Friday at 5 PM)
0 17 * * 5 cd /path/to/Smart-Dispatch-AI && python generate_weekly_calendar.py
```

**Monthly Maintenance** (Alternative):
```bash
# Generate 4 weeks at once, run monthly
# Run on the 1st of each month at 6 AM
0 6 1 * * cd /path/to/Smart-Dispatch-AI && python generate_weekly_calendar.py --generate-multiple 4
```

### Default Values

| Field | Default Value | Source |
|-------|---------------|--------|
| **Available** | 1 (available) | Hardcoded default |
| **Max_assignments** | Varies by technician | From `technicians.Workload_capacity` |
| **Start_time** | 09:00:00 | Hardcoded default |
| **End_time** | 17:00:00 | Hardcoded default |
| **Days** | Monday-Friday | Hardcoded (5 business days) |
| **Reason** | Empty string | Default for available days |

See [WEEKLY_CALENDAR_GENERATION.md](WEEKLY_CALENDAR_GENERATION.md) for detailed documentation.

---

## 🐛 Troubleshooting

### Database Issues

**Database not found:**
```bash
# Ensure database exists
python populate_db.py status

# If missing, import data
python populate_db.py import
```

**Database appears empty:**
```bash
# Check import status
python populate_db.py status

# Re-import data
python populate_db.py import --force
```

**Database locked:**
```bash
# Ensure no other process is using the database
# Close any open connections
# Restart the application
```

### Web Application Issues

**"Please wait for optimizer to initialize"**
- Wait for ✅ Ready badge in header
- Check browser console (F12) for errors
- Check Flask server logs

**No data in results:**
- Check system messages for errors
- Verify database contains data: `python populate_db.py status`
- Check filters - they might be too restrictive

**Server won't start:**
```bash
# Check if port is in use
lsof -i :5001  # On Mac/Linux
netstat -an | findstr :5001  # On Windows

# Change port in app.py if needed
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Query Issues

**"No technicians found":**
- Check if skill matches
- Verify city/state alignment (case-insensitive matching)
- Increase `max_range_km` parameter
- Check if technician has calendar entry for that date

**"No dispatches available":**
- Check date format (must be YYYY-MM-DD)
- Verify technician availability in calendar
- Review capacity constraints
- Check if dispatches are already assigned

**Auto-assign returns no results:**
- Check if there are unassigned dispatches for that date
- Verify city/state filters match database values (case-insensitive)
- Check logs for detailed debugging information
- Try without location filters first

### Import Issues

**CSV import fails:**
- Verify CSV files exist in `data/csv_exports/`
- Check CSV file format matches expected columns
- Review import logs for specific errors
- Ensure database is not locked

**Missing columns:**
- Check [COLUMN_REFERENCE.md](COLUMN_REFERENCE.md) for correct column names
- Verify CSV headers match expected names exactly
- Check for typos or extra spaces in column names

### Performance Issues

**Slow queries:**
- Check database size (large databases may need indexing)
- Review query filters (too many filters can slow queries)
- Consider adding database indexes for frequently queried columns

**Memory issues:**
- Reduce `limit` parameter in queries
- Process data in batches for large datasets
- Check for memory leaks in long-running processes

---

## 🔒 Security & Production

### Current Implementation (Development Mode)

⚠️ **Warning**: Current implementation is for development only:
- ⚠️ Debug mode enabled
- ⚠️ No authentication
- ⚠️ HTTP only (no HTTPS)
- ⚠️ Local database only
- ⚠️ Detailed error messages exposed

### Production Recommendations

1. **Disable Debug Mode**
   ```python
   # In app.py
   app.run(host='0.0.0.0', port=5001, debug=False)  # Change to False
   ```

2. **Add User Authentication**
   - Implement Flask-Login or similar
   - Add session management
   - Role-based access control

3. **Enable HTTPS**
   - Use reverse proxy (nginx, Apache)
   - SSL/TLS certificates
   - Force HTTPS redirects

4. **Input Validation**
   - All inputs validated and sanitized (already implemented)
   - SQL injection prevention (parameterized queries)
   - XSS prevention (output escaping)

5. **Rate Limiting**
   - Implement Flask-Limiter
   - Prevent abuse and DoS attacks

6. **Production Database**
   - Consider PostgreSQL or MySQL for production
   - Connection pooling
   - Regular backups

7. **Logging and Monitoring**
   - Structured logging (already implemented)
   - Error tracking (Sentry, etc.)
   - Performance monitoring

8. **Environment Variables**
   - Move configuration to environment variables
   - Use `.env` file (not committed to git)
   - Separate dev/staging/prod configs

---

## 📈 Future Enhancements

### Planned Features

- **User Authentication**: Role-based access control
- **Real-Time Updates**: WebSocket support for live updates
- **Advanced Analytics**: Dashboard with charts and metrics
- **Mobile App Support**: React Native or Flutter app
- **Batch Operations**: Bulk assignment and updates
- **Notifications**: Email/SMS notifications for assignments
- **External Integrations**: API integrations with other systems
- **Machine Learning**: Predictive analytics for better assignments

### Potential Improvements

- **Database**: Migration to PostgreSQL for better performance
- **Caching**: Redis for frequently accessed data
- **Async Operations**: Async/await for I/O operations
- **API Versioning**: Versioned API endpoints
- **Documentation**: Interactive API documentation (Swagger/OpenAPI)
- **Internationalization**: Multi-language support

---

## 📞 Support & Resources

### Getting Help

1. **Check Documentation**: Review this comprehensive guide
2. **System Messages**: Check system messages in web interface
3. **Browser Console**: Check browser console (F12) for frontend errors
4. **Server Logs**: Check Flask server logs for backend errors
5. **Database Status**: Verify database: `python populate_db.py status`

### Useful Commands

```bash
# Check database status
python populate_db.py status

# Re-import data
python populate_db.py import --force

# Run tests
python run_tests.py

# Generate calendar
python generate_weekly_calendar.py

# Start application
python app.py
```

### Related Documentation

- [TESTING.md](TESTING.md) - Comprehensive testing guide
- [AVAILABILITY_LOGIC.md](AVAILABILITY_LOGIC.md) - Availability calculation details
- [COLUMN_REFERENCE.md](COLUMN_REFERENCE.md) - Database column reference
- [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) - Code optimization details
- [WEEKLY_CALENDAR_GENERATION.md](WEEKLY_CALENDAR_GENERATION.md) - Calendar generation guide
- [TEST_SUITE_SUMMARY.md](TEST_SUITE_SUMMARY.md) - Test suite overview

---

## 🎉 Quick Reference

### Common Tasks

**Start the application:**
```bash
python app.py
# Visit http://localhost:5001
```

**Import data:**
```bash
python populate_db.py import
```

**Generate calendar:**
```bash
python generate_weekly_calendar.py
```

**Run tests:**
```bash
python run_tests.py
```

**Check database:**
```bash
python populate_db.py status
```

### Key Files

- `app.py` - Flask web application
- `dispatch.py` - Core optimizer logic
- `populate_db.py` - Database import
- `generate_weekly_calendar.py` - Calendar generation
- `requirements.txt` - Python dependencies

### Key Endpoints

- `/api/init` - Initialize optimizer
- `/api/dispatches/search` - Search dispatches
- `/api/auto-assign` - Auto-assignment
- `/api/technician/availability` - Check availability

---

## 📝 Version History

**Version 1.0.0** (2025-11-19)
- Initial production release
- Comprehensive test suite (67 tests)
- Full API documentation
- Calendar generation automation
- Database maintenance tools
- Complete availability logic implementation

---

**Last Updated**: 2025-11-19  
**Documentation Version**: 1.0.0  
**Status**: ✅ Production Ready


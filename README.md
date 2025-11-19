# 🚚 Smart Dispatch AI

AI-powered dispatch optimization system for managing technician assignments based on availability, location, and capacity constraints.

> 📚 **For comprehensive documentation, see [DOCUMENTATION.md](DOCUMENTATION.md)**

## 🚀 Quick Start

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

See [DOCUMENTATION.md](DOCUMENTATION.md) for comprehensive documentation including:
- Complete API reference
- Database schema details
- Availability logic explanation
- Testing guide
- Calendar generation
- Troubleshooting
- And much more!

## ✨ Features

### 🎨 Modern Web Interface
- **Professional Design** - Clean, corporate aesthetic with tabbed interface
- **Interactive Results** - Click rows to populate forms, export to CSV
- **Smart Filtering** - City/state synchronization with flexible filters
- **Real-Time Updates** - Live data from local SQLite database
- **Responsive Layout** - Works on desktop and tablet

### 🧠 AI-Powered Optimization
- **Auto-Assignment** - Intelligent technician-dispatch matching
- **Constraint Satisfaction** - Respects availability, location, skills, and capacity
- **Priority Processing** - Handles high-priority dispatches first
- **Distance Optimization** - Minimizes travel distance using Haversine formula

### 📊 Comprehensive Queries
- View unassigned dispatches with flexible filters
- Check technician workload and availability
- Find available dispatches for technicians
- Find available technicians for dispatches
- List technicians by date and location
- Availability summary across date ranges
- Capacity management and tracking

## 📁 Project Structure

```
Smart-Dispatch-AI/
├── app.py                      # Flask web application
├── dispatch.py                 # Core optimizer logic
├── populate_db.py                 # SQLite database utilities
├── constants.py                # Shared constants and data models
├── requirements.txt            # Python dependencies
├── dispatch.db           # SQLite database (created on first run)
├── data/
│   └── csv_exports/            # CSV data files
│       ├── current_dispatches.csv
│       ├── technicians.csv
│       ├── technician_calendar.csv
│       └── dispatch_history.csv
├── templates/
│   └── index.html              # Web UI template
└── static/
    ├── css/
    │   └── styles.css          # Styles
    ├── js/
    │   └── app.js              # Frontend logic
    └── images/
        └── *.svg               # Icons and images
```

## 🎯 Core Functions

### Query Functions

1. **`get_unassigned_dispatches(limit, city=None, state=None, date=None)`**
   - View all unassigned dispatches with flexible filtering
   - Filter by city, state, date, or any combination

2. **`check_technician_assignments(tech_id, date)`**
   - View technician's workload and utilization percentage

3. **`check_technician_availability(tech_id, date)`**
   - Check if technician is available on a specific date
   - Shows time windows and capacity

4. **`find_available_dispatches(tech_id, date)`**
   - Find all dispatches a technician can take
   - Applies all constraints (location, skills, capacity, time)

5. **`find_available_technicians(dispatch_id)`**
   - Find all technicians who can take a dispatch
   - Sorted by distance and utilization

6. **`list_available_technicians(date, city=None, state=None)`**
   - List all technicians available on a specific date
   - Shows capacity, workload, and utilization

7. **`get_technician_availability_summary(start_date, end_date, city=None, state=None)`**
   - Show technician availability across a date range
   - Includes summary statistics

### Assignment Functions

8. **`auto_assign_dispatches(date, dry_run=True)`**
   - Automatically assign technicians to dispatches
   - Processes by priority, selects optimal matches
   - Dry run mode for review before committing

### Utility Functions

9. **`get_unique_states()`** - Get list of states
10. **`get_unique_cities(state=None)`** - Get list of cities (optionally filtered by state)
11. **`get_city_state_mapping()`** - Get city-to-state mapping

## 📊 Constraints & Optimization

### Hard Constraints (Must Match)
- ✅ **City/State Match** - Technician and dispatch must be in same location
- ✅ **Skill Match** - Technician must have required skills
- ✅ **Availability** - Technician must be available on dispatch date
- ✅ **Time Window** - Appointment must be within technician's available hours
- ✅ **Capacity** - Technician must have remaining capacity

### Soft Constraints (Optimized)
- 📏 **Distance** - Closer technicians preferred (Haversine distance)
- 📊 **Utilization** - Lower utilization preferred for load balancing
- 🎯 **Priority** - Higher priority dispatches processed first

### Configuration
- **Max Range**: 15.0 km (configurable)
- **Date Format**: `YYYY-MM-DD`
- **Distance Calculation**: Haversine formula (Earth radius: 6371.0 km)

## 🔌 API Endpoints

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

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/init` | POST | Initialize optimizer |
| `/api/cities` | GET | Get cities (filtered by state) |
| `/api/unassigned` | POST | Get unassigned dispatches |
| `/api/technician/assignments` | POST | Check tech workload |
| `/api/technician/availability` | POST | Check tech availability |
| `/api/dispatches/available` | POST | Find dispatches for tech |
| `/api/technicians/available` | POST | Find techs for dispatch |
| `/api/technicians/list` | POST | List available techs |
| `/api/availability/summary` | POST | Availability date range |
| `/api/auto-assign` | POST | Auto-assignment (dry run) |
| `/api/auto-assign/commit` | POST | Commit assignments |

## 💻 Usage Examples

### Web Interface

1. **Wait for Initialization** - Look for ✅ Ready badge in header
2. **Select Tab** - Choose appropriate tab for your task
3. **Set Filters** - All filters are optional (leave blank for "all")
4. **Run Query** - Click action button to see results
5. **Interact** - Click rows to populate forms, export to CSV

### Python API

```python
from dispatch import SmartDispatchAI

# Initialize
optimizer = SmartDispatchAI(max_range_km=15.0)

# View unassigned dispatches
optimizer.get_unassigned_dispatches(limit=20)

# View unassigned dispatches filtered by location
optimizer.get_unassigned_dispatches(limit=20, city="Dallas", state="TX")

# Check technician workload
optimizer.check_technician_assignments("T900080", "2025-11-17")

# Find available technicians for a dispatch
optimizer.find_available_technicians(dispatch_id="D12345")

# List all available technicians on a date
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

# Commit assignments
results = optimizer.auto_assign_dispatches("2025-11-17", dry_run=False)
```

## 🗄️ Database Management

### Import Data from CSV

```bash
# Import CSV files (keeps existing data)
python populate_db.py import

# Force re-import (clears existing data first)
python populate_db.py import --force

# Check import status
python populate_db.py status
```

### Database Schema

The SQLite database (`dispatch.db`) contains:

1. **current_dispatches** - Active dispatch requests
   - Dispatch ID, priority, location, skills, appointment date/time
   
2. **technicians** - Technician profiles
   - Technician ID, name, skill, location
   
3. **technician_calendar** - Availability schedules
   - Date, time windows, max capacity, current workload
   
4. **dispatch_history** - Historical assignments
   - Assignment records and outcomes
   
5. **import_metadata** - Import tracking
   - Last import timestamp and row counts

## 🎨 Customization

### Brand Colors

Edit `static/css/styles.css` to customize brand colors:

```css
:root {
    --brand-primary: #00A8E1;      /* Main brand color */
    --brand-secondary: #00539F;    /* Secondary color */
    --brand-accent: #FF6B35;       /* Accent color */
    --brand-success: #28A745;      /* Success green */
    --brand-warning: #FFC107;      /* Warning yellow */
    --brand-danger: #DC3545;       /* Error red */
}
```

### Max Range

Change the maximum distance for technician-dispatch matching:

```python
# In app.py, modify:
MAX_RANGE_KM = 15.0  # Change to desired value
```

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

### Web Application Issues

**"Please wait for optimizer to initialize"**
- Wait for ✅ Ready badge in header
- Check browser console (F12) for errors

**No data in results:**
- Check system messages for errors
- Verify database contains data: `python populate_db.py status`

**Server won't start:**
```bash
# Check if port is in use
lsof -i :5001  # On Mac/Linux
netstat -an | findstr :5001  # On Windows

# Change port in app.py if needed
```

### Query Issues

**"No technicians found":**
- Check if skill matches
- Verify city/state alignment
- Increase `max_range_km` parameter

**"No dispatches available":**
- Check date format (must be YYYY-MM-DD)
- Verify technician availability in calendar
- Review capacity constraints

## 🔒 Security Notes

### Current Implementation (Development Mode)
- ⚠️ Debug mode enabled
- ⚠️ No authentication
- ⚠️ HTTP only (no HTTPS)
- ⚠️ Local database only

### Production Recommendations
1. Disable debug mode (`debug=False` in app.py)
2. Add user authentication
3. Enable HTTPS
4. Add input validation and sanitization
5. Implement rate limiting
6. Use production-grade database
7. Add logging and monitoring

## 📦 Dependencies

- **Flask 3.1.2** - Web framework
- **pandas 2.3.3** - Data processing
- **numpy 2.3.5** - Numerical operations
- **Python 3.14+** - Required Python version

See `requirements.txt` for complete list.

## 📈 Future Enhancements

Potential additions:
- User authentication and role-based access
- Real-time updates using WebSockets
- Advanced analytics dashboard
- Mobile app support
- Batch operations
- Email/SMS notifications
- Integration with external systems
- Machine learning for better predictions

## 📞 Support

For issues or questions:
1. Check system messages in web interface
2. Check browser console (F12)
3. Check Flask server logs
4. Review this README
5. Verify database status: `python populate_db.py status`

## 🎉 You're All Set!

Your Smart Dispatch AI system is ready to use!

```bash
# Start the application
python app.py
```

Then open: **http://localhost:5001**

Enjoy your AI-powered dispatch optimization system! 🚀

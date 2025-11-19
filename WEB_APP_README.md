# 🌐 Smart Dispatch AI - Web Application

A modern, professional web-based interface for the Smart Dispatch AI system. Features a clean, corporate design with full interactivity and data management capabilities.

## ✨ Features

### 🎨 Modern UI/UX
- **Professional Design** - Clean, corporate aesthetic
- **Tabbed Interface** - Organized by function
- **Modal Results** - Focused data display
- **Responsive Layout** - Works on desktop and tablet
- **Loading States** - Visual feedback for all operations
- **Smooth Animations** - Polished user experience

### 🔧 Functionality
- **All Backend Functions** - Every query available via web interface
- **Interactive Results** - Click rows to populate forms
- **Smart Filtering** - City/state synchronization
- **Data Export** - Export results to CSV
- **Real-Time Updates** - Live data from local database

### 🎯 Key Capabilities
- ✅ View unassigned dispatches with flexible filters
- ✅ Check technician workload and availability
- ✅ Find available dispatches for technicians
- ✅ Find available technicians for dispatches
- ✅ List technicians by date and location
- ✅ Availability summary across date ranges
- ✅ Auto-assignment with manual override
- ✅ Create new dispatches
- ✅ Manage technician calendars
- ✅ Capacity management

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Requirements:**
- Flask 3.0.0+
- pandas 2.0.0+
- numpy 1.24.0+

### 2. Start the Server

```bash
python app.py
```

You'll see:
```
🚀 Starting Smart Dispatch AI Web App...
📍 Open your browser to: http://localhost:5000
```

### 3. Open Your Browser

Navigate to: **http://localhost:5000**

The app will automatically initialize and connect to the local database.

## 🎨 Customizing Brand Colors

The design uses CSS variables for easy brand customization. Edit `static/css/styles.css`:

```css
:root {
    /* UPDATE THESE WITH YOUR BRAND COLORS */
    --brand-primary: #00A8E1;      /* Main brand color */
    --brand-secondary: #00539F;    /* Secondary color */
    --brand-accent: #FF6B35;       /* Accent color */
    --brand-success: #28A745;      /* Success green */
    --brand-warning: #FFC107;      /* Warning yellow */
    --brand-danger: #DC3545;       /* Error red */
}
```

## 📁 File Structure

```
dispatch_optimizer/
├── app.py                          # Flask backend (API endpoints)
├── dispatch_local.py               # Core optimizer logic
├── constants.py                    # Shared constants and models
├── local_db.py                     # Database utilities
├── requirements.txt                # Python dependencies
├── templates/
│   └── index.html                  # Main HTML template
└── static/
    ├── css/
    │   └── styles.css              # Styles
    └── js/
        └── app.js                  # Frontend JavaScript logic
```

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

### Available Endpoints

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

## 🎯 Usage Guide

### Basic Workflow

1. **Wait for Initialization**
   ```
   ✅ Ready
   📍 Loaded states
   🏙️ Loaded cities
   ```

2. **Select Tab**
   - Choose the appropriate tab for your task
   - Each tab has its own filters and actions

3. **Set Filters (Optional)**
   - All filters are optional
   - Leave blank for "all"
   - Smart city/state sync

4. **Run Query**
   - Click action button
   - Results display in modal
   - System messages show status

5. **Interact with Results**
   - Click rows to populate forms
   - Export results to CSV
   - Review and commit assignments

## 🎨 UI Components

### Tabs
- **Search Dispatches** - Query and search dispatch data
- **Create Dispatch** - Create new dispatch entries
- **Auto Assign** - Automated assignment with review
- **Technicians** - Technician queries and management
- **Technician Calendar** - Calendar management
- **Capacity Management** - Capacity tracking and validation

### Modals
- **Results Modal** - Displays query results
- **Edit Modal** - Edit individual records
- **Technician List Modal** - Select technicians
- **Capacity Modal** - Capacity details
- **Availability Modal** - Technician availability details
- **Auto-Assign Modal** - Review and commit assignments

## 🔧 Technical Details

### Frontend Stack
- **HTML5** - Semantic, accessible markup
- **CSS3** - Modern styling, CSS Grid/Flexbox
- **Vanilla JavaScript** - No frameworks needed
- **Font Awesome** - Professional icons

### Backend Stack
- **Flask** - Lightweight Python web framework
- **SQLite** - Local database
- **pandas** - Data processing

### State Management
```javascript
state = {
    initialized: false,
    autoAssignData: null,
    cityStateMapping: {},
    allCities: [],
    allStates: []
}
```

## 🐛 Troubleshooting

### "Please wait for optimizer to initialize"
**Solution:** Wait for ✅ Ready badge in header

### No data in results
**Solution:** Check system messages for errors. Verify database contains data.

### Dropdown cities not loading
**Solution:** Check console for errors. Ensure initialization completed.

### Server won't start
**Solution:** 
```bash
# Check if port 5000 is in use
netstat -an | findstr :5000

# Use different port
# In app.py, change: app.run(port=5001)
```

## 🔒 Security Notes

### Current Implementation
- **Development Mode** - `debug=True` enabled
- **No Authentication** - Open access
- **No HTTPS** - HTTP only
- **Local Database** - SQLite file-based

### Production Recommendations
1. **Disable Debug Mode**
2. **Add Authentication**
3. **Enable HTTPS**
4. **Add Input Validation**
5. **Rate Limiting**

## 📈 Future Enhancements

Potential additions:
- User Authentication
- Real-time updates (WebSocket)
- Advanced analytics dashboard
- Mobile app support
- Batch operations

## 📞 Support

For issues or questions:
1. Check system messages for errors
2. Check browser console (F12)
3. Check Flask server logs
4. Review this README

## 🎉 You're All Set!

Your web-based Smart Dispatch AI is ready to use!

```bash
python app.py
```

Then open: **http://localhost:5000**

Enjoy your modern, professional dispatch optimization system! 🚀

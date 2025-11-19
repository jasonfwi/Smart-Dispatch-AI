# Smart Dispatch AI

AI-powered dispatch optimization system for managing technician assignments based on availability, location, and capacity constraints.

## Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

The application uses a local SQLite database (`local_dispatch.db`). Ensure the database file exists and contains the required tables:
- `current_dispatches`
- `technicians`
- `technician_calendar`
- `dispatch_history`

### 3. Run the Application

```bash
python app.py
```

Then open your browser to: **http://localhost:5000**

## Features

- **Web-Based Interface** - Modern, responsive web UI
- **Local SQLite Database** - Fast, offline-capable data storage
- **AI-Powered Assignment** - Intelligent technician-dispatch matching
- **Real-Time Queries** - Instant results for all queries
- **Capacity Management** - Track and manage technician capacity
- **Auto-Assignment** - Automated dispatch assignment with manual override

## Project Structure

```
dispatch_optimizer/
├── app.py                  # Flask web application
├── dispatch_local.py       # Core optimizer logic (SQLite)
├── local_db.py             # SQLite database utilities
├── constants.py            # Shared constants and data models
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html         # Web UI template
└── static/
    ├── css/
    │   └── styles.css     # Styles
    └── js/
        └── app.js         # Frontend logic
```

## Documentation

- **WEB_APP_README.md** - Web application user guide
- **DISPATCH_README.md** - Backend API documentation
- **LOCAL_DB_README.md** - Local database setup and usage

## Support

For issues or questions, check the documentation files or review the application logs.

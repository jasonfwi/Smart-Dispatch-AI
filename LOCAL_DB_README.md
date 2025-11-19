# Local Database Mode - Smart Dispatch AI

This document explains how to use the local SQLite database version of Smart Dispatch AI.

## Overview

The application uses a local SQLite database for:
- Fast query performance
- Offline operation
- Easy development and testing
- No external dependencies

## Database Setup

The application requires a local SQLite database file (`local_dispatch.db`) with the following tables:

1. **current_dispatches** - Active dispatch requests
2. **technicians** - Technician profiles and skills
3. **technician_calendar** - Technician availability schedules
4. **dispatch_history** - Historical dispatch assignments

## Running the Application

Simply run:

```bash
python app.py
```

The application will automatically connect to the local SQLite database.

## Database Location

By default, the local database is located at:
```
dispatch_optimizer/local_dispatch.db
```

## Features

The local version supports:
- ✅ Querying dispatches (all queries)
- ✅ Querying technicians
- ✅ Querying technician calendar
- ✅ Capacity management queries
- ✅ Technician location queries
- ✅ Auto-assignment
- ✅ Dispatch creation and management
- ✅ Calendar updates

## Database Schema

The local database contains these tables:

1. **current_dispatches** - Active dispatch requests
2. **technicians** - Technician profiles and skills
3. **technician_calendar** - Technician availability schedules
4. **dispatch_history** - Historical dispatch assignments
5. **import_metadata** - Tracks when data was imported (if applicable)

## Troubleshooting

### Database Not Found
```
Error: Database file not found
```
**Solution**: Ensure `local_dispatch.db` exists in the application directory.

### Database Appears Empty
```
Warning: Local database exists but appears empty!
```
**Solution**: Verify the database contains data. Check table row counts.

### Performance Issues
If queries are slow:
- Check database file size
- Consider adding database indexes
- Verify data was imported correctly

## File Structure

```
dispatch_optimizer/
├── dispatch_local.py         # Local SQLite version
├── local_db.py              # SQLite database wrapper
├── constants.py             # Shared constants and models
├── local_dispatch.db        # SQLite database
└── LOCAL_DB_README.md       # This file
```

## Support

For issues or questions:
- Check logs for detailed error messages
- Verify database file exists and is readable
- Ensure database contains required tables and data

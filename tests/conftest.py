"""
Pytest configuration and fixtures for Smart Dispatch AI tests.
"""

import pytest
import sys
from pathlib import Path
import sqlite3
import shutil
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dispatch import SmartDispatchAI
from populate_db import LocalDatabase
from db_maintenance import DatabaseMaintenance


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create a temporary database path for testing."""
    return tmp_path_factory.mktemp("data") / "test_dispatch.db"


@pytest.fixture(scope="session")
def sample_data():
    """Provide sample test data."""
    return {
        'technicians': [
            {
                'Technician_id': 'T900000',
                'Name': 'Test Technician 1',
                'Primary_skill': 'Fiber ONT installation',
                'City': 'New York',
                'County': 'NEW YORK',
                'State': 'NY',
                'Latitude': 40.7128,
                'Longitude': -74.0060,
                'Workload_capacity': 8,
                'Current_assignments': 2
            },
            {
                'Technician_id': 'T900001',
                'Name': 'Test Technician 2',
                'Primary_skill': 'Network troubleshooting',
                'City': 'New York',
                'County': 'NEW YORK',
                'State': 'NY',
                'Latitude': 40.7580,
                'Longitude': -73.9855,
                'Workload_capacity': 6,
                'Current_assignments': 0
            }
        ],
        'dispatches': [
            {
                'Dispatch_id': '200000000',
                'Ticket_type': 'Install',
                'Order_type': 'New Service',
                'Priority': 'High',
                'Required_skill': 'Fiber ONT installation',
                'Status': 'Pending',
                'Street': '123 Test St',
                'City': 'New York',
                'County': 'NEW YORK',
                'State': 'NY',
                'Postal_code': '10001',
                'Customer_latitude': 40.7489,
                'Customer_longitude': -73.9680,
                'Appointment_start_datetime': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 09:00:00'),
                'Appointment_end_datetime': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 10:00:00'),
                'Duration_min': 60,
                'Assigned_technician_id': None,
                'Optimized_technician_id': None,
                'Resolution_type': None,
                'Optimization_status': 'pending',
                'Optimization_timestamp': None,
                'Optimization_confidence': None
            },
            {
                'Dispatch_id': '200000001',
                'Ticket_type': 'Trouble',
                'Order_type': None,
                'Priority': 'Critical',
                'Required_skill': 'Network troubleshooting',
                'Status': 'In Progress',
                'Street': '456 Test Ave',
                'City': 'New York',
                'County': 'NEW YORK',
                'State': 'NY',
                'Postal_code': '10002',
                'Customer_latitude': 40.7589,
                'Customer_longitude': -73.9851,
                'Appointment_start_datetime': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 10:00:00'),
                'Appointment_end_datetime': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 11:00:00'),
                'Duration_min': 60,
                'Assigned_technician_id': 'T900000',
                'Optimized_technician_id': None,
                'Resolution_type': None,
                'Optimization_status': 'pending',
                'Optimization_timestamp': None,
                'Optimization_confidence': None
            }
        ],
        'calendar': [
            {
                'Technician_id': 'T900000',
                'Date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'Day_of_week': (datetime.now() + timedelta(days=1)).strftime('%A'),
                'Available': 1,
                'Start_time': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 08:00:00'),
                'End_time': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 17:00:00'),
                'Reason': '',
                'Max_assignments': 8
            },
            {
                'Technician_id': 'T900001',
                'Date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'Day_of_week': (datetime.now() + timedelta(days=1)).strftime('%A'),
                'Available': 1,
                'Start_time': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 09:00:00'),
                'End_time': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 18:00:00'),
                'Reason': '',
                'Max_assignments': 6
            }
        ]
    }


@pytest.fixture(scope="function")
def test_database(test_db_path, sample_data):
    """Create a test database with sample data."""
    # Remove existing test database
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Create new database
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE technicians (
            Technician_id TEXT PRIMARY KEY,
            Name TEXT,
            Primary_skill TEXT,
            City TEXT,
            County TEXT,
            State TEXT,
            Latitude REAL,
            Longitude REAL,
            Workload_capacity INTEGER,
            Current_assignments INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE current_dispatches (
            Dispatch_id TEXT PRIMARY KEY,
            Ticket_type TEXT,
            Order_type TEXT,
            Priority TEXT,
            Required_skill TEXT,
            Status TEXT,
            Street TEXT,
            City TEXT,
            County TEXT,
            State TEXT,
            Postal_code TEXT,
            Customer_latitude REAL,
            Customer_longitude REAL,
            Appointment_start_datetime TEXT,
            Appointment_end_datetime TEXT,
            Duration_min INTEGER,
            Assigned_technician_id TEXT,
            Optimized_technician_id TEXT,
            Resolution_type TEXT,
            Optimization_status TEXT,
            Optimization_timestamp TEXT,
            Optimization_confidence REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE technician_calendar (
            Technician_id TEXT,
            Date TEXT,
            Day_of_week TEXT,
            Available INTEGER,
            Start_time TEXT,
            End_time TEXT,
            Reason TEXT,
            Max_assignments INTEGER,
            PRIMARY KEY (Technician_id, Date)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE dispatch_history (
            History_id INTEGER PRIMARY KEY AUTOINCREMENT,
            Dispatch_id TEXT,
            Technician_id TEXT,
            Action TEXT,
            Timestamp TEXT,
            Details TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE change_history (
            change_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            table_name TEXT NOT NULL,
            operation TEXT NOT NULL,
            record_id TEXT NOT NULL,
            old_data TEXT,
            new_data TEXT,
            user_action TEXT,
            can_rollback INTEGER DEFAULT 1
        )
    """)
    
    # Insert sample data
    for tech in sample_data['technicians']:
        cursor.execute("""
            INSERT INTO technicians VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tech['Technician_id'], tech['Name'], tech['Primary_skill'],
            tech['City'], tech['County'], tech['State'],
            tech['Latitude'], tech['Longitude'],
            tech['Workload_capacity'], tech['Current_assignments']
        ))
    
    for dispatch in sample_data['dispatches']:
        cursor.execute("""
            INSERT INTO current_dispatches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dispatch['Dispatch_id'], dispatch['Ticket_type'], dispatch['Order_type'],
            dispatch['Priority'], dispatch['Required_skill'], dispatch['Status'],
            dispatch['Street'], dispatch['City'], dispatch['County'], dispatch['State'],
            dispatch['Postal_code'], dispatch['Customer_latitude'], dispatch['Customer_longitude'],
            dispatch['Appointment_start_datetime'], dispatch['Appointment_end_datetime'],
            dispatch['Duration_min'], dispatch['Assigned_technician_id'],
            dispatch['Optimized_technician_id'], dispatch['Resolution_type'],
            dispatch['Optimization_status'], dispatch['Optimization_timestamp'],
            dispatch['Optimization_confidence']
        ))
    
    for cal in sample_data['calendar']:
        cursor.execute("""
            INSERT INTO technician_calendar VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cal['Technician_id'], cal['Date'], cal['Day_of_week'],
            cal['Available'], cal['Start_time'], cal['End_time'],
            cal['Reason'], cal['Max_assignments']
        ))
    
    conn.commit()
    conn.close()
    
    yield test_db_path
    
    # Cleanup
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture(scope="function")
def optimizer(test_database):
    """Create a SmartDispatchAI instance with test database."""
    return SmartDispatchAI(db_path=str(test_database))


@pytest.fixture(scope="function")
def maintenance(test_database):
    """Create a DatabaseMaintenance instance with test database."""
    return DatabaseMaintenance(db_path=test_database)


@pytest.fixture
def tomorrow_date():
    """Get tomorrow's date as string."""
    return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')


@pytest.fixture
def next_week_monday():
    """Get next Monday's date as string."""
    today = datetime.now()
    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + timedelta(days=days_ahead)
    return next_monday.strftime('%Y-%m-%d')


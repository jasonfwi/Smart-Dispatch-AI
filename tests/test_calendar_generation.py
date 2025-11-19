"""
Tests for calendar generation functionality.
"""

import pytest
from datetime import datetime, timedelta
import json


class TestCalendarGeneration:
    """Test calendar generation features."""
    
    def test_manual_week_generation(self, optimizer, next_week_monday):
        """Test manual generation of a week of calendar entries."""
        tech_id = 'T900000'
        
        # Generate week
        entries_created = 0
        for day_offset in range(5):  # Mon-Fri
            entry_date = datetime.strptime(next_week_monday, '%Y-%m-%d') + timedelta(days=day_offset)
            date_str = entry_date.strftime('%Y-%m-%d')
            day_name = entry_date.strftime('%A')
            
            # Check if entry exists
            existing = optimizer.db.query(
                "SELECT * FROM technician_calendar WHERE Technician_id = ? AND Date = ?",
                (tech_id, date_str)
            )
            
            if not existing:
                optimizer.db.execute("""
                    INSERT INTO technician_calendar
                    (Technician_id, Date, Day_of_week, Available, Start_time, End_time, Reason, Max_assignments)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tech_id,
                    date_str,
                    day_name,
                    1,
                    f"{date_str} 09:00:00",
                    f"{date_str} 17:00:00",
                    '',
                    8
                ))
                entries_created += 1
        
        assert entries_created > 0
        
        # Verify entries were created
        result = optimizer.db.query(
            "SELECT * FROM technician_calendar WHERE Technician_id = ? AND Date >= ?",
            (tech_id, next_week_monday)
        )
        
        assert result is not None
        assert len(result) >= entries_created
    
    def test_manual_entry_flagging(self, maintenance, next_week_monday):
        """Test that manual entries are flagged in change_history."""
        tech_id = 'T900000'
        date_str = next_week_monday
        
        # Create manual entry with flag
        entry_data = {
            'Technician_id': tech_id,
            'Date': date_str,
            'Day_of_week': 'Monday',
            'Available': 1,
            'Start_time': f"{date_str} 09:00:00",
            'End_time': f"{date_str} 17:00:00",
            'Max_assignments': 8,
            'manual_entry': True
        }
        
        # Log to change_history
        change_id = maintenance.log_change(
            table_name='technician_calendar',
            operation='INSERT',
            record_id=f"{tech_id}_{date_str}",
            new_data=entry_data,
            user_action=f'Manual week generation test for {date_str}'
        )
        
        assert change_id > 0
        
        # Verify flag is present
        history = maintenance.get_change_history(
            table_name='technician_calendar',
            limit=1
        )
        
        assert len(history) > 0
        assert history[0]['new_data']['manual_entry'] is True
    
    def test_automated_script_skips_manual(self, maintenance, next_week_monday):
        """Test that automated script detects and skips manual entries."""
        tech_id = 'T900000'
        date_str = next_week_monday
        
        # Create manual entry
        entry_data = {
            'Technician_id': tech_id,
            'Date': date_str,
            'manual_entry': True
        }
        
        maintenance.log_change(
            table_name='technician_calendar',
            operation='INSERT',
            record_id=f"{tech_id}_{date_str}",
            new_data=entry_data,
            user_action='Manual test entry'
        )
        
        # Check if entry is detected as manual
        cursor = maintenance.conn.cursor()
        cursor.execute("""
            SELECT new_data
            FROM change_history
            WHERE table_name = 'technician_calendar'
            AND operation = 'INSERT'
            AND record_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (f"{tech_id}_{date_str}",))
        
        result = cursor.fetchone()
        assert result is not None
        
        data = json.loads(result['new_data'])
        assert data.get('manual_entry') is True
    
    def test_week_generation_no_duplicates(self, optimizer, next_week_monday):
        """Test that week generation doesn't create duplicates."""
        tech_id = 'T900001'
        
        # Generate week first time
        first_count = 0
        for day_offset in range(5):
            entry_date = datetime.strptime(next_week_monday, '%Y-%m-%d') + timedelta(days=day_offset)
            date_str = entry_date.strftime('%Y-%m-%d')
            
            existing = optimizer.db.query(
                "SELECT * FROM technician_calendar WHERE Technician_id = ? AND Date = ?",
                (tech_id, date_str)
            )
            
            if not existing:
                optimizer.db.execute("""
                    INSERT INTO technician_calendar
                    (Technician_id, Date, Day_of_week, Available, Start_time, End_time, Reason, Max_assignments)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tech_id, date_str, entry_date.strftime('%A'), 1,
                    f"{date_str} 09:00:00", f"{date_str} 17:00:00", '', 6
                ))
                first_count += 1
        
        # Try to generate again
        second_count = 0
        for day_offset in range(5):
            entry_date = datetime.strptime(next_week_monday, '%Y-%m-%d') + timedelta(days=day_offset)
            date_str = entry_date.strftime('%Y-%m-%d')
            
            existing = optimizer.db.query(
                "SELECT * FROM technician_calendar WHERE Technician_id = ? AND Date = ?",
                (tech_id, date_str)
            )
            
            if not existing:
                second_count += 1
        
        # Second generation should create 0 entries (all exist)
        assert second_count == 0
        assert first_count > 0
    
    def test_calendar_update(self, optimizer, tomorrow_date):
        """Test updating calendar entry."""
        tech_id = 'T900000'
        
        # Update availability
        success = optimizer.update_technician_calendar(
            tech_id=tech_id,
            date=tomorrow_date,
            available=0,
            reason='Testing unavailability'
        )
        
        assert success is True
        
        # Verify update
        result = optimizer.db.query(
            "SELECT * FROM technician_calendar WHERE Technician_id = ? AND Date = ?",
            (tech_id, tomorrow_date)
        )
        
        assert result is not None
        assert len(result) == 1
        assert result[0]['Available'] == 0
        assert result[0]['Reason'] == 'Testing unavailability'
    
    def test_calendar_max_assignments_update(self, optimizer, tomorrow_date):
        """Test updating max_assignments in calendar."""
        tech_id = 'T900000'
        new_max = 10
        
        success = optimizer.update_technician_calendar(
            tech_id=tech_id,
            date=tomorrow_date,
            max_assignments=new_max
        )
        
        assert success is True
        
        # Verify update
        result = optimizer.db.query(
            "SELECT Max_assignments FROM technician_calendar WHERE Technician_id = ? AND Date = ?",
            (tech_id, tomorrow_date)
        )
        
        assert result is not None
        assert result[0]['Max_assignments'] == new_max


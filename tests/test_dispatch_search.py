"""
Tests for dispatch search functionality.
"""

import pytest
from datetime import datetime, timedelta


class TestDispatchSearch:
    """Test dispatch search and filtering."""
    
    def test_get_unassigned_dispatches(self, optimizer):
        """Test getting unassigned dispatches."""
        result = optimizer.get_unassigned_dispatches(limit=100)
        
        assert result is not None
        assert len(result) > 0
        
        # Verify all returned dispatches are unassigned
        for dispatch in result:
            assigned = dispatch.get('Assigned_technician_id')
            assert assigned is None or assigned == ''
    
    def test_get_unassigned_with_filters(self, optimizer, tomorrow_date):
        """Test unassigned dispatches with date/city/state filters."""
        result = optimizer.get_unassigned_dispatches(
            date=tomorrow_date,
            city='New York',
            state='NY',
            limit=100
        )
        
        assert result is not None
        
        # Verify filters are applied
        for dispatch in result:
            assert dispatch.get('City') == 'New York'
            assert dispatch.get('State') == 'NY'
            assert dispatch.get('Assigned_technician_id') is None or dispatch.get('Assigned_technician_id') == ''
    
    def test_search_by_dispatch_id(self, optimizer):
        """Test searching by specific dispatch ID."""
        result = optimizer.db.query(
            "SELECT * FROM current_dispatches WHERE Dispatch_id = ?",
            ('200000000',)
        )
        
        assert result is not None
        assert len(result) == 1
        assert result[0]['Dispatch_id'] == '200000000'
    
    def test_search_by_status(self, optimizer):
        """Test searching by status."""
        result = optimizer.db.query(
            "SELECT * FROM current_dispatches WHERE Status = ?",
            ('Pending',)
        )
        
        assert result is not None
        for dispatch in result:
            assert dispatch['Status'] == 'Pending'
    
    def test_search_by_priority(self, optimizer):
        """Test searching by priority."""
        result = optimizer.db.query(
            "SELECT * FROM current_dispatches WHERE Priority = ?",
            ('Critical',)
        )
        
        assert result is not None
        for dispatch in result:
            assert dispatch['Priority'] == 'Critical'
    
    def test_search_by_skill(self, optimizer):
        """Test searching by required skill."""
        result = optimizer.db.query(
            "SELECT * FROM current_dispatches WHERE Required_skill = ?",
            ('Network troubleshooting',)
        )
        
        assert result is not None
        for dispatch in result:
            assert dispatch['Required_skill'] == 'Network troubleshooting'
    
    def test_search_assigned_only(self, optimizer):
        """Test searching for assigned dispatches only."""
        result = optimizer.db.query(
            "SELECT * FROM current_dispatches WHERE Assigned_technician_id IS NOT NULL AND Assigned_technician_id != ''"
        )
        
        assert result is not None
        for dispatch in result:
            assert dispatch['Assigned_technician_id'] is not None
            assert dispatch['Assigned_technician_id'] != ''
    
    def test_search_date_range(self, optimizer, tomorrow_date):
        """Test searching by date range."""
        end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        result = optimizer.db.query(
            "SELECT * FROM current_dispatches WHERE DATE(Appointment_start_datetime) BETWEEN ? AND ?",
            (tomorrow_date, end_date)
        )
        
        assert result is not None
        # Verify dates are within range
        for dispatch in result:
            appt_date = dispatch['Appointment_start_datetime'][:10]
            assert tomorrow_date <= appt_date <= end_date
    
    def test_search_combined_filters(self, optimizer, tomorrow_date):
        """Test searching with multiple filters combined."""
        result = optimizer.db.query("""
            SELECT * FROM current_dispatches 
            WHERE State = ? 
            AND Priority = ? 
            AND (Assigned_technician_id IS NULL OR Assigned_technician_id = '')
            AND DATE(Appointment_start_datetime) = ?
        """, ('NY', 'High', tomorrow_date))
        
        assert result is not None
        # Verify all filters are applied
        for dispatch in result:
            assert dispatch['State'] == 'NY'
            assert dispatch['Priority'] == 'High'
            assert dispatch['Assigned_technician_id'] is None or dispatch['Assigned_technician_id'] == ''
    
    def test_get_dispatch_ids(self, optimizer):
        """Test getting list of dispatch IDs."""
        result = optimizer.db.query(
            "SELECT Dispatch_id FROM current_dispatches ORDER BY Dispatch_id DESC LIMIT 1000"
        )
        
        assert result is not None
        assert len(result) > 0
        
        # Verify IDs are strings
        for row in result:
            assert isinstance(row['Dispatch_id'], str)
    
    def test_get_unique_skills(self, optimizer):
        """Test getting unique skills."""
        result = optimizer.db.query("""
            SELECT DISTINCT Required_skill 
            FROM current_dispatches 
            WHERE Required_skill IS NOT NULL AND Required_skill != ''
            ORDER BY Required_skill
        """)
        
        assert result is not None
        assert len(result) > 0
        
        # Verify no duplicates
        skills = [row['Required_skill'] for row in result]
        assert len(skills) == len(set(skills))


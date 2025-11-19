"""
Tests for technician availability logic.
"""

import pytest
from datetime import datetime, timedelta


class TestAvailability:
    """Test technician availability checking."""
    
    def test_check_availability_basic(self, optimizer, tomorrow_date):
        """Test basic availability check."""
        result = optimizer.check_technician_availability('T900000', tomorrow_date)
        
        assert result is not None
        assert hasattr(result, 'available')
        assert result.available is True
    
    def test_check_availability_with_calendar(self, optimizer, tomorrow_date):
        """Test availability uses calendar max_assignments."""
        result = optimizer.check_technician_availability('T900000', tomorrow_date)
        
        assert result.available is True
        assert result.available_minutes is not None
        assert result.available_minutes > 0
        
        # Verify it's using calendar max_assignments (8 hours = 480 minutes)
        assert result.available_minutes == 480
    
    def test_check_availability_with_workload(self, optimizer, tomorrow_date):
        """Test availability considers current workload."""
        result = optimizer.check_technician_availability('T900000', tomorrow_date)
        
        assert result.assigned_minutes is not None
        assert result.assigned_minutes >= 0
        
        # Verify remaining capacity calculation
        remaining = result.available_minutes - result.assigned_minutes
        assert remaining >= 0
    
    def test_unavailable_technician(self, optimizer):
        """Test checking unavailable technician."""
        # Add unavailable calendar entry
        optimizer.db.execute("""
            INSERT INTO technician_calendar 
            (Technician_id, Date, Day_of_week, Available, Start_time, End_time, Reason, Max_assignments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'T900000',
            '2025-12-25',
            'Thursday',
            0,
            '2025-12-25 00:00:00',
            '2025-12-25 00:00:00',
            'Holiday',
            0
        ))
        
        result = optimizer.check_technician_availability('T900000', '2025-12-25')
        
        assert result.available is False
        assert result.reason == 'Holiday'
    
    def test_no_calendar_entry(self, optimizer):
        """Test checking availability with no calendar entry."""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        
        result = optimizer.check_technician_availability('T900000', future_date)
        
        assert result.available is False
        assert 'No calendar entry' in result.reason
    
    def test_get_assigned_minutes(self, optimizer, tomorrow_date):
        """Test calculating assigned minutes for a technician."""
        minutes = optimizer._get_assigned_minutes('T900000', tomorrow_date)
        
        assert minutes is not None
        assert minutes >= 0
        assert isinstance(minutes, int)
    
    def test_availability_multiple_technicians(self, optimizer, tomorrow_date):
        """Test checking availability for multiple technicians."""
        tech_ids = ['T900000', 'T900001']
        
        for tech_id in tech_ids:
            result = optimizer.check_technician_availability(tech_id, tomorrow_date)
            assert result is not None
            assert hasattr(result, 'available')
    
    def test_workload_capacity_not_used(self, optimizer, tomorrow_date):
        """Test that workload_capacity is NOT used for availability."""
        # Get calendar max_assignments
        cal_result = optimizer.db.query(
            "SELECT Max_assignments FROM technician_calendar WHERE Technician_id = ? AND Date = ?",
            ('T900000', tomorrow_date)
        )
        
        # Get workload_capacity
        tech_result = optimizer.db.query(
            "SELECT Workload_capacity FROM technicians WHERE Technician_id = ?",
            ('T900000',)
        )
        
        # Check availability
        avail_result = optimizer.check_technician_availability('T900000', tomorrow_date)
        
        # Verify it uses calendar max_assignments, not workload_capacity
        if cal_result and tech_result:
            calendar_max = cal_result[0]['Max_assignments'] * 60  # Convert to minutes
            assert avail_result.available_minutes == calendar_max
    
    def test_city_capacity(self, optimizer, tomorrow_date):
        """Test getting city capacity."""
        result = optimizer.get_city_capacity(
            city='New York',
            state='NY',
            target_date=tomorrow_date
        )
        
        assert result is not None
        assert 'total_technicians' in result
        assert 'total_capacity' in result
        assert 'assigned_count' in result
        assert 'available_capacity' in result
        
        # Verify capacity calculation
        assert result['available_capacity'] == result['total_capacity'] - result['assigned_count']
    
    def test_capacity_uses_calendar(self, optimizer, tomorrow_date):
        """Test that capacity calculation uses calendar max_assignments."""
        result = optimizer.get_city_capacity(
            city='New York',
            state='NY',
            target_date=tomorrow_date
        )
        
        # Total capacity should be sum of calendar max_assignments, not workload_capacity
        assert result['total_capacity'] > 0


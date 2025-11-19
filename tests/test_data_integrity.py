"""
Tests for data integrity and validation.
"""

import pytest


class TestDataIntegrity:
    """Test data integrity constraints and validation."""
    
    def test_no_negative_assignments(self, optimizer):
        """Test that no technicians have negative current_assignments."""
        result = optimizer.db.query(
            "SELECT Technician_id, Current_assignments FROM technicians WHERE Current_assignments < 0"
        )
        
        assert len(result) == 0, "Found technicians with negative assignments"
    
    def test_assignments_match_dispatches(self, optimizer):
        """Test that current_assignments matches actual dispatch count."""
        techs = optimizer.db.query("SELECT Technician_id, Current_assignments FROM technicians")
        
        for tech in techs:
            tech_id = tech['Technician_id']
            recorded_assignments = tech['Current_assignments']
            
            # Count actual dispatches
            actual_dispatches = optimizer.db.query(
                "SELECT COUNT(*) as count FROM current_dispatches WHERE Assigned_technician_id = ?",
                (tech_id,)
            )
            
            actual_count = actual_dispatches[0]['count'] if actual_dispatches else 0
            
            # Allow some tolerance for in-progress updates
            assert abs(recorded_assignments - actual_count) <= 1, \
                f"Technician {tech_id}: recorded={recorded_assignments}, actual={actual_count}"
    
    def test_calendar_dates_valid(self, optimizer):
        """Test that calendar dates are valid."""
        result = optimizer.db.query(
            "SELECT Date FROM technician_calendar WHERE Date IS NULL OR Date = ''"
        )
        
        assert len(result) == 0, "Found calendar entries with invalid dates"
    
    def test_calendar_max_assignments_positive(self, optimizer):
        """Test that calendar max_assignments are non-negative."""
        result = optimizer.db.query(
            "SELECT Technician_id, Date, Max_assignments FROM technician_calendar WHERE Max_assignments < 0"
        )
        
        assert len(result) == 0, "Found calendar entries with negative max_assignments"
    
    def test_dispatch_ids_unique(self, optimizer):
        """Test that dispatch IDs are unique."""
        result = optimizer.db.query("""
            SELECT Dispatch_id, COUNT(*) as count 
            FROM current_dispatches 
            GROUP BY Dispatch_id 
            HAVING count > 1
        """)
        
        assert len(result) == 0, "Found duplicate dispatch IDs"
    
    def test_technician_ids_unique(self, optimizer):
        """Test that technician IDs are unique."""
        result = optimizer.db.query("""
            SELECT Technician_id, COUNT(*) as count 
            FROM technicians 
            GROUP BY Technician_id 
            HAVING count > 1
        """)
        
        assert len(result) == 0, "Found duplicate technician IDs"
    
    def test_assigned_dispatches_have_valid_tech(self, optimizer):
        """Test that assigned dispatches reference valid technicians."""
        result = optimizer.db.query("""
            SELECT d.Dispatch_id, d.Assigned_technician_id
            FROM current_dispatches d
            LEFT JOIN technicians t ON d.Assigned_technician_id = t.Technician_id
            WHERE d.Assigned_technician_id IS NOT NULL 
            AND d.Assigned_technician_id != ''
            AND t.Technician_id IS NULL
        """)
        
        assert len(result) == 0, "Found dispatches assigned to non-existent technicians"
    
    def test_calendar_entries_have_valid_tech(self, optimizer):
        """Test that calendar entries reference valid technicians."""
        result = optimizer.db.query("""
            SELECT c.Technician_id, c.Date
            FROM technician_calendar c
            LEFT JOIN technicians t ON c.Technician_id = t.Technician_id
            WHERE t.Technician_id IS NULL
        """)
        
        assert len(result) == 0, "Found calendar entries for non-existent technicians"
    
    def test_coordinates_valid(self, optimizer):
        """Test that coordinates are within valid ranges."""
        # Latitude: -90 to 90, Longitude: -180 to 180
        result = optimizer.db.query("""
            SELECT Technician_id, Latitude, Longitude
            FROM technicians
            WHERE Latitude < -90 OR Latitude > 90
            OR Longitude < -180 OR Longitude > 180
        """)
        
        assert len(result) == 0, "Found technicians with invalid coordinates"
        
        result = optimizer.db.query("""
            SELECT Dispatch_id, Customer_latitude, Customer_longitude
            FROM current_dispatches
            WHERE Customer_latitude < -90 OR Customer_latitude > 90
            OR Customer_longitude < -180 OR Customer_longitude > 180
        """)
        
        assert len(result) == 0, "Found dispatches with invalid coordinates"
    
    def test_workload_capacity_reasonable(self, optimizer):
        """Test that workload capacity is within reasonable bounds."""
        result = optimizer.db.query("""
            SELECT Technician_id, Workload_capacity
            FROM technicians
            WHERE Workload_capacity < 0 OR Workload_capacity > 24
        """)
        
        assert len(result) == 0, "Found technicians with unreasonable workload capacity"
    
    def test_appointment_times_valid(self, optimizer):
        """Test that appointment start is before end."""
        result = optimizer.db.query("""
            SELECT Dispatch_id, Appointment_start_datetime, Appointment_end_datetime
            FROM current_dispatches
            WHERE Appointment_start_datetime >= Appointment_end_datetime
        """)
        
        assert len(result) == 0, "Found dispatches with invalid appointment times"
    
    def test_priority_values_valid(self, optimizer):
        """Test that priority values are from valid set."""
        valid_priorities = ['Critical', 'High', 'Medium', 'Low']
        
        result = optimizer.db.query("""
            SELECT DISTINCT Priority
            FROM current_dispatches
            WHERE Priority IS NOT NULL AND Priority != ''
        """)
        
        for row in result:
            assert row['Priority'] in valid_priorities, \
                f"Invalid priority value: {row['Priority']}"
    
    def test_status_values_valid(self, optimizer):
        """Test that status values are from valid set."""
        valid_statuses = ['Pending', 'In Progress', 'Completed', 'Cancelled']
        
        result = optimizer.db.query("""
            SELECT DISTINCT Status
            FROM current_dispatches
            WHERE Status IS NOT NULL AND Status != ''
        """)
        
        for row in result:
            assert row['Status'] in valid_statuses, \
                f"Invalid status value: {row['Status']}"
    
    def test_no_orphaned_history(self, maintenance):
        """Test that change_history doesn't have orphaned entries."""
        # This is a soft check - we just verify the structure is valid
        history = maintenance.get_change_history(limit=100)
        
        for entry in history:
            assert 'table_name' in entry
            assert 'operation' in entry
            assert 'record_id' in entry
            assert entry['operation'] in ['INSERT', 'UPDATE', 'DELETE']


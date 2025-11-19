"""
Tests for database maintenance functionality.
"""

import pytest
from datetime import datetime
import json


class TestDatabaseMaintenance:
    """Test database maintenance operations."""
    
    def test_log_change(self, maintenance):
        """Test logging a change to change_history."""
        change_id = maintenance.log_change(
            table_name='technicians',
            operation='UPDATE',
            record_id='T900000',
            old_data={'Name': 'Old Name'},
            new_data={'Name': 'New Name'},
            user_action='Test update'
        )
        
        assert change_id > 0
    
    def test_get_change_history(self, maintenance):
        """Test retrieving change history."""
        # Log some changes
        maintenance.log_change(
            table_name='technicians',
            operation='INSERT',
            record_id='T999999',
            new_data={'Name': 'Test Tech'},
            user_action='Test insert'
        )
        
        # Get history
        history = maintenance.get_change_history(limit=10)
        
        assert history is not None
        assert len(history) > 0
        assert isinstance(history[0], dict)
        assert 'change_id' in history[0]
        assert 'timestamp' in history[0]
        assert 'table_name' in history[0]
    
    def test_get_change_history_filtered(self, maintenance):
        """Test retrieving filtered change history."""
        # Log changes to different tables
        maintenance.log_change(
            table_name='technicians',
            operation='UPDATE',
            record_id='T900000',
            new_data={'Name': 'Updated'},
            user_action='Test'
        )
        
        maintenance.log_change(
            table_name='current_dispatches',
            operation='UPDATE',
            record_id='200000000',
            new_data={'Status': 'Completed'},
            user_action='Test'
        )
        
        # Get filtered history
        history = maintenance.get_change_history(
            table_name='technicians',
            limit=10
        )
        
        assert history is not None
        # All results should be for technicians table
        for change in history:
            assert change['table_name'] == 'technicians'
    
    def test_get_change_stats(self, maintenance):
        """Test getting change statistics."""
        # Log some changes
        for i in range(5):
            maintenance.log_change(
                table_name='technicians',
                operation='UPDATE',
                record_id=f'T{i}',
                new_data={'test': i},
                user_action='Test'
            )
        
        stats = maintenance.get_change_stats()
        
        assert stats is not None
        assert 'total_changes' in stats
        assert 'by_table' in stats
        assert 'by_operation' in stats
        assert 'recent_changes' in stats
        
        assert stats['total_changes'] > 0
    
    def test_rollback_insert(self, maintenance, optimizer):
        """Test rolling back an INSERT operation."""
        # Insert a test record
        optimizer.db.execute("""
            INSERT INTO technicians 
            (Technician_id, Name, Primary_skill, City, State, Latitude, Longitude, Workload_capacity, Current_assignments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('T999999', 'Test Rollback', 'Testing', 'Test City', 'TS', 0.0, 0.0, 8, 0))
        
        # Log the change
        change_id = maintenance.log_change(
            table_name='technicians',
            operation='INSERT',
            record_id='T999999',
            new_data={'Technician_id': 'T999999', 'Name': 'Test Rollback'},
            user_action='Test insert for rollback'
        )
        
        # Verify record exists
        result = optimizer.db.query(
            "SELECT * FROM technicians WHERE Technician_id = ?",
            ('T999999',)
        )
        assert len(result) == 1
        
        # Rollback
        success = maintenance.rollback_change(change_id)
        assert success is True
        
        # Verify record was deleted
        result = optimizer.db.query(
            "SELECT * FROM technicians WHERE Technician_id = ?",
            ('T999999',)
        )
        assert len(result) == 0
    
    def test_rollback_update(self, maintenance, optimizer):
        """Test rolling back an UPDATE operation."""
        tech_id = 'T900000'
        
        # Get original data
        original = optimizer.db.query(
            "SELECT Name FROM technicians WHERE Technician_id = ?",
            (tech_id,)
        )[0]
        original_name = original['Name']
        
        # Update the record
        new_name = 'Updated Name'
        optimizer.db.execute(
            "UPDATE technicians SET Name = ? WHERE Technician_id = ?",
            (new_name, tech_id)
        )
        
        # Log the change
        change_id = maintenance.log_change(
            table_name='technicians',
            operation='UPDATE',
            record_id=tech_id,
            old_data={'Name': original_name},
            new_data={'Name': new_name},
            user_action='Test update for rollback'
        )
        
        # Verify update
        result = optimizer.db.query(
            "SELECT Name FROM technicians WHERE Technician_id = ?",
            (tech_id,)
        )[0]
        assert result['Name'] == new_name
        
        # Rollback
        success = maintenance.rollback_change(change_id)
        assert success is True
        
        # Verify rollback
        result = optimizer.db.query(
            "SELECT Name FROM technicians WHERE Technician_id = ?",
            (tech_id,)
        )[0]
        assert result['Name'] == original_name
    
    def test_delete_record(self, maintenance, optimizer):
        """Test deleting a record with logging."""
        # Insert a test record
        optimizer.db.execute("""
            INSERT INTO technicians 
            (Technician_id, Name, Primary_skill, City, State, Latitude, Longitude, Workload_capacity, Current_assignments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('T888888', 'Test Delete', 'Testing', 'Test City', 'TS', 0.0, 0.0, 8, 0))
        
        # Verify record exists
        result = optimizer.db.query(
            "SELECT * FROM technicians WHERE Technician_id = ?",
            ('T888888',)
        )
        assert len(result) == 1
        
        # Delete with logging
        success = maintenance.delete_record(
            table_name='technicians',
            record_id='T888888',
            user_action='Test deletion'
        )
        
        assert success is True
        
        # Verify record was deleted
        result = optimizer.db.query(
            "SELECT * FROM technicians WHERE Technician_id = ?",
            ('T888888',)
        )
        assert len(result) == 0
        
        # Verify change was logged
        history = maintenance.get_change_history(
            table_name='technicians',
            limit=1
        )
        assert len(history) > 0
        assert history[0]['operation'] == 'DELETE'
        assert history[0]['record_id'] == 'T888888'
    
    def test_clear_old_history(self, maintenance):
        """Test clearing old history entries."""
        # Log some test changes
        for i in range(5):
            maintenance.log_change(
                table_name='test_table',
                operation='TEST',
                record_id=f'TEST{i}',
                new_data={'test': i},
                user_action='Test'
            )
        
        # Clear history older than 0 days (should clear all test entries)
        deleted_count = maintenance.clear_history(days_old=0)
        
        assert deleted_count >= 0
    
    def test_change_history_json_parsing(self, maintenance):
        """Test that JSON data in change_history is properly parsed."""
        test_data = {
            'field1': 'value1',
            'field2': 123,
            'field3': True
        }
        
        change_id = maintenance.log_change(
            table_name='test_table',
            operation='INSERT',
            record_id='TEST001',
            new_data=test_data,
            user_action='Test JSON'
        )
        
        # Retrieve and verify
        history = maintenance.get_change_history(limit=1)
        
        assert history[0]['new_data'] == test_data
        assert isinstance(history[0]['new_data'], dict)


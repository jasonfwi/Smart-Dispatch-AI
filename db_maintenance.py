"""
Database Maintenance Module - Change tracking and rollback for Smart Dispatch AI

This module provides database maintenance functionality including:
- Change history tracking and audit trails
- Rollback functionality for database operations
- Record deletion with logging
- Database statistics and monitoring

Note: This module ONLY modifies the database, never the CSV files.
CSV files remain the source of truth for data imports.
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent / "dispatch.db"


class DatabaseMaintenance:
    """
    Database Maintenance - Change tracking and rollback operations.
    
    This class provides maintenance operations for the Smart Dispatch AI database,
    including change tracking, rollback, and audit trail functionality.
    
    IMPORTANT: This class ONLY modifies the database. CSV files are never touched.
    """
    
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        """
        Initialize database maintenance.
        
        Args:
            db_path: Path to SQLite database file (default: dispatch.db)
        """
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        
        # Connect to database
        self._connect()
        
        # Ensure change_history table exists
        self._ensure_history_table()
        
        logger.info(f"Database maintenance initialized: {self.db_path}")
    
    def _connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.debug(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _ensure_history_table(self):
        """Ensure the change_history table exists."""
        cursor = self.conn.cursor()
        
        # Change history table for audit trail and rollback
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS change_history (
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
        
        # Create indexes for faster history queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_change_history_timestamp 
            ON change_history(timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_change_history_table 
            ON change_history(table_name, timestamp DESC)
        """)
        
        self.conn.commit()
        logger.debug("Change history table verified")
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")
    
    def log_change(self, table_name: str, operation: str, record_id: str, 
                   old_data: Optional[Dict] = None, new_data: Optional[Dict] = None,
                   user_action: str = None) -> int:
        """
        Log a database change to the change_history table.
        
        Args:
            table_name: Name of the table being modified
            operation: Type of operation (INSERT, UPDATE, DELETE)
            record_id: Primary key of the affected record
            old_data: Previous data (for UPDATE/DELETE)
            new_data: New data (for INSERT/UPDATE)
            user_action: Description of the user action
            
        Returns:
            change_id: ID of the logged change
        """
        cursor = self.conn.cursor()
        
        timestamp = datetime.now().isoformat()
        old_json = json.dumps(old_data) if old_data else None
        new_json = json.dumps(new_data) if new_data else None
        
        cursor.execute("""
            INSERT INTO change_history 
            (timestamp, table_name, operation, record_id, old_data, new_data, user_action, can_rollback)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (timestamp, table_name, operation, record_id, old_json, new_json, user_action))
        
        self.conn.commit()
        change_id = cursor.lastrowid
        logger.info(f"Logged {operation} on {table_name}.{record_id} (change_id: {change_id})")
        return change_id
    
    def get_change_history(self, table_name: Optional[str] = None, 
                          limit: int = 100, offset: int = 0,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve change history with optional filters.
        
        Args:
            table_name: Filter by table name (optional)
            limit: Maximum number of records to return
            offset: Number of records to skip
            start_date: Filter changes after this date (ISO format)
            end_date: Filter changes before this date (ISO format)
            
        Returns:
            List of change records
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM change_history WHERE 1=1"
        params = []
        
        if table_name:
            query += " AND table_name = ?"
            params.append(table_name)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        
        results = []
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            # Parse JSON data
            if record.get('old_data'):
                record['old_data'] = json.loads(record['old_data'])
            if record.get('new_data'):
                record['new_data'] = json.loads(record['new_data'])
            results.append(record)
        
        logger.debug(f"Retrieved {len(results)} change history records")
        return results
    
    def get_change_stats(self) -> Dict[str, Any]:
        """Get statistics about database changes."""
        cursor = self.conn.cursor()
        
        # Total changes
        cursor.execute("SELECT COUNT(*) FROM change_history")
        total_changes = cursor.fetchone()[0]
        
        # Changes by table
        cursor.execute("""
            SELECT table_name, COUNT(*) as count 
            FROM change_history 
            GROUP BY table_name 
            ORDER BY count DESC
        """)
        by_table = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Changes by operation
        cursor.execute("""
            SELECT operation, COUNT(*) as count 
            FROM change_history 
            GROUP BY operation
        """)
        by_operation = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Recent changes (last 24 hours)
        yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM change_history 
            WHERE timestamp >= ?
        """, (yesterday,))
        recent_changes = cursor.fetchone()[0]
        
        stats = {
            'total_changes': total_changes,
            'by_table': by_table,
            'by_operation': by_operation,
            'recent_changes': recent_changes
        }
        
        logger.debug(f"Retrieved change statistics: {total_changes} total changes")
        return stats
    
    def rollback_change(self, change_id: int) -> bool:
        """
        Rollback a specific change.
        
        IMPORTANT: This ONLY modifies the database. CSV files are never touched.
        
        Args:
            change_id: ID of the change to rollback
            
        Returns:
            True if successful, False otherwise
        """
        cursor = self.conn.cursor()
        
        # Get the change record
        cursor.execute("""
            SELECT table_name, operation, record_id, old_data, new_data, can_rollback
            FROM change_history WHERE change_id = ?
        """, (change_id,))
        
        row = cursor.fetchone()
        if not row:
            logger.error(f"Change {change_id} not found")
            return False
        
        table_name, operation, record_id, old_data_json, new_data_json, can_rollback = row
        
        if not can_rollback:
            logger.error(f"Change {change_id} cannot be rolled back")
            return False
        
        try:
            if operation == 'INSERT':
                # Rollback INSERT by deleting the record
                cursor.execute(f"DELETE FROM {table_name} WHERE {self._get_primary_key(table_name)} = ?", 
                             (record_id,))
                logger.info(f"Rolled back INSERT: Deleted {record_id} from {table_name}")
                
            elif operation == 'UPDATE':
                # Rollback UPDATE by restoring old data
                if old_data_json:
                    old_data = json.loads(old_data_json)
                    set_clause = ', '.join([f"{k} = ?" for k in old_data.keys()])
                    values = list(old_data.values()) + [record_id]
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET {set_clause}
                        WHERE {self._get_primary_key(table_name)} = ?
                    """, values)
                    logger.info(f"Rolled back UPDATE: Restored {record_id} in {table_name}")
                
            elif operation == 'DELETE':
                # Rollback DELETE by re-inserting the record
                if old_data_json:
                    old_data = json.loads(old_data_json)
                    columns = ', '.join(old_data.keys())
                    placeholders = ', '.join(['?' for _ in old_data])
                    cursor.execute(f"""
                        INSERT INTO {table_name} ({columns})
                        VALUES ({placeholders})
                    """, list(old_data.values()))
                    logger.info(f"Rolled back DELETE: Re-inserted {record_id} into {table_name}")
            
            # Mark this change as rolled back
            cursor.execute("""
                UPDATE change_history 
                SET can_rollback = 0, user_action = COALESCE(user_action, '') || ' [ROLLED BACK]'
                WHERE change_id = ?
            """, (change_id,))
            
            # Log the rollback as a new change
            self.log_change(
                table_name=table_name,
                operation=f'ROLLBACK_{operation}',
                record_id=record_id,
                old_data=json.loads(new_data_json) if new_data_json else None,
                new_data=json.loads(old_data_json) if old_data_json else None,
                user_action=f'Rollback of change {change_id}'
            )
            
            self.conn.commit()
            logger.info(f"Successfully rolled back change {change_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback change {change_id}: {e}")
            self.conn.rollback()
            return False
    
    def _get_primary_key(self, table_name: str) -> str:
        """Get the primary key column name for a table."""
        primary_keys = {
            'current_dispatches': 'Dispatch_id',
            'technicians': 'Technician_id',
            'technician_calendar': 'Technician_id',  # Composite key, using first
            'dispatch_history': 'History_id'
        }
        return primary_keys.get(table_name, 'id')
    
    def delete_record(self, table_name: str, record_id: str, user_action: str = None) -> bool:
        """
        Delete a record and log the change.
        
        IMPORTANT: This ONLY modifies the database. CSV files are never touched.
        
        Args:
            table_name: Name of the table
            record_id: Primary key of the record to delete
            user_action: Description of why the record is being deleted
            
        Returns:
            True if successful, False otherwise
        """
        cursor = self.conn.cursor()
        
        try:
            # Get current data before deletion
            pk_column = self._get_primary_key(table_name)
            cursor.execute(f"SELECT * FROM {table_name} WHERE {pk_column} = ?", (record_id,))
            row = cursor.fetchone()
            
            if not row:
                logger.error(f"Record {record_id} not found in {table_name}")
                return False
            
            # Convert row to dict
            columns = [desc[0] for desc in cursor.description]
            old_data = dict(zip(columns, row))
            
            # Delete the record
            cursor.execute(f"DELETE FROM {table_name} WHERE {pk_column} = ?", (record_id,))
            
            # Log the change
            self.log_change(
                table_name=table_name,
                operation='DELETE',
                record_id=record_id,
                old_data=old_data,
                user_action=user_action or f'User deleted record {record_id}'
            )
            
            self.conn.commit()
            logger.info(f"Deleted record {record_id} from {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete record {record_id} from {table_name}: {e}")
            self.conn.rollback()
            return False
    
    def clear_history(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear change history (useful for maintenance).
        
        Args:
            older_than_days: Only clear history older than this many days (optional)
            
        Returns:
            Number of records deleted
        """
        cursor = self.conn.cursor()
        
        if older_than_days:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - older_than_days).isoformat()
            cursor.execute("DELETE FROM change_history WHERE timestamp < ?", (cutoff_date,))
        else:
            cursor.execute("DELETE FROM change_history")
        
        deleted_count = cursor.rowcount
        self.conn.commit()
        
        logger.info(f"Cleared {deleted_count} change history records")
        return deleted_count


def main():
    """
    Command-line interface for database maintenance.
    
    Usage:
        python db_maintenance.py stats              # Show change statistics
        python db_maintenance.py history [limit]    # Show change history
        python db_maintenance.py clear [days]       # Clear old history
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python db_maintenance.py stats              # Show change statistics")
        print("  python db_maintenance.py history [limit]    # Show change history")
        print("  python db_maintenance.py clear [days]       # Clear old history")
        return 1
    
    command = sys.argv[1].lower()
    
    # Initialize maintenance
    maintenance = DatabaseMaintenance()
    
    try:
        if command == 'stats':
            print("=" * 80)
            print("Database Change Statistics")
            print("=" * 80)
            print()
            
            stats = maintenance.get_change_stats()
            
            print(f"Total Changes: {stats['total_changes']:,}")
            print(f"Recent Changes (24h): {stats['recent_changes']:,}")
            print()
            
            if stats['by_operation']:
                print("Changes by Operation:")
                for op, count in stats['by_operation'].items():
                    print(f"  {op}: {count:,}")
                print()
            
            if stats['by_table']:
                print("Changes by Table:")
                for table, count in stats['by_table'].items():
                    print(f"  {table}: {count:,}")
                print()
        
        elif command == 'history':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            
            print("=" * 80)
            print(f"Change History (Last {limit} changes)")
            print("=" * 80)
            print()
            
            history = maintenance.get_change_history(limit=limit)
            
            if not history:
                print("No change history found.")
            else:
                for change in history:
                    print(f"[{change['change_id']}] {change['timestamp']}")
                    print(f"  {change['operation']} on {change['table_name']}.{change['record_id']}")
                    if change['user_action']:
                        print(f"  Action: {change['user_action']}")
                    print(f"  Can Rollback: {'Yes' if change['can_rollback'] else 'No'}")
                    print()
        
        elif command == 'clear':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else None
            
            if days:
                confirm = input(f"Clear history older than {days} days? (yes/no): ")
            else:
                confirm = input("Clear ALL history? This cannot be undone! (yes/no): ")
            
            if confirm.lower() == 'yes':
                deleted = maintenance.clear_history(older_than_days=days)
                print(f"✅ Cleared {deleted:,} change history records")
            else:
                print("❌ Cancelled")
        
        else:
            print(f"Unknown command: {command}")
            return 1
    
    finally:
        maintenance.close()
    
    return 0


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    exit(main())


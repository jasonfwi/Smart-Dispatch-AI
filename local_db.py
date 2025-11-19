"""
Local Database Module - SQLite-based local storage for Smart Dispatch AI

This module provides local database functionality using SQLite for
dispatch optimization and technician management.
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import json
import pandas as pd

logger = logging.getLogger(__name__)

# Default local database path
DEFAULT_DB_PATH = Path(__file__).parent / "local_dispatch.db"


class TransactionContext:
    """Context manager for database transactions."""
    
    def __init__(self, db: 'LocalDatabase'):
        self.db = db
        self._in_transaction = False
    
    def __enter__(self):
        self.db.begin_transaction()
        self._in_transaction = True
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._in_transaction:
            if exc_type is None:
                # No exception - commit transaction
                try:
                    self.db.commit_transaction()
                    logger.debug("Transaction committed successfully")
                except Exception as e:
                    logger.error(f"Failed to commit transaction: {e}")
                    self.db.rollback_transaction()
                    raise
            else:
                # Exception occurred - rollback transaction
                logger.warning(f"Transaction rolled back due to exception: {exc_type.__name__}")
                self.db.rollback_transaction()
            self._in_transaction = False
        return False  # Don't suppress exceptions


class LocalDatabase:
    """SQLite-based local database for dispatch data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize local database connection.
        
        Args:
            db_path: Path to SQLite database file (default: local_dispatch.db)
        """
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection."""
        try:
            # Check if database file exists
            if not self.db_path.exists():
                logger.warning(f"Database file does not exist: {self.db_path}")
                logger.info("Creating new database file. Run 'python import_to_local.py' to populate with data.")
            
            # Use check_same_thread=False to allow connection sharing across threads
            # This is safe for read-heavy workloads with SQLite's default isolation level
            self.conn = sqlite3.connect(
                str(self.db_path), 
                timeout=10.0,
                check_same_thread=False
            )
            self.conn.row_factory = sqlite3.Row  # Enable dict-like row access
            # Enable WAL mode for better concurrency
            self.conn.execute("PRAGMA journal_mode=WAL")
            logger.info(f"Connected to local database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to local database: {e}")
            raise
    
    def _create_tables(self):
        """Create tables if they don't exist (basic structure - will be extended by import)."""
        cursor = self.conn.cursor()
        
        # Current Dispatches table (basic structure - columns will be added dynamically)
        # We create a minimal table here, and import_from_spark_df will add missing columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS current_dispatches (
                Dispatch_id TEXT PRIMARY KEY
            )
        """)
        
        # Technicians table (basic structure - columns will be added dynamically)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS technicians (
                Technician_id TEXT PRIMARY KEY
            )
        """)
        
        # Technician Calendar table (basic structure - columns will be added dynamically)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS technician_calendar (
                Technician_id TEXT,
                Date TEXT,
                PRIMARY KEY (Technician_id, Date)
            )
        """)
        
        # Dispatch History table (basic structure - columns will be added dynamically)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dispatch_history (
                History_id TEXT PRIMARY KEY
            )
        """)
        
        # Metadata table to track import status
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_metadata (
                table_name TEXT PRIMARY KEY,
                last_imported TEXT,
                row_count INTEGER,
                import_timestamp TEXT
            )
        """)
        
        self.conn.commit()
        logger.info("Local database tables created/verified")
    
    def _create_table_from_dataframe(self, table_name: str, pandas_df: pd.DataFrame):
        """
        Create or alter table to match DataFrame schema.
        
        Args:
            table_name: Name of the table
            pandas_df: Pandas DataFrame with the schema
        """
        cursor = self.conn.cursor()
        
        # Get existing columns if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Get existing columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}
        else:
            existing_columns = set()
        
        # Get DataFrame columns
        df_columns = set(pandas_df.columns)
        
        # Find missing columns
        missing_columns = df_columns - existing_columns
        
        if missing_columns:
            logger.info(f"Adding {len(missing_columns)} missing columns to {table_name}")
            logger.debug(f"Missing columns: {sorted(missing_columns)}")
            
            for col in sorted(missing_columns):
                # Determine SQLite type from pandas dtype
                dtype = pandas_df[col].dtype
                if pd.api.types.is_integer_dtype(dtype):
                    sql_type = "INTEGER"
                elif pd.api.types.is_float_dtype(dtype):
                    sql_type = "REAL"
                elif pd.api.types.is_datetime64_any_dtype(dtype):
                    sql_type = "TEXT"
                elif pd.api.types.is_bool_dtype(dtype):
                    sql_type = "INTEGER"  # SQLite doesn't have boolean, use INTEGER (0/1)
                else:
                    sql_type = "TEXT"
                
                try:
                    # Escape column name if it contains special characters
                    safe_col_name = f'"{col}"' if any(c in col for c in [' ', '-', '.']) else col
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {safe_col_name} {sql_type}")
                    logger.info(f"  ✓ Added column {col} ({sql_type})")
                except sqlite3.OperationalError as e:
                    error_msg = str(e).lower()
                    # Column might already exist (race condition or case sensitivity)
                    if "duplicate column" in error_msg or "already exists" in error_msg:
                        logger.debug(f"  Column {col} already exists, skipping")
                    else:
                        logger.warning(f"  Could not add column {col}: {e}")
                        # Try with quoted name if it failed
                        try:
                            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN "{col}" {sql_type}')
                            logger.info(f"  ✓ Added column {col} ({sql_type}) with quotes")
                        except:
                            logger.error(f"  ✗ Failed to add column {col} even with quotes")
        
        self.conn.commit()
    
    def import_from_spark_df(self, table_name: str, df, spark_session):
        """
        Import data from Spark DataFrame to local SQLite table.
        
        Args:
            table_name: Name of the local table
            df: Spark DataFrame
            spark_session: Spark session for data conversion
        """
        logger.info(f"Importing {table_name} from Spark DataFrame...")
        
        try:
            # Convert Spark DataFrame to Pandas for easier SQLite insertion
            pandas_df = df.toPandas()
            
            cursor = self.conn.cursor()
            
            # Check if table exists, if not create it with basic structure
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create table dynamically from DataFrame schema
                logger.info(f"Creating table {table_name} from DataFrame schema...")
                pandas_df.head(0).to_sql(table_name, self.conn, if_exists='fail', index=False)
            else:
                # Ensure table has all columns from DataFrame
                self._create_table_from_dataframe(table_name, pandas_df)
            
            # Clear existing data
            cursor.execute(f"DELETE FROM {table_name}")
            
            # Insert data
            pandas_df.to_sql(table_name, self.conn, if_exists='append', index=False)
            
            row_count = len(pandas_df)
            
            # Update metadata
            cursor.execute("""
                INSERT OR REPLACE INTO import_metadata 
                (table_name, last_imported, row_count, import_timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                table_name,
                datetime.now().isoformat(),
                row_count,
                datetime.now().isoformat()
            ))
            
            self.conn.commit()
            logger.info(f"✓ Imported {row_count} rows into {table_name}")
            return row_count
            
        except Exception as e:
            logger.error(f"Failed to import {table_name}: {e}")
            self.conn.rollback()
            raise
    
    def query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dicts.
        
        Args:
            sql: SQL query string
            params: Optional parameters for parameterized query
        
        Returns:
            List of dictionaries representing rows
        """
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def execute(self, sql: str, params: Optional[Tuple] = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query (auto-commits).
        
        Args:
            sql: SQL query string
            params: Optional parameters for parameterized query
        
        Returns:
            Number of affected rows
        """
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        self.conn.commit()
        return cursor.rowcount
    
    def execute_non_query(self, sql: str, params: Optional[Tuple] = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query without auto-commit (for transactions).
        
        Args:
            sql: SQL query string
            params: Optional parameters for parameterized query
        
        Returns:
            Number of affected rows
        """
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        # Don't commit - caller must handle transaction
        return cursor.rowcount
    
    def execute_batch(self, sql: str, params_list: List[Tuple]) -> int:
        """
        Execute a batch of INSERT/UPDATE/DELETE queries (within a transaction).
        
        Args:
            sql: SQL query string (with placeholders)
            params_list: List of parameter tuples
        
        Returns:
            Total number of affected rows
        """
        cursor = self.conn.cursor()
        cursor.executemany(sql, params_list)
        # Don't commit - caller must handle transaction
        return cursor.rowcount
    
    def begin_transaction(self):
        """Begin a database transaction."""
        self.conn.execute("BEGIN TRANSACTION")
        logger.debug("Transaction started")
    
    def commit_transaction(self):
        """Commit the current transaction."""
        self.conn.commit()
        logger.debug("Transaction committed")
    
    def rollback_transaction(self):
        """Rollback the current transaction."""
        self.conn.rollback()
        logger.debug("Transaction rolled back")
    
    def transaction(self):
        """
        Context manager for database transactions.
        
        Usage:
            with db.transaction():
                db.execute_non_query("INSERT INTO ...")
                db.execute_non_query("UPDATE ...")
            # Automatically commits on success, rolls back on error
        """
        return TransactionContext(self)
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table."""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    
    def get_import_status(self) -> Dict[str, Any]:
        """Get import metadata for all tables."""
        return {
            row['table_name']: {
                'last_imported': row['last_imported'],
                'row_count': row['row_count'],
                'import_timestamp': row['import_timestamp']
            }
            for row in self.query("SELECT * FROM import_metadata")
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Local database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def populate_from_csv(self, csv_dir: Optional[Path] = None, force: bool = False) -> Dict[str, int]:
        """
        Populate database from CSV files.
        
        Args:
            csv_dir: Directory containing CSV files (default: data/csv_exports)
            force: If True, clear existing data before importing
            
        Returns:
            Dictionary with table names and row counts imported
        """
        if csv_dir is None:
            csv_dir = Path(__file__).parent / "data" / "csv_exports"
        
        if not csv_dir.exists():
            raise FileNotFoundError(f"CSV directory not found: {csv_dir}")
        
        # Map CSV files to database tables
        csv_mapping = {
            'current_dispatches.csv': 'current_dispatches',
            'technicians.csv': 'technicians',
            'technician_calendar.csv': 'technician_calendar',
            'dispatch_history.csv': 'dispatch_history',
        }
        
        results = {}
        
        for csv_file, table_name in csv_mapping.items():
            csv_path = csv_dir / csv_file
            
            if not csv_path.exists():
                logger.warning(f"CSV file not found: {csv_path}")
                results[table_name] = 0
                continue
            
            try:
                # Read CSV
                df = pd.read_csv(csv_path)
                row_count = len(df)
                
                logger.info(f"Loading {row_count} rows from {csv_file} into {table_name}")
                
                # Clear existing data if force=True
                if force:
                    cursor = self.conn.cursor()
                    cursor.execute(f"DELETE FROM {table_name}")
                    logger.info(f"  Cleared existing data from {table_name}")
                
                # Insert data
                df.to_sql(table_name, self.conn, if_exists='replace', index=False)
                
                # Update metadata
                self._update_import_metadata(table_name, row_count)
                
                logger.info(f"  ✓ Imported {row_count} rows into {table_name}")
                results[table_name] = row_count
                
            except Exception as e:
                logger.error(f"  ✗ Failed to import {csv_file}: {e}")
                results[table_name] = 0
                raise
        
        self.conn.commit()
        return results
    
    def _update_import_metadata(self, table_name: str, row_count: int):
        """Update import metadata for a table."""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO import_metadata 
            (table_name, last_imported, row_count, import_timestamp)
            VALUES (?, ?, ?, ?)
        """, (table_name, now, row_count, now))
    
    def get_import_status(self) -> List[Dict[str, Any]]:
        """Get import status for all tables."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT table_name, last_imported, row_count, import_timestamp
            FROM import_metadata
            ORDER BY table_name
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'table_name': row[0],
                'last_imported': row[1],
                'row_count': row[2],
                'import_timestamp': row[3]
            })
        
        return results


def main():
    """
    Command-line interface for database operations.
    
    Usage:
        python local_db.py import [--force]  # Import CSV files to database
        python local_db.py status            # Show import status
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python local_db.py import [--force]  # Import CSV files to database")
        print("  python local_db.py status            # Show import status")
        return 1
    
    command = sys.argv[1].lower()
    
    if command == 'import':
        force = '--force' in sys.argv
        
        print("=" * 80)
        print("CSV to SQLite Database Import")
        print("=" * 80)
        print()
        
        db = LocalDatabase()
        
        try:
            print("📥 Importing data from CSV files...")
            if force:
                print("   (Force mode: clearing existing data)")
            print()
            
            results = db.populate_from_csv(force=force)
            
            print()
            print("=" * 80)
            print("Import Summary")
            print("=" * 80)
            
            total_rows = 0
            for table_name, row_count in results.items():
                print(f"  {table_name}: {row_count:,} rows")
                total_rows += row_count
            
            print()
            print(f"✅ Total rows imported: {total_rows:,}")
            print()
            
            # Show import status
            print("=" * 80)
            print("Import Status")
            print("=" * 80)
            
            status = db.get_import_status()
            for item in status:
                print(f"  {item['table_name']}")
                print(f"    Rows: {item['row_count']:,}")
                print(f"    Last imported: {item['last_imported']}")
                print()
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        finally:
            db.close()
        
        print("=" * 80)
        print("✅ Import Complete!")
        print("=" * 80)
        return 0
    
    elif command == 'status':
        print("=" * 80)
        print("Database Import Status")
        print("=" * 80)
        print()
        
        db = LocalDatabase()
        
        try:
            status = db.get_import_status()
            
            if not status:
                print("No import history found.")
                print()
                print("Run 'python local_db.py import' to populate the database.")
            else:
                for item in status:
                    print(f"📊 {item['table_name']}")
                    print(f"   Rows: {item['row_count']:,}")
                    print(f"   Last imported: {item['last_imported']}")
                    print()
        
        finally:
            db.close()
        
        print("=" * 80)
        return 0
    
    else:
        print(f"Unknown command: {command}")
        print()
        print("Available commands:")
        print("  import [--force]  # Import CSV files to database")
        print("  status            # Show import status")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())

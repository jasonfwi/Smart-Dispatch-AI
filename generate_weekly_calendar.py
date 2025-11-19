"""
Generate Weekly Technician Calendar Entries

This script generates technician calendar entries for the upcoming week (Monday-Friday).
It should be run once per week to populate the calendar with new entries.

Features:
- Creates entries for all technicians
- Generates Monday-Friday entries (5 days)
- Defaults to Available=1
- Sets Max_assignments from technician's Workload_capacity
- Uses standard work hours (09:00-17:00)
- Updates both CSV and database
- Prevents duplicate entries
- Logs all changes to change_history
"""

import sqlite3
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
DB_PATH = Path(__file__).parent / "dispatch.db"
CSV_PATH = Path(__file__).parent / "data" / "csv_exports" / "technician_calendar.csv"
TECH_CSV_PATH = Path(__file__).parent / "data" / "csv_exports" / "technicians.csv"

# Default work schedule
DEFAULT_START_TIME = "09:00:00"
DEFAULT_END_TIME = "17:00:00"
WORK_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

class WeeklyCalendarGenerator:
    """Generate weekly calendar entries for all technicians."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Connect to database."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")
    
    def get_next_monday(self, from_date: Optional[datetime] = None) -> datetime:
        """Get the next Monday from the given date (or today)."""
        if from_date is None:
            from_date = datetime.now()
        
        # Calculate days until next Monday (0 = Monday, 6 = Sunday)
        days_ahead = 0 - from_date.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_monday = from_date + timedelta(days=days_ahead)
        return next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def get_technicians(self) -> List[Dict]:
        """Get all technicians from database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT Technician_id, Name, Workload_capacity
            FROM technicians
            ORDER BY Technician_id
        """)
        
        technicians = []
        for row in cursor.fetchall():
            technicians.append({
                'Technician_id': row['Technician_id'],
                'Name': row['Name'],
                'Workload_capacity': row['Workload_capacity']
            })
        
        logger.info(f"Found {len(technicians)} technicians")
        return technicians
    
    def check_existing_entries(self, tech_id: str, dates: List[str]) -> List[str]:
        """Check which dates already have entries for a technician."""
        cursor = self.conn.cursor()
        
        placeholders = ','.join(['?' for _ in dates])
        cursor.execute(f"""
            SELECT Date
            FROM technician_calendar
            WHERE Technician_id = ?
            AND Date IN ({placeholders})
        """, [tech_id] + dates)
        
        existing = [row['Date'] for row in cursor.fetchall()]
        return existing
    
    def generate_week_entries(self, start_monday: datetime, 
                             technicians: List[Dict]) -> List[Dict]:
        """Generate calendar entries for a week (Monday-Friday)."""
        entries = []
        
        for tech in technicians:
            tech_id = tech['Technician_id']
            tech_name = tech['Name']
            workload_capacity = tech['Workload_capacity']
            
            # Generate entries for Monday-Friday
            for day_offset in range(5):  # 0-4 for Mon-Fri
                entry_date = start_monday + timedelta(days=day_offset)
                date_str = entry_date.strftime('%Y-%m-%d')
                day_name = entry_date.strftime('%A')
                
                # Create start/end time strings with the date
                start_datetime = f"{date_str} {DEFAULT_START_TIME}"
                end_datetime = f"{date_str} {DEFAULT_END_TIME}"
                
                entry = {
                    'Technician_id': tech_id,
                    'Date': date_str,
                    'Day_of_week': day_name,
                    'Available': 1,
                    'Start_time': start_datetime,
                    'End_time': end_datetime,
                    'Reason': '',
                    'Max_assignments': workload_capacity
                }
                
                entries.append(entry)
        
        logger.info(f"Generated {len(entries)} calendar entries for week starting {start_monday.strftime('%Y-%m-%d')}")
        return entries
    
    def check_manual_entry(self, tech_id: str, date: str) -> bool:
        """Check if an entry was manually created (via UI)."""
        cursor = self.conn.cursor()
        
        # Check change_history for manual entries
        cursor.execute("""
            SELECT new_data
            FROM change_history
            WHERE table_name = 'technician_calendar'
            AND operation = 'INSERT'
            AND record_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (f"{tech_id}_{date}",))
        
        result = cursor.fetchone()
        if result and result['new_data']:
            try:
                data = json.loads(result['new_data'])
                return data.get('manual_entry', False)
            except:
                pass
        
        return False
    
    def insert_entries_to_db(self, entries: List[Dict]) -> int:
        """Insert new entries into database."""
        cursor = self.conn.cursor()
        inserted = 0
        skipped = 0
        skipped_manual = 0
        
        for entry in entries:
            # Check if entry already exists
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM technician_calendar
                WHERE Technician_id = ? AND Date = ?
            """, (entry['Technician_id'], entry['Date']))
            
            exists = cursor.fetchone()['count'] > 0
            
            if exists:
                # Check if it was manually created
                if self.check_manual_entry(entry['Technician_id'], entry['Date']):
                    skipped_manual += 1
                    logger.debug(f"Skipping {entry['Technician_id']} on {entry['Date']} - manually created")
                else:
                    skipped += 1
                continue
            
            # Insert new entry
            cursor.execute("""
                INSERT INTO technician_calendar
                (Technician_id, Date, Day_of_week, Available, Start_time, End_time, Reason, Max_assignments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry['Technician_id'],
                entry['Date'],
                entry['Day_of_week'],
                entry['Available'],
                entry['Start_time'],
                entry['End_time'],
                entry['Reason'],
                entry['Max_assignments']
            ))
            
            # Log to change_history
            cursor.execute("""
                INSERT INTO change_history
                (timestamp, table_name, operation, record_id, new_data, user_action, can_rollback)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                datetime.now().isoformat(),
                'technician_calendar',
                'INSERT',
                f"{entry['Technician_id']}_{entry['Date']}",
                json.dumps(entry),
                f"Weekly calendar generation for {entry['Date']}"
            ))
            
            inserted += 1
        
        self.conn.commit()
        logger.info(f"Inserted {inserted} new entries, skipped {skipped} existing entries, skipped {skipped_manual} manual entries")
        return inserted
    
    def update_csv(self, entries: List[Dict]) -> int:
        """Update CSV file with new entries."""
        # Read existing CSV
        if CSV_PATH.exists():
            existing_df = pd.read_csv(CSV_PATH)
            logger.info(f"Loaded {len(existing_df)} existing calendar entries from CSV")
        else:
            existing_df = pd.DataFrame()
            logger.warning("CSV file not found, creating new one")
        
        # Create DataFrame from new entries
        new_df = pd.DataFrame(entries)
        
        # Combine and remove duplicates (keep existing entries)
        if not existing_df.empty:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            # Remove duplicates based on Technician_id and Date, keeping first (existing)
            before_count = len(combined_df)
            combined_df = combined_df.drop_duplicates(subset=['Technician_id', 'Date'], keep='first')
            after_count = len(combined_df)
            duplicates_removed = before_count - after_count
            logger.info(f"Removed {duplicates_removed} duplicate entries from CSV")
        else:
            combined_df = new_df
        
        # Sort by Technician_id and Date
        combined_df = combined_df.sort_values(['Technician_id', 'Date'])
        
        # Save to CSV
        combined_df.to_csv(CSV_PATH, index=False)
        logger.info(f"Updated CSV with {len(combined_df)} total entries")
        
        return len(new_df) - (duplicates_removed if not existing_df.empty else 0)
    
    def generate_week(self, weeks_ahead: int = 1, dry_run: bool = False) -> Dict:
        """
        Generate calendar entries for a specific week.
        
        Args:
            weeks_ahead: Number of weeks ahead to generate (1 = next week, 2 = week after, etc.)
            dry_run: If True, only show what would be generated without making changes
        
        Returns:
            Dictionary with generation statistics
        """
        # Get the target Monday
        base_monday = self.get_next_monday()
        target_monday = base_monday + timedelta(weeks=weeks_ahead-1)
        
        logger.info("=" * 80)
        logger.info(f"GENERATING CALENDAR FOR WEEK STARTING: {target_monday.strftime('%Y-%m-%d (%A)')}")
        logger.info(f"Week ending: {(target_monday + timedelta(days=4)).strftime('%Y-%m-%d (%A)')}")
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
        logger.info("=" * 80)
        
        # Get all technicians
        technicians = self.get_technicians()
        
        if not technicians:
            logger.error("No technicians found in database!")
            return {'success': False, 'error': 'No technicians found'}
        
        # Generate entries
        entries = self.generate_week_entries(target_monday, technicians)
        
        # Show sample entries
        logger.info("\nSample entries to be created:")
        logger.info("-" * 80)
        for entry in entries[:5]:
            logger.info(f"  {entry['Technician_id']} | {entry['Date']} ({entry['Day_of_week']}) | "
                       f"Available: {entry['Available']} | Max: {entry['Max_assignments']}")
        if len(entries) > 5:
            logger.info(f"  ... and {len(entries) - 5} more entries")
        logger.info("-" * 80)
        
        if dry_run:
            logger.info("\n✅ DRY RUN COMPLETE - No changes made")
            return {
                'success': True,
                'dry_run': True,
                'week_start': target_monday.strftime('%Y-%m-%d'),
                'entries_generated': len(entries),
                'technicians_count': len(technicians)
            }
        
        # Insert into database
        db_inserted = self.insert_entries_to_db(entries)
        
        # Update CSV
        csv_inserted = self.update_csv(entries)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ CALENDAR GENERATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Week starting: {target_monday.strftime('%Y-%m-%d')}")
        logger.info(f"Technicians: {len(technicians)}")
        logger.info(f"Entries generated: {len(entries)}")
        logger.info(f"Database: {db_inserted} new entries inserted")
        logger.info(f"CSV: {csv_inserted} new entries added")
        logger.info("=" * 80)
        
        return {
            'success': True,
            'week_start': target_monday.strftime('%Y-%m-%d'),
            'week_end': (target_monday + timedelta(days=4)).strftime('%Y-%m-%d'),
            'technicians_count': len(technicians),
            'entries_generated': len(entries),
            'db_inserted': db_inserted,
            'csv_inserted': csv_inserted
        }


def main():
    """Main function with CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate weekly technician calendar entries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate next week's calendar (dry run)
  python generate_weekly_calendar.py --dry-run
  
  # Generate next week's calendar (for real)
  python generate_weekly_calendar.py
  
  # Generate calendar for 2 weeks from now
  python generate_weekly_calendar.py --weeks-ahead 2
  
  # Generate next 4 weeks
  python generate_weekly_calendar.py --generate-multiple 4
        """
    )
    
    parser.add_argument(
        '--weeks-ahead',
        type=int,
        default=1,
        help='Number of weeks ahead to generate (default: 1 = next week)'
    )
    
    parser.add_argument(
        '--generate-multiple',
        type=int,
        help='Generate multiple weeks at once (e.g., 4 = next 4 weeks)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be generated without making changes'
    )
    
    parser.add_argument(
        '--show-next-monday',
        action='store_true',
        help='Just show when the next Monday is and exit'
    )
    
    args = parser.parse_args()
    
    generator = WeeklyCalendarGenerator()
    
    try:
        # Show next Monday
        if args.show_next_monday:
            next_monday = generator.get_next_monday()
            print(f"\nNext Monday: {next_monday.strftime('%Y-%m-%d (%A)')}")
            return 0
        
        # Generate multiple weeks
        if args.generate_multiple:
            print(f"\n🔄 Generating {args.generate_multiple} weeks of calendar entries...")
            results = []
            
            for week_num in range(1, args.generate_multiple + 1):
                result = generator.generate_week(weeks_ahead=week_num, dry_run=args.dry_run)
                results.append(result)
                print()  # Blank line between weeks
            
            # Summary
            if not args.dry_run:
                total_inserted_db = sum(r.get('db_inserted', 0) for r in results)
                total_inserted_csv = sum(r.get('csv_inserted', 0) for r in results)
                print("\n" + "=" * 80)
                print(f"✅ GENERATED {args.generate_multiple} WEEKS")
                print("=" * 80)
                print(f"Total database inserts: {total_inserted_db}")
                print(f"Total CSV inserts: {total_inserted_csv}")
                print("=" * 80)
        
        # Generate single week
        else:
            result = generator.generate_week(weeks_ahead=args.weeks_ahead, dry_run=args.dry_run)
            
            if not result['success']:
                logger.error(f"Generation failed: {result.get('error')}")
                return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during calendar generation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        generator.close()


if __name__ == '__main__':
    exit(main())


"""
Smart Dispatch AI - Local Database Version

This is a modified version that uses SQLite instead of Databricks for faster
local development and testing. All functionality remains the same, but queries
run against a local SQLite database.
"""

import sqlite3
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, date
import pandas as pd

# Import the base classes and utilities from constants
from constants import (
    Location, TechnicianInfo, AvailabilityInfo, RangeCheckResult,
    Assignment, NewDispatch, Status, SCORING_WEIGHTS, DEFAULT_MAX_RANGE_KM,
    EARTH_RADIUS_KM, AVERAGE_SPEED_KMH, TRAVEL_BUFFER_MINUTES, MINUTES_PER_KM,
    MINUTES_PER_HOUR, round_minutes_to_nearest_hour,
    RANGE_EXPANSION_FACTOR, RANGE_EXPANSION_THRESHOLD
)
from local_db import LocalDatabase, DEFAULT_DB_PATH

logger = logging.getLogger(__name__)


class SmartDispatchAILocal:
    """
    Local version of SmartDispatchAI using SQLite instead of Databricks.
    
    This class provides the same interface as SmartDispatchAI but uses
    a local SQLite database for all data operations.
    """
    
    def __init__(self, max_range_km: float = DEFAULT_MAX_RANGE_KM,
                 scoring_weights: Optional[Dict[str, float]] = None,
                 db_path: Optional[str] = None):
        """
        Initialize SmartDispatchAI with local database.
        
        Args:
            max_range_km: Maximum search radius in kilometers
            scoring_weights: Custom scoring weights (optional)
            db_path: Path to SQLite database (default: local_dispatch.db)
        """
        logger.info("Initializing Smart Dispatch AI (Local Mode)...")
        self.max_range_km = max_range_km
        self.scoring_weights = scoring_weights or SCORING_WEIGHTS
        
        # Initialize database connection
        try:
            self.db = LocalDatabase(db_path)
            # Verify database has data
            dispatch_count = self.db.get_table_count('current_dispatches')
            if dispatch_count == 0:
                logger.warning("⚠️ Local database exists but appears empty!")
        except Exception as e:
            logger.error(f"Failed to initialize local database: {e}")
            raise
        
        self._tech_cache: Dict[str, TechnicianInfo] = {}
        self._history_cache: Dict[str, str] = {}
        self._previous_assignments: Dict[str, Dict[str, Any]] = {}  # Track assignments: {dispatch_id: {tech_id, date, hours_deducted}}
        self._pending_dispatches: List[NewDispatch] = []
        self._next_dispatch_id: int = self._get_max_dispatch_id() + 1
        logger.info(f"✓ Local initialization complete (Max Range: {self.max_range_km} km)\n")
    
    def _get_max_dispatch_id(self) -> int:
        """Get the maximum dispatch ID from local database."""
        try:
            result = self.db.query(
                "SELECT MAX(CAST(SUBSTR(Dispatch_id, 2) AS INTEGER)) as max_id FROM current_dispatches WHERE Dispatch_id LIKE 'D%'"
            )
            if result and result[0]['max_id']:
                return int(result[0]['max_id'])
            return 0
        except Exception as e:
            logger.warning(f"Could not determine max dispatch ID: {e}")
            return 0
    
    def _query_to_pandas(self, sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute SQL query and return as pandas DataFrame."""
        return pd.read_sql_query(sql, self.db.conn, params=params)
    
    # Re-implement all the query methods to use SQLite instead of Spark
    
    def get_all_dispatches(self, status: Optional[str] = None, 
                          city: Optional[str] = None, 
                          state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all dispatches with optional filters."""
        sql = "SELECT * FROM current_dispatches WHERE 1=1"
        params = []
        
        if status:
            sql += " AND Status = ?"
            params.append(status)
        if city:
            sql += " AND City = ?"
            params.append(city)
        if state:
            sql += " AND State = ?"
            params.append(state)
        
        return self.db.query(sql, tuple(params) if params else None)
    
    def get_unassigned_dispatches(self, limit: int = 100, 
                                  city: Optional[str] = None, 
                                  state: Optional[str] = None, 
                                  date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get unassigned dispatches with optional filters.
        
        Args:
            limit: Maximum number of dispatches to return
            city: Optional city filter
            state: Optional state filter
            date: Optional date filter (YYYY-MM-DD format)
        
        Returns:
            List of dispatch dictionaries
        """
        sql = """
            SELECT * FROM current_dispatches 
            WHERE (Assigned_technician_id IS NULL OR Assigned_technician_id = '')
        """
        params = []
        
        if city:
            sql += " AND City = ?"
            params.append(city)
        if state:
            sql += " AND State = ?"
            params.append(state)
        if date:
            sql += " AND DATE(Appointment_start_datetime) = ?"
            params.append(date)
        
        sql += " ORDER BY Priority DESC LIMIT ?"
        params.append(limit)
        
        return self.db.query(sql, tuple(params) if params else None)
    
    def get_technician_calendar(self, tech_id: Optional[str] = None,
                                tech_name: Optional[str] = None,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get technician calendar entries."""
        if not tech_id and not tech_name:
            logger.warning("get_technician_calendar called without tech_id or tech_name")
            return None
        
        # If name provided but not ID, find technician by name
        if tech_name and not tech_id:
            tech_sql = "SELECT Technician_id FROM technicians WHERE LOWER(Name) = LOWER(?)"
            tech_result = self.db.query(tech_sql, (tech_name,))
            if not tech_result:
                logger.warning(f"Technician not found by name: {tech_name}")
                return None
            tech_id = tech_result[0]['Technician_id']
            logger.info(f"Found technician ID {tech_id} for name '{tech_name}'")
        
        # Verify technician exists
        tech_check_sql = "SELECT Technician_id, Name, City, State, Primary_skill FROM technicians WHERE Technician_id = ?"
        tech_exists = self.db.query(tech_check_sql, (tech_id,))
        if not tech_exists:
            logger.warning(f"Technician ID '{tech_id}' not found in technicians table")
            return None
        
        # Get calendar entries
        sql = """
            SELECT 
                c.Technician_id,
                t.Name,
                t.City,
                t.State,
                t.Primary_skill,
                c.Date,
                c.Day_of_week,
                c.Available,
                c.Start_time,
                c.End_time,
                c.Reason,
                c.Max_assignments
            FROM technician_calendar c
            JOIN technicians t ON c.Technician_id = t.Technician_id
            WHERE c.Technician_id = ?
        """
        params = [tech_id]
        
        if start_date:
            sql += " AND c.Date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND c.Date <= ?"
            params.append(end_date)
        
        sql += " ORDER BY c.Date"
        
        try:
            df = self._query_to_pandas(sql, tuple(params))
            if df.empty:
                logger.info(f"Technician {tech_id} exists but has no calendar entries (date filter: {start_date} to {end_date})")
                # Return empty DataFrame with technician info for form population
                tech_info = tech_exists[0]
                empty_df = pd.DataFrame([{
                    'Technician_id': tech_info['Technician_id'],
                    'Name': tech_info['Name'],
                    'City': tech_info.get('City', ''),
                    'State': tech_info.get('State', ''),
                    'Primary_skill': tech_info.get('Primary_skill', ''),
                    'Date': None,
                    'Day_of_week': None,
                    'Available': None,
                    'Start_time': None,
                    'End_time': None,
                    'Reason': None,
                    'Max_assignments': None
                }])
                return empty_df
            logger.info(f"Found {len(df)} calendar entries for technician {tech_id}")
            return df
        except Exception as e:
            logger.error(f"Error querying calendar: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def get_technicians_by_location(self, city: Optional[str] = None,
                                    state: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get technicians by location."""
        sql = "SELECT Technician_id, Name, City, State, Primary_skill FROM technicians WHERE 1=1"
        params = []
        
        if city:
            sql += " AND City = ?"
            params.append(city)
        if state:
            sql += " AND State = ?"
            params.append(state)
        
        if not city and not state:
            return None
        
        sql += " ORDER BY Name"
        
        try:
            df = self._query_to_pandas(sql, tuple(params) if params else None)
            return df if not df.empty else None
        except Exception as e:
            logger.error(f"Error querying technicians: {e}")
            return None
    
    def check_technician_availability(self, tech_id: str, date: Optional[str] = None) -> AvailabilityInfo:
        """
        Check if a technician is available (optimized with caching).
        
        If date is provided, checks specific date.
        If date is None, shows all available days.
        """
        tech = self._get_technician_data_cached(tech_id)
        if not tech:
            logger.warning(f"Technician {tech_id} not found!")
            return AvailabilityInfo(available=False, reason="Technician not found")
        
        logger.info(f"Technician: {tech.name}")
        logger.debug(f"Location: {tech.location.city}, {tech.location.state}")
        logger.debug(f"Primary Skill: {tech.primary_skill}")
        
        # If no date provided, return general availability info
        if not date:
            # Get all calendar entries
            cal_result = self.db.query(
                "SELECT * FROM technician_calendar WHERE Technician_id = ? ORDER BY Date",
                (tech_id,)
            )
            
            if not cal_result:
                return AvailabilityInfo(available=False, reason="No calendar entries found")
            
            available_count = sum(1 for entry in cal_result if entry.get("Available") == 1)
            total_count = len(cal_result)
            
            logger.info(f"CALENDAR OVERVIEW: Total Entries: {total_count}, Available: {available_count}, Unavailable: {total_count - available_count}")
            
            return AvailabilityInfo(available=True, reason=f"{available_count} of {total_count} days available")
        
        # Check specific date
        cal_result = self.db.query(
            "SELECT * FROM technician_calendar WHERE Technician_id = ? AND Date = ?",
            (tech_id, date)
        )
        
        if not cal_result:
            logger.warning(f"No calendar entry found for {date}")
            return AvailabilityInfo(available=False, reason="No calendar entry")
        
        cal_entry = cal_result[0]
        available = int(cal_entry.get("Available", 0)) if cal_entry.get("Available") else 0
        
        if available == 0:
            reason = str(cal_entry.get("Reason", "Not specified")) if cal_entry.get("Reason") else "Not specified"
            logger.warning(f"Technician is NOT AVAILABLE on {date}. Reason: {reason}")
            return AvailabilityInfo(available=False, reason=reason)
        
        max_assignments = int(cal_entry.get("Max_assignments", 0)) if cal_entry.get("Max_assignments") else 0
        max_assignments_minutes = max_assignments * MINUTES_PER_HOUR
        assigned_minutes = self._get_assigned_minutes(tech_id, date)
        
        logger.info(f"Technician IS AVAILABLE on {date}")
        start_time_val = str(cal_entry.get("Start_time", "N/A")) if cal_entry.get("Start_time") else "N/A"
        end_time_val = str(cal_entry.get("End_time", "N/A")) if cal_entry.get("End_time") else "N/A"
        logger.debug(f"Availability Window: {start_time_val} - {end_time_val}")
        logger.debug(f"Max Assignments: {max_assignments} hours ({max_assignments_minutes} minutes)")
        logger.debug(f"Total Assigned Minutes: {assigned_minutes}")
        logger.debug(f"Remaining Capacity: {max_assignments_minutes - assigned_minutes} minutes")
        utilization_pct = (assigned_minutes/max_assignments_minutes*100) if max_assignments_minutes > 0 else 0.0
        logger.debug(f"Utilization: {utilization_pct:.1f}%")
        
        start_time_str = str(cal_entry.get("Start_time")) if cal_entry.get("Start_time") else None
        end_time_str = str(cal_entry.get("End_time")) if cal_entry.get("End_time") else None
        
        return AvailabilityInfo(
            available=True,
            start_time=start_time_str,
            end_time=end_time_str,
            available_minutes=max_assignments_minutes,
            assigned_minutes=assigned_minutes
        )
    
    def _get_assigned_minutes(self, tech_id: str, date: str) -> int:
        """Get total assigned minutes for a technician on a specific date."""
        try:
            result = self.db.query(
                """
                SELECT COALESCE(SUM(Duration_min), 0) as total_minutes
                FROM current_dispatches
                WHERE Assigned_technician_id = ? 
                AND DATE(Appointment_start_datetime) = ?
                """,
                (tech_id, date)
            )
            
            if result:
                return int(result[0].get('total_minutes', 0)) if result[0].get('total_minutes') else 0
            return 0
        except Exception as e:
            logger.error(f"Error getting assigned minutes for {tech_id} on {date}: {e}")
            return 0
    
    def _get_technician_data_cached(self, tech_id: str) -> Optional[TechnicianInfo]:
        """Get technician data with caching."""
        if tech_id in self._tech_cache:
            return self._tech_cache[tech_id]
        
        try:
            result = self.db.query(
                "SELECT * FROM technicians WHERE Technician_id = ?",
                (tech_id,)
            )
            
            if not result:
                return None
            
            tech_row = result[0]
            tech_info = TechnicianInfo(
                technician_id=tech_id,
                name=str(tech_row.get("Name", "")) if tech_row.get("Name") else "",
                location=Location(
                    city=str(tech_row.get("City", "")) if tech_row.get("City") else "",
                    state=str(tech_row.get("State", "")) if tech_row.get("State") else "",
                    latitude=float(tech_row.get("Latitude", 0)) if tech_row.get("Latitude") else 0.0,
                    longitude=float(tech_row.get("Longitude", 0)) if tech_row.get("Longitude") else 0.0
                ),
                primary_skill=str(tech_row.get("Primary_skill", "")) if tech_row.get("Primary_skill") else "",
                current_assignments=int(tech_row.get("Current_assignments", 0)) if tech_row.get("Current_assignments") else 0,
                workload_capacity=int(tech_row.get("Workload_capacity", 0)) if tech_row.get("Workload_capacity") else 0
            )
            
            self._tech_cache[tech_id] = tech_info
            return tech_info
        except Exception as e:
            logger.error(f"Error getting technician data for {tech_id}: {e}")
            return None
    
    def get_available_technicians(self, target_date: str, 
                                 required_skill: Optional[str] = None,
                                 city: Optional[str] = None,
                                 state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available technicians for a date."""
        sql = """
            SELECT 
                t.*,
                c.Available,
                c.Start_time,
                c.End_time,
                c.Max_assignments
            FROM technicians t
            JOIN technician_calendar c ON t.Technician_id = c.Technician_id
            WHERE c.Date = ? AND c.Available = 1
        """
        params = [target_date]
        
        if required_skill:
            sql += " AND t.Primary_skill = ?"
            params.append(required_skill)
        if city:
            sql += " AND t.City = ?"
            params.append(city)
        if state:
            sql += " AND t.State = ?"
            params.append(state)
        
        return self.db.query(sql, tuple(params))
    
    def get_city_capacity(self, city: Optional[str] = None,
                         state: Optional[str] = None,
                         target_date: Optional[str] = None) -> Dict[str, Any]:
        """Get capacity information for a city/state."""
        if not city and not state:
            # Overview mode - get all cities/states
            sql = """
                SELECT 
                    t.City,
                    t.State,
                    COUNT(DISTINCT t.Technician_id) as total_technicians,
                    SUM(c.Max_assignments) as total_capacity,
                    SUM(COALESCE(COUNT(DISTINCT d.Dispatch_id), 0)) as assigned_count
                FROM technicians t
                JOIN technician_calendar c ON t.Technician_id = c.Technician_id
                LEFT JOIN current_dispatches d ON d.Assigned_technician_id = t.Technician_id
                    AND d.Appointment_start_time LIKE c.Date || '%'
                WHERE c.Date = ? AND c.Available = 1
                GROUP BY t.City, t.State
            """
            if target_date:
                results = self.db.query(sql, (target_date,))
            else:
                results = []
            
            return {
                'overview': [
                    {
                        'city': r['City'],
                        'state': r['State'],
                        'total_technicians': r['total_technicians'],
                        'total_capacity': r['total_capacity'],
                        'assigned_count': r['assigned_count'],
                        'available_capacity': r['total_capacity'] - r['assigned_count']
                    }
                    for r in results
                ]
            }
        
        # Single city/state mode
        sql = """
            SELECT 
                COUNT(DISTINCT t.Technician_id) as total_technicians,
                SUM(c.Max_assignments) as total_capacity,
                COUNT(DISTINCT d.Dispatch_id) as assigned_count
            FROM technicians t
            JOIN technician_calendar c ON t.Technician_id = c.Technician_id
            LEFT JOIN current_dispatches d ON d.Assigned_technician_id = t.Technician_id
                AND d.Appointment_start_time LIKE c.Date || '%'
            WHERE c.Date = ? AND c.Available = 1
        """
        params = [target_date] if target_date else []
        
        if city:
            sql += " AND t.City = ?"
            params.append(city)
        if state:
            sql += " AND t.State = ?"
            params.append(state)
        
        result = self.db.query(sql, tuple(params) if params else None)
        
        if result:
            r = result[0]
            return {
                'city': city,
                'state': state,
                'total_technicians': r['total_technicians'] or 0,
                'total_capacity': r['total_capacity'] or 0,
                'assigned_count': r['assigned_count'] or 0,
                'available_capacity': (r['total_capacity'] or 0) - (r['assigned_count'] or 0)
            }
        
        return {
            'city': city,
            'state': state,
            'total_technicians': 0,
            'total_capacity': 0,
            'assigned_count': 0,
            'available_capacity': 0
        }
    
    def _update_technician_calendar_capacity(self, tech_id: str, date: str, 
                                            hours_to_adjust: int, 
                                            restore: bool = False) -> bool:
        """
        Update technician calendar capacity by adjusting available hours.
        
        This is called automatically when a dispatch is assigned or unassigned.
        The dispatch duration + travel time is rounded to the nearest hour before adjusting capacity.
        
        Args:
            tech_id: Technician ID
            date: Date in 'YYYY-MM-DD' format
            hours_to_adjust: Number of hours to adjust (positive value)
            restore: If True, restore capacity (add hours back). If False, reduce capacity.
        
        Returns:
            True if update succeeded, False otherwise
        """
        try:
            # Get current calendar entry
            result = self.db.query(
                "SELECT * FROM technician_calendar WHERE Technician_id = ? AND Date = ?",
                (tech_id, date)
            )
            
            if not result:
                logger.warning(f"No calendar entry found for {tech_id} on {date}")
                return False
            
            cal_entry = result[0]
            current_max = int(cal_entry.get("Max_assignments", 0)) if cal_entry.get("Max_assignments") else 0
            
            # Calculate new max assignments
            if restore:
                # Restore capacity (add hours back)
                new_max = current_max + abs(hours_to_adjust)
                action = "restored"
            else:
                # Reduce capacity (subtract hours)
                new_max = max(0, current_max - abs(hours_to_adjust))
                action = "reduced"
            
            # Update calendar entry within transaction
            sql = """
                UPDATE technician_calendar 
                SET Max_assignments = ?
                WHERE Technician_id = ? AND Date = ?
            """
            rows_affected = self.db.execute_non_query(sql, (new_max, tech_id, date))
            
            if rows_affected == 0:
                logger.warning(f"No rows updated for {tech_id} on {date}")
                return False
            
            logger.debug(f"Calendar capacity update for {tech_id} on {date}: "
                        f"{current_max} hrs -> {new_max} hrs ({action} by {abs(hours_to_adjust)} hrs)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update calendar capacity for {tech_id} on {date}: {e}")
            return False
    
    def _restore_technician_calendar_capacity(self, dispatch_id: str, tech_id: str, date: str) -> bool:
        """
        Restore technician calendar capacity when a dispatch is unassigned.
        
        This calculates the original duration + travel time that was deducted and restores it.
        
        Args:
            dispatch_id: Dispatch ID that was unassigned
            tech_id: Technician ID
            date: Date in 'YYYY-MM-DD' format
        
        Returns:
            True if restoration succeeded, False otherwise
        """
        try:
            # Get the dispatch to find duration and calculate travel time
            result = self.db.query(
                "SELECT * FROM current_dispatches WHERE Dispatch_id = ?",
                (dispatch_id,)
            )
            
            if not result:
                logger.warning(f"Dispatch {dispatch_id} not found for capacity restoration")
                return False
            
            dispatch_row = result[0]
            
            # Get technician location to calculate travel time
            tech_result = self.db.query(
                "SELECT * FROM technicians WHERE Technician_id = ?",
                (tech_id,)
            )
            
            if not tech_result:
                logger.warning(f"Technician {tech_id} not found for capacity restoration")
                return False
            
            tech_row = tech_result[0]
            
            # Get dispatch location
            dispatch_lat = float(dispatch_row.get("Customer_latitude", 0)) if dispatch_row.get("Customer_latitude") else 0.0
            dispatch_lon = float(dispatch_row.get("Customer_longitude", 0)) if dispatch_row.get("Customer_longitude") else 0.0
            
            tech_lat = float(tech_row.get("Latitude", 0)) if tech_row.get("Latitude") else 0.0
            tech_lon = float(tech_row.get("Longitude", 0)) if tech_row.get("Longitude") else 0.0
            
            if dispatch_lat == 0.0 or dispatch_lon == 0.0 or tech_lat == 0.0 or tech_lon == 0.0:
                logger.warning(f"Invalid coordinates for dispatch {dispatch_id} or technician {tech_id}")
                # Still restore duration without travel time
                duration_min = int(dispatch_row.get("Duration_min", 0)) if dispatch_row.get("Duration_min") else 0
                rounded_duration_min = round_minutes_to_nearest_hour(duration_min)
                hours_to_restore = rounded_duration_min // MINUTES_PER_HOUR
            else:
                # Calculate distance using Haversine formula
                from math import radians, sin, cos, asin, sqrt
                EARTH_RADIUS_KM = 6371.0
                
                lat1, lon1 = radians(tech_lat), radians(tech_lon)
                lat2, lon2 = radians(dispatch_lat), radians(dispatch_lon)
                
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                distance_km = EARTH_RADIUS_KM * c
                
                # Calculate travel time
                AVERAGE_SPEED_KMH = 40.0
                TRAVEL_BUFFER_MINUTES = 15
                MINUTES_PER_KM = 60.0 / AVERAGE_SPEED_KMH
                travel_time_min = distance_km * MINUTES_PER_KM + TRAVEL_BUFFER_MINUTES
                
                # Get dispatch duration
                duration_min = int(dispatch_row.get("Duration_min", 0)) if dispatch_row.get("Duration_min") else 0
                
                # Total time = duration + travel time (round to nearest hour)
                total_time_min = duration_min + int(travel_time_min)
                rounded_total_min = round_minutes_to_nearest_hour(total_time_min)
                hours_to_restore = rounded_total_min // MINUTES_PER_HOUR
            
            # Restore capacity
            return self._update_technician_calendar_capacity(
                tech_id, date, hours_to_restore, restore=True
            )
            
        except Exception as e:
            logger.error(f"Failed to restore calendar capacity for {tech_id} on {date}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def update_technician_calendar(self, tech_id: str, date: str,
                                  available: Optional[int] = None,
                                  start_time: Optional[str] = None,
                                  end_time: Optional[str] = None,
                                  max_assignments: Optional[int] = None,
                                  reason: Optional[str] = None,
                                  city: Optional[str] = None,
                                  state: Optional[str] = None,
                                  update_type: str = 'single') -> bool:
        """
        Update technician calendar entry using a transaction.
        
        Args:
            tech_id: Technician ID
            date: Date to update
            available: Availability flag (1 for available, 0 for unavailable)
            start_time: Start time (optional)
            end_time: End time (optional)
            max_assignments: Maximum assignments (optional)
            reason: Reason for unavailability (optional)
            city: City for permanent move (optional)
            state: State for permanent move (optional)
            update_type: 'single' for single day update, 'permanent' for permanent move
        
        Returns:
            True if update succeeded, False otherwise
        """
        logger.info(f"Update requested for {tech_id} on {date} ({update_type})")
        logger.debug(f"  Available: {available}, Max: {max_assignments}, City: {city}, State: {state}")
        
        try:
            # Use transaction for atomic update
            with self.db.transaction():
                # First, verify calendar entry exists
                result = self.db.query(
                    "SELECT * FROM technician_calendar WHERE Technician_id = ? AND Date = ?",
                    (tech_id, date)
                )
                
                if not result:
                    logger.warning(f"Calendar entry not found for {tech_id} on {date}")
                    return False
                
                # Build UPDATE statement dynamically based on provided fields
                update_fields = []
                update_values = []
                
                if start_time is not None:
                    update_fields.append("Start_time = ?")
                    update_values.append(start_time)
                
                if end_time is not None:
                    update_fields.append("End_time = ?")
                    update_values.append(end_time)
                
                if available is not None:
                    update_fields.append("Available = ?")
                    update_values.append(available)
                
                if max_assignments is not None:
                    update_fields.append("Max_assignments = ?")
                    update_values.append(max_assignments)
                
                if reason is not None:
                    update_fields.append("Reason = ?")
                    update_values.append(reason)
                
                if city is not None:
                    update_fields.append("City = ?")
                    update_values.append(city)
                
                if state is not None:
                    update_fields.append("State = ?")
                    update_values.append(state)
                
                if not update_fields:
                    logger.warning("No fields to update")
                    return False
                
                # Add WHERE clause values
                update_values.extend([tech_id, date])
                
                # Execute UPDATE
                sql = f"""
                    UPDATE technician_calendar 
                    SET {', '.join(update_fields)}
                    WHERE Technician_id = ? AND Date = ?
                """
                
                rows_affected = self.db.execute_non_query(sql, tuple(update_values))
                
                if rows_affected == 0:
                    logger.warning(f"No rows updated for {tech_id} on {date}")
                    return False
                
                logger.debug(f"Updated {rows_affected} calendar entry(ies)")
                
                # If permanent move, update technician's city/state in technicians table
                if update_type == 'permanent' and (city or state):
                    tech_update_fields = []
                    tech_update_values = []
                    
                    if city:
                        tech_update_fields.append("City = ?")
                        tech_update_values.append(city)
                    
                    if state:
                        tech_update_fields.append("State = ?")
                        tech_update_values.append(state)
                    
                    if tech_update_fields:
                        tech_update_values.append(tech_id)
                        tech_sql = f"""
                            UPDATE technicians 
                            SET {', '.join(tech_update_fields)}
                            WHERE Technician_id = ?
                        """
                        tech_rows = self.db.execute_non_query(tech_sql, tuple(tech_update_values))
                        logger.debug(f"Updated technician location: {tech_rows} row(s) affected")
                
                # Transaction will auto-commit on success
                logger.info(f"Successfully updated calendar entry for {tech_id} on {date}")
                return True
                
        except Exception as e:
            error_msg = f"Failed to update calendar entry: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_unique_states(self) -> list:
        """Get list of unique states from dispatch data."""
        try:
            result = self.db.query("SELECT DISTINCT State FROM current_dispatches WHERE State IS NOT NULL ORDER BY State")
            states = [row['State'] for row in result if row['State']]
            states = sorted(set(states))
            return [""] + states  # Include blank option first
        except Exception as e:
            logger.error(f"Error getting unique states: {e}")
            return [""]
    
    def get_unique_cities(self, state: Optional[str] = None) -> list:
        """Get list of unique cities, optionally filtered by state."""
        try:
            sql = "SELECT DISTINCT City FROM current_dispatches WHERE City IS NOT NULL"
            params = None
            
            if state:
                sql += " AND State = ?"
                params = (state,)
            
            sql += " ORDER BY City"
            
            result = self.db.query(sql, params)
            cities = [row['City'] for row in result if row['City']]
            cities = sorted(set(cities))
            return [""] + cities  # Include blank option first
        except Exception as e:
            logger.error(f"Error getting unique cities: {e}")
            return [""]
    
    def get_city_state_mapping(self) -> dict:
        """Get mapping of cities to their states."""
        try:
            result = self.db.query(
                "SELECT DISTINCT City, State FROM current_dispatches WHERE City IS NOT NULL AND State IS NOT NULL"
            )
            mapping = {}
            for row in result:
                city = row['City']
                state = row['State']
                if city and state:
                    # If city exists in multiple states, use the most common one
                    if city not in mapping:
                        mapping[city] = state
            return mapping
        except Exception as e:
            logger.error(f"Error getting city-state mapping: {e}")
            return {}
    
    def get_pending_dispatches(self) -> List[Dict[str, Any]]:
        """Get all pending dispatches that haven't been committed to database."""
        return [d.to_dict() for d in self._pending_dispatches]
    
    def clear_pending_dispatches(self) -> Dict[str, Any]:
        """Clear all pending dispatches from memory without committing."""
        count = len(self._pending_dispatches)
        self._pending_dispatches.clear()
        logger.info(f"Cleared {count} pending dispatches")
        return {
            "success": True,
            "cleared_count": count,
            "message": f"Cleared {count} pending dispatch(es) from memory"
        }
    
    def commit_pending_dispatches(self) -> Dict[str, Any]:
        """
        Commit all pending dispatches to the database using a transaction.
        
        This ensures atomicity - either all dispatches are committed or none are.
        If any dispatch fails, the entire transaction is rolled back.
        
        Returns:
            Dictionary with commit result including success status and count
        """
        if not self._pending_dispatches:
            return {
                "success": True,
                "committed_count": 0,
                "message": "No pending dispatches to commit"
            }
        
        count = len(self._pending_dispatches)
        logger.info(f"Starting transaction to commit {count} pending dispatch(es)")
        
        try:
            # Use transaction context manager for atomic operation
            with self.db.transaction():
                # Convert pending dispatches to list of dicts
                dispatch_dicts = [d.to_dict() for d in self._pending_dispatches]
                
                # Prepare all INSERT statements
                insert_statements = []
                for dispatch_dict in dispatch_dicts:
                    # Convert datetime to string for SQLite
                    appointment_str = dispatch_dict.get("Appointment_start_datetime")
                    if isinstance(appointment_str, datetime):
                        appointment_str = appointment_str.isoformat()
                        dispatch_dict["Appointment_start_datetime"] = appointment_str
                    
                    # Map NewDispatch fields to database column names
                    db_dict = {
                        "Dispatch_id": f"D{dispatch_dict.get('Dispatch_id', self._next_dispatch_id)}",
                        "Street": dispatch_dict.get("Street", dispatch_dict.get("customer_address", "")),
                        "City": dispatch_dict.get("City", dispatch_dict.get("city", "")),
                        "State": dispatch_dict.get("State", dispatch_dict.get("state", "")),
                        "Customer_latitude": dispatch_dict.get("Customer_latitude", dispatch_dict.get("customer_latitude", 0.0)),
                        "Customer_longitude": dispatch_dict.get("Customer_longitude", dispatch_dict.get("customer_longitude", 0.0)),
                        "Appointment_start_datetime": appointment_str,
                        "Duration_min": dispatch_dict.get("Duration_min", dispatch_dict.get("duration_min", 0)),
                        "Required_skill": dispatch_dict.get("Required_skill", dispatch_dict.get("required_skill", "")),
                        "Priority": dispatch_dict.get("Priority", dispatch_dict.get("priority", "")),
                        "Status": dispatch_dict.get("Status", dispatch_dict.get("status", "pending")),
                        "Assigned_technician_id": dispatch_dict.get("Assigned_technician_id", dispatch_dict.get("assigned_technician_id"))
                    }
                    
                    # Build INSERT statement with only non-None values
                    columns = [k for k, v in db_dict.items() if v is not None]
                    placeholders = ', '.join(['?' for _ in columns])
                    values = [db_dict[col] for col in columns]
                    
                    columns_str = ', '.join([f'"{c}"' for c in columns])
                    sql = f"INSERT INTO current_dispatches ({columns_str}) VALUES ({placeholders})"
                    insert_statements.append((sql, tuple(values)))
                
                # Execute all inserts within the transaction
                total_rows = 0
                for sql, params in insert_statements:
                    rows_affected = self.db.execute_non_query(sql, params)
                    total_rows += rows_affected
                    logger.debug(f"Inserted dispatch: {rows_affected} row(s) affected")
                
                logger.info(f"Successfully inserted {total_rows} dispatch(es) within transaction")
                
                # Update technician calendars for assigned dispatches (within same transaction)
                assigned_count = 0
                for dispatch in self._pending_dispatches:
                    if dispatch.assigned_technician_id:
                        try:
                            # Get dispatch date
                            dispatch_date = dispatch.appointment_start_datetime.date() if isinstance(dispatch.appointment_start_datetime, datetime) else dispatch.appointment_start_datetime
                            date_str = dispatch_date.strftime("%Y-%m-%d") if hasattr(dispatch_date, 'strftime') else str(dispatch_date)
                            
                            # Get technician to calculate travel time
                            tech_result = self.db.query(
                                "SELECT * FROM technicians WHERE Technician_id = ?",
                                (dispatch.assigned_technician_id,)
                            )
                            travel_time_min = 0.0
                            
                            if tech_result:
                                tech_row = tech_result[0]
                                tech_lat = float(tech_row.get("Latitude", 0)) if tech_row.get("Latitude") else 0.0
                                tech_lon = float(tech_row.get("Longitude", 0)) if tech_row.get("Longitude") else 0.0
                                
                                if tech_lat != 0.0 and tech_lon != 0.0 and dispatch.customer_latitude != 0.0 and dispatch.customer_longitude != 0.0:
                                    # Calculate distance using Haversine formula
                                    from math import radians, sin, cos, asin, sqrt
                                    EARTH_RADIUS_KM = 6371.0
                                    
                                    lat1, lon1 = radians(tech_lat), radians(tech_lon)
                                    lat2, lon2 = radians(dispatch.customer_latitude), radians(dispatch.customer_longitude)
                                    
                                    dlat = lat2 - lat1
                                    dlon = lon2 - lon1
                                    
                                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                                    c = 2 * asin(sqrt(a))
                                    distance_km = EARTH_RADIUS_KM * c
                                    
                                    # Calculate travel time
                                    AVERAGE_SPEED_KMH = 40.0
                                    TRAVEL_BUFFER_MINUTES = 15
                                    MINUTES_PER_KM = 60.0 / AVERAGE_SPEED_KMH
                                    travel_time_min = distance_km * MINUTES_PER_KM + TRAVEL_BUFFER_MINUTES
                            
                            # Total time = duration + travel time (round to nearest hour)
                            total_time_min = dispatch.duration_min + int(travel_time_min)
                            rounded_total_min = round_minutes_to_nearest_hour(total_time_min)
                            hours_to_reduce = rounded_total_min // MINUTES_PER_HOUR
                            
                            # Update calendar capacity within transaction (reduce by duration + travel time)
                            self._update_technician_calendar_capacity(
                                dispatch.assigned_technician_id,
                                date_str,
                                hours_to_reduce,
                                restore=False
                            )
                            assigned_count += 1
                            logger.debug(f"Updated calendar for {dispatch.assigned_technician_id} on {date_str}: "
                                       f"-{hours_to_reduce} hours (duration: {dispatch.duration_min} min, "
                                       f"travel: {travel_time_min:.1f} min, total: {total_time_min} min)")
                        except Exception as e:
                            logger.error(f"Failed to update calendar for technician {dispatch.assigned_technician_id}: {e}")
                            # Exception will cause transaction rollback
                            raise  # Re-raise to trigger rollback
                
                if assigned_count > 0:
                    logger.info(f"Updated calendar capacity for {assigned_count} technician assignment(s)")
                
                # Track new assignments for future capacity restoration
                for dispatch in self._pending_dispatches:
                    if dispatch.assigned_technician_id:
                        dispatch_date = dispatch.appointment_start_datetime.date() if isinstance(dispatch.appointment_start_datetime, datetime) else dispatch.appointment_start_datetime
                        date_str = dispatch_date.strftime("%Y-%m-%d") if hasattr(dispatch_date, 'strftime') else str(dispatch_date)
                        
                        # Calculate hours deducted (already calculated above)
                        tech_result = self.db.query(
                            "SELECT * FROM technicians WHERE Technician_id = ?",
                            (dispatch.assigned_technician_id,)
                        )
                        travel_time_min = 0.0
                        if tech_result:
                            tech_row = tech_result[0]
                            tech_lat = float(tech_row.get("Latitude", 0)) if tech_row.get("Latitude") else 0.0
                            tech_lon = float(tech_row.get("Longitude", 0)) if tech_row.get("Longitude") else 0.0
                            
                            if tech_lat != 0.0 and tech_lon != 0.0 and dispatch.customer_latitude != 0.0 and dispatch.customer_longitude != 0.0:
                                from math import radians, sin, cos, asin, sqrt
                                EARTH_RADIUS_KM = 6371.0
                                lat1, lon1 = radians(tech_lat), radians(tech_lon)
                                lat2, lon2 = radians(dispatch.customer_latitude), radians(dispatch.customer_longitude)
                                dlat = lat2 - lat1
                                dlon = lon2 - lon1
                                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                                c = 2 * asin(sqrt(a))
                                distance_km = EARTH_RADIUS_KM * c
                                AVERAGE_SPEED_KMH = 40.0
                                TRAVEL_BUFFER_MINUTES = 15
                                MINUTES_PER_KM = 60.0 / AVERAGE_SPEED_KMH
                                travel_time_min = distance_km * MINUTES_PER_KM + TRAVEL_BUFFER_MINUTES
                        
                        total_time_min = dispatch.duration_min + int(travel_time_min)
                        rounded_total_min = round_minutes_to_nearest_hour(total_time_min)
                        hours_deducted = rounded_total_min // MINUTES_PER_HOUR
                        
                        # Store assignment info for tracking
                        self._previous_assignments[str(dispatch.dispatch_id)] = {
                            "tech_id": dispatch.assigned_technician_id,
                            "date": date_str,
                            "hours_deducted": hours_deducted
                        }
            
            # Transaction committed successfully - now clear pending list and reload data
            logger.info(f"Transaction committed successfully - {count} dispatch(es) saved to database")
            
            # Clear pending list (only after successful commit)
            self._pending_dispatches.clear()
            
            # Reload data to include new dispatches
            logger.debug("Reloading data to include new dispatches...")
            old_assignments = dict(self._previous_assignments)  # Copy for comparison
            self.curr_df, self.tech_df, self.cal_df, self.history_df = self._load_data()
            
            # Check for unassigned dispatches and restore capacity
            restored_count = 0
            with self.db.transaction():
                for dispatch_id, assignment_info in list(old_assignments.items()):
                    # Check current assignment status
                    current_result = self.db.query(
                        "SELECT Assigned_technician_id FROM current_dispatches WHERE Dispatch_id = ?",
                        (dispatch_id,)
                    )
                    
                    current_tech_id = None
                    if current_result:
                        current_tech_id = str(current_result[0].get("Assigned_technician_id", "")) if current_result[0].get("Assigned_technician_id") else None
                    
                    previous_tech_id = assignment_info.get("tech_id")
                    
                    # If technician was removed or changed, restore capacity
                    if previous_tech_id and (not current_tech_id or current_tech_id != previous_tech_id):
                        try:
                            date_str = assignment_info.get("date")
                            hours_deducted = assignment_info.get("hours_deducted", 0)
                            if date_str and hours_deducted > 0:
                                self._update_technician_calendar_capacity(
                                    previous_tech_id, date_str, hours_deducted, restore=True
                                )
                                restored_count += 1
                                logger.info(f"Restored {hours_deducted} hours capacity for {previous_tech_id} on {date_str} "
                                          f"(dispatch {dispatch_id} unassigned)")
                        except Exception as e:
                            logger.error(f"Failed to restore capacity for dispatch {dispatch_id}: {e}")
                            raise  # Re-raise to trigger rollback
                    
                    # Remove from tracking if dispatch no longer exists or was unassigned
                    if not current_result or (current_result and not current_tech_id):
                        self._previous_assignments.pop(dispatch_id, None)
                    elif current_tech_id != previous_tech_id:
                        # Technician changed - remove old tracking
                        self._previous_assignments.pop(dispatch_id, None)
                
                # Update tracking for currently assigned dispatches
                assigned_result = self.db.query(
                    "SELECT Dispatch_id, Assigned_technician_id, Appointment_start_datetime, "
                    "Duration_min, Customer_latitude, Customer_longitude, City, State "
                    "FROM current_dispatches "
                    "WHERE Assigned_technician_id IS NOT NULL AND Assigned_technician_id != ''"
                )
                
                for row in assigned_result:
                    dispatch_id = str(row.get("Dispatch_id", ""))
                    tech_id = str(row.get("Assigned_technician_id", ""))
                    appointment_dt = row.get("Appointment_start_datetime")
                    
                    if not dispatch_id or not tech_id or not appointment_dt:
                        continue
                    
                    # Parse date
                    if isinstance(appointment_dt, str):
                        from datetime import datetime as dt
                        try:
                            appointment_dt = dt.fromisoformat(appointment_dt.replace('Z', '+00:00'))
                        except:
                            continue
                    
                    date_str = appointment_dt.strftime("%Y-%m-%d") if hasattr(appointment_dt, 'strftime') else str(appointment_dt)
                    
                    # Calculate hours if not already tracked
                    if dispatch_id not in self._previous_assignments:
                        tech_result = self.db.query(
                            "SELECT Latitude, Longitude FROM technicians WHERE Technician_id = ?",
                            (tech_id,)
                        )
                        
                        travel_time_min = 0.0
                        if tech_result:
                            tech_row = tech_result[0]
                            tech_lat = float(tech_row.get("Latitude", 0)) if tech_row.get("Latitude") else 0.0
                            tech_lon = float(tech_row.get("Longitude", 0)) if tech_row.get("Longitude") else 0.0
                            dispatch_lat = float(row.get("Customer_latitude", 0)) if row.get("Customer_latitude") else 0.0
                            dispatch_lon = float(row.get("Customer_longitude", 0)) if row.get("Customer_longitude") else 0.0
                            
                            if tech_lat != 0.0 and tech_lon != 0.0 and dispatch_lat != 0.0 and dispatch_lon != 0.0:
                                from math import radians, sin, cos, asin, sqrt
                                EARTH_RADIUS_KM = 6371.0
                                lat1, lon1 = radians(tech_lat), radians(tech_lon)
                                lat2, lon2 = radians(dispatch_lat), radians(dispatch_lon)
                                dlat = lat2 - lat1
                                dlon = lon2 - lon1
                                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                                c = 2 * asin(sqrt(a))
                                distance_km = EARTH_RADIUS_KM * c
                                AVERAGE_SPEED_KMH = 40.0
                                TRAVEL_BUFFER_MINUTES = 15
                                MINUTES_PER_KM = 60.0 / AVERAGE_SPEED_KMH
                                travel_time_min = distance_km * MINUTES_PER_KM + TRAVEL_BUFFER_MINUTES
                        
                        duration_min = int(row.get("Duration_min", 0)) if row.get("Duration_min") else 0
                        total_time_min = duration_min + int(travel_time_min)
                        rounded_total_min = round_minutes_to_nearest_hour(total_time_min)
                        hours_deducted = rounded_total_min // MINUTES_PER_HOUR
                        
                        self._previous_assignments[dispatch_id] = {
                            "tech_id": tech_id,
                            "date": date_str,
                            "hours_deducted": hours_deducted
                        }
            
            if restored_count > 0:
                logger.info(f"Restored calendar capacity for {restored_count} unassigned dispatch(es)")
            
            return {
                "success": True,
                "committed_count": count,
                "restored_count": restored_count,
                "message": f"Successfully committed {count} dispatch(es) to database"
            }
            
        except Exception as e:
            error_msg = f"Failed to commit dispatches: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            logger.warning(f"Transaction rolled back - {count} dispatch(es) remain in pending list")
            return {
                "success": False,
                "error": error_msg,
                "committed_count": 0,
                "pending_count": count  # Return count of dispatches that remain pending
            }
    
    def get_valid_skills(self) -> List[str]:
        """Get all valid skills from technician database."""
        try:
            result = self.db.query("SELECT DISTINCT Primary_skill FROM technicians WHERE Primary_skill IS NOT NULL ORDER BY Primary_skill")
            skills = [row['Primary_skill'] for row in result if row['Primary_skill']]
            return sorted(set(skills))
        except Exception as e:
            logger.error(f"Error getting valid skills: {e}")
            return []
    
    def get_valid_priorities(self) -> List[str]:
        """Get all valid priority values from existing dispatches."""
        try:
            result = self.db.query("SELECT DISTINCT Priority FROM current_dispatches WHERE Priority IS NOT NULL ORDER BY Priority")
            priorities = [row['Priority'] for row in result if row['Priority']]
            return sorted(set(priorities))
        except Exception as e:
            logger.error(f"Error getting valid priorities: {e}")
            return []
    
    def get_valid_dispatch_reasons(self) -> List[str]:
        """Get valid dispatch reasons (column doesn't exist, returns empty list)."""
        logger.debug("Dispatch_reason column doesn't exist in schema, returning empty list")
        return []
    
    def get_valid_addresses(self) -> List[Dict[str, Any]]:
        """Get all valid addresses from existing dispatches."""
        try:
            result = self.db.query("""
                SELECT DISTINCT Street, City, State, Customer_latitude, Customer_longitude
                FROM current_dispatches
                WHERE Street IS NOT NULL
                ORDER BY State, City, Street
            """)
            return [{
                "address": row.get('Street', ''),
                "city": row.get('City', ''),
                "state": row.get('State', ''),
                "latitude": float(row.get('Customer_latitude') or 0.0),
                "longitude": float(row.get('Customer_longitude') or 0.0)
            } for row in result]
        except Exception as e:
            logger.error(f"Error getting valid addresses: {e}")
            return []
    
    def get_addresses_by_location(self, city: Optional[str] = None, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get addresses filtered by city and/or state."""
        try:
            sql = """
                SELECT DISTINCT Street, City, State, Customer_latitude, Customer_longitude
                FROM current_dispatches
                WHERE Street IS NOT NULL
            """
            params = []
            
            if city:
                sql += " AND City = ?"
                params.append(city)
            if state:
                sql += " AND State = ?"
                params.append(state)
            
            sql += " ORDER BY State, City, Street"
            
            result = self.db.query(sql, tuple(params) if params else None)
            return [{
                "address": row.get('Street', ''),
                "city": row.get('City', ''),
                "state": row.get('State', ''),
                "latitude": float(row.get('Customer_latitude') or 0.0),
                "longitude": float(row.get('Customer_longitude') or 0.0)
            } for row in result]
        except Exception as e:
            logger.error(f"Error getting addresses by location: {e}")
            return []
    
    def validate_address(self, address: str, city: str, state: str) -> Dict[str, Any]:
        """Validate that an address exists in the database."""
        try:
            result = self.db.query("""
                SELECT Street, City, State, Customer_latitude, Customer_longitude
                FROM current_dispatches
                WHERE Street = ? AND City = ? AND State = ?
                LIMIT 1
            """, (address, city, state))
            
            if result:
                row = result[0]
                return {
                    "valid": True,
                    "address": row.get('Street', ''),
                    "city": row.get('City', ''),
                    "state": row.get('State', ''),
                    "latitude": float(row.get('Customer_latitude') or 0.0),
                    "longitude": float(row.get('Customer_longitude') or 0.0)
                }
            else:
                return {
                    "valid": False,
                    "error": f"Address not found: {address}, {city}, {state}"
                }
        except Exception as e:
            logger.error(f"Error validating address: {e}")
            return {
                "valid": False,
                "error": f"Error validating address: {str(e)}"
            }
    
    def check_capacity_available(self, city: str, state: str, date: str, duration_min: int) -> Dict[str, Any]:
        """Check if there is sufficient capacity to add a dispatch."""
        capacity = self.get_city_capacity(city, state, date)
        
        # Handle both dict and list responses from get_city_capacity
        if isinstance(capacity, list):
            # Overview mode - find matching city/state
            matching = next((c for c in capacity if c.get('city') == city and c.get('state') == state), None)
            if not matching:
                return {
                    "available": False,
                    "capacity": {},
                    "message": f"City/state combination not found: {city}, {state}"
                }
            capacity = matching
        
        available_min = capacity.get("available_capacity_min", 0)
        
        if available_min >= duration_min:
            return {
                "available": True,
                "capacity": capacity,
                "message": f"Sufficient capacity available ({available_min} min available, {duration_min} min needed)"
            }
        else:
            shortage = duration_min - available_min
            return {
                "available": False,
                "capacity": capacity,
                "shortage_min": shortage,
                "shortage_hrs": round(shortage / 60, 1),
                "message": f"Insufficient capacity (need {duration_min} min, only {available_min} min available, shortage: {shortage} min)"
            }
    
    def create_dispatch(self,
                       customer_address: str,
                       city: str,
                       state: str,
                       appointment_datetime: datetime,
                       duration_min: int,
                       required_skill: str,
                       priority: str,
                       dispatch_reason: str,
                       auto_assign: bool = False,
                       commit_to_db: bool = False) -> Dict[str, Any]:
        """Create a new dispatch with full validation."""
        from datetime import date
        
        # Validation 1: Check date is in future
        if isinstance(appointment_datetime, str):
            appointment_datetime = datetime.fromisoformat(appointment_datetime)
        
        if appointment_datetime.date() <= date.today():
            error_msg = f"Appointment date must be in the future (got: {appointment_datetime.date()})"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Validation 2: Validate address exists
        address_result = self.validate_address(customer_address, city, state)
        if not address_result["valid"]:
            logger.error(address_result["error"])
            return {"success": False, "error": address_result["error"]}
        
        # Validation 3: Validate skill exists
        valid_skills = self.get_valid_skills()
        if required_skill not in valid_skills:
            error_msg = f"Invalid skill: {required_skill}. Valid skills: {valid_skills}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Validation 4: Validate priority exists
        valid_priorities = self.get_valid_priorities()
        if priority not in valid_priorities:
            error_msg = f"Invalid priority: {priority}. Valid priorities: {valid_priorities}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Validation 5: Check city capacity
        date_str = str(appointment_datetime.date())
        capacity_check = self.check_capacity_available(city, state, date_str, duration_min)
        
        if not capacity_check["available"]:
            capacity = capacity_check["capacity"]
            error_msg = (f"Insufficient capacity in {city}, {state} on {date_str}:\n"
                        f"  Available: {capacity.get('available_capacity_min', 0) / 60:.1f} hrs\n"
                        f"  This dispatch needs: {duration_min / 60:.1f} hrs\n"
                        f"  Shortage: {capacity_check.get('shortage_hrs', 0)} hrs")
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "capacity": capacity
            }
        
        # Create new dispatch object
        new_dispatch = NewDispatch(
            customer_address=address_result["address"],
            city=address_result["city"],
            state=address_result["state"],
            customer_latitude=address_result["latitude"],
            customer_longitude=address_result["longitude"],
            appointment_start_datetime=appointment_datetime,
            duration_min=duration_min,
            required_skill=required_skill,
            priority=priority,
            dispatch_reason=dispatch_reason,
            dispatch_id=self._next_dispatch_id
        )
        
        logger.info(f"Created dispatch with ID: {new_dispatch.dispatch_id}")
        
        # Auto-assign if requested (simplified - would need full implementation)
        if auto_assign:
            logger.warning("Auto-assign not fully implemented in local mode")
            # TODO: Implement auto-assignment logic
        
        # Add to pending list
        self._pending_dispatches.append(new_dispatch)
        
        # Commit to database if requested
        if commit_to_db:
            commit_result = self.commit_pending_dispatches()
            if not commit_result["success"]:
                return commit_result
        
        # Increment dispatch ID for next dispatch
        self._next_dispatch_id += 1
        
        return {
            "success": True,
            "dispatch": new_dispatch.to_dict(),
            "assigned": new_dispatch.assigned_technician_id is not None,
            "committed": commit_to_db
        }
    
    def close(self):
        """Close database connection."""
        self.db.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def check_technician_assignments(self, tech_id: str, date: Optional[str] = None) -> Dict[str, Any]:
        """Check technician's current assignments and workload."""
        try:
            sql = """
                SELECT d.* 
                FROM current_dispatches d
                WHERE d.Assigned_technician_id = ?
            """
            params = [tech_id]
            
            if date:
                sql += " AND DATE(d.Appointment_start_datetime) = ?"
                params.append(date)
            
            sql += " ORDER BY d.Appointment_start_datetime"
            
            assignments = self.db.query(sql, tuple(params))
            
            # Get technician info
            tech_info = self._get_technician_data_cached(tech_id)
            if not tech_info:
                return {
                    'tech_id': tech_id,
                    'assignments': [],
                    'total_assignments': 0,
                    'utilization_pct': 0.0
                }
            
            return {
                'tech_id': tech_id,
                'name': tech_info.name,
                'assignments': assignments or [],
                'total_assignments': len(assignments) if assignments else 0,
                'utilization_pct': tech_info.utilization_pct
            }
        except Exception as e:
            logger.error(f"Error checking technician assignments: {e}")
            return {
                'tech_id': tech_id,
                'assignments': [],
                'total_assignments': 0,
                'utilization_pct': 0.0,
                'error': str(e)
            }
    
    def find_available_technicians(self, dispatch_id: str, enable_range_expansion: bool = True) -> Optional[List[Dict[str, Any]]]:
        """
        Find available technicians for a dispatch.
        
        Args:
            dispatch_id: Dispatch ID
            enable_range_expansion: Whether to expand search range if better match found
        
        Returns:
            List of available technicians with scores, distances, etc.
        """
        try:
            # Get dispatch info
            dispatch_result = self.db.query(
                "SELECT * FROM current_dispatches WHERE Dispatch_id = ?",
                (dispatch_id,)
            )
            
            if not dispatch_result:
                logger.warning(f"Dispatch {dispatch_id} not found")
                return None
            
            dispatch = dispatch_result[0]
            dispatch_date = str(dispatch.get("Appointment_start_datetime", ""))[:10] if dispatch.get("Appointment_start_datetime") else None
            required_skill = dispatch.get("Required_skill", "")
            dispatch_city = dispatch.get("City", "")
            dispatch_state = dispatch.get("State", "")
            dispatch_lat = float(dispatch.get("Customer_latitude", 0)) if dispatch.get("Customer_latitude") else 0.0
            dispatch_lon = float(dispatch.get("Customer_longitude", 0)) if dispatch.get("Customer_longitude") else 0.0
            
            if not dispatch_date:
                logger.warning(f"Dispatch {dispatch_id} has no appointment date")
                return None
            
            # Find technicians in same city/state with matching skill
            sql = """
                SELECT t.*, c.Available, c.Start_time, c.End_time, c.Max_assignments
                FROM technicians t
                JOIN technician_calendar c ON t.Technician_id = c.Technician_id
                WHERE c.Date = ? 
                AND c.Available = 1
                AND t.City = ?
                AND t.State = ?
            """
            params = [dispatch_date, dispatch_city, dispatch_state]
            
            if required_skill:
                sql += " AND t.Primary_skill = ?"
                params.append(required_skill)
            
            techs = self.db.query(sql, tuple(params))
            
            if not techs:
                return []
            
            # Calculate distance and score for each technician
            available_techs = []
            for tech in techs:
                tech_lat = float(tech.get("Latitude", 0)) if tech.get("Latitude") else 0.0
                tech_lon = float(tech.get("Longitude", 0)) if tech.get("Longitude") else 0.0
                
                if tech_lat == 0.0 or tech_lon == 0.0 or dispatch_lat == 0.0 or dispatch_lon == 0.0:
                    continue
                
                # Calculate distance
                from math import radians, sin, cos, asin, sqrt
                lat1, lon1 = radians(tech_lat), radians(tech_lon)
                lat2, lon2 = radians(dispatch_lat), radians(dispatch_lon)
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                distance_km = EARTH_RADIUS_KM * c
                
                # Check if within range
                if distance_km > self.max_range_km:
                    if not enable_range_expansion:
                        continue
                    # Could implement range expansion logic here
                
                # Calculate travel time
                travel_time_min = distance_km * MINUTES_PER_KM + TRAVEL_BUFFER_MINUTES
                
                # Get assigned minutes for utilization
                assigned_minutes = self._get_assigned_minutes(tech["Technician_id"], dispatch_date)
                max_assignments_minutes = int(tech.get("Max_assignments", 0)) * MINUTES_PER_HOUR if tech.get("Max_assignments") else 0
                utilization_pct = (assigned_minutes / max_assignments_minutes * 100) if max_assignments_minutes > 0 else 0.0
                
                # Simple scoring (can be enhanced)
                score = 100.0 - (distance_km * 2) - (utilization_pct * 0.5)
                
                available_techs.append({
                    "Technician_id": tech["Technician_id"],
                    "Name": tech.get("Name", ""),
                    "Distance_km": round(distance_km, 2),
                    "Travel_time_min": round(travel_time_min, 1),
                    "Score": round(score, 2),
                    "Utilization_pct": round(utilization_pct, 1)
                })
            
            # Sort by score (highest first)
            available_techs.sort(key=lambda x: x["Score"], reverse=True)
            return available_techs
            
        except Exception as e:
            logger.error(f"Error finding available technicians: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def find_available_dispatches(self, tech_id: str, date: str) -> Optional[pd.DataFrame]:
        """Find available dispatches for a technician."""
        try:
            # Get technician info
            tech_info = self._get_technician_data_cached(tech_id)
            if not tech_info:
                logger.warning(f"Technician {tech_id} not found")
                return None
            
            # Get technician calendar for date
            cal_result = self.db.query(
                "SELECT * FROM technician_calendar WHERE Technician_id = ? AND Date = ?",
                (tech_id, date)
            )
            
            if not cal_result or cal_result[0].get("Available", 0) == 0:
                logger.info(f"Technician {tech_id} not available on {date}")
                return pd.DataFrame()
            
            cal = cal_result[0]
            
            # Find unassigned dispatches in same city/state
            sql = """
                SELECT * FROM current_dispatches
                WHERE (Assigned_technician_id IS NULL OR Assigned_technician_id = '')
                AND City = ?
                AND State = ?
                AND DATE(Appointment_start_datetime) = ?
            """
            
            dispatches = self.db.query(sql, (tech_info.location.city, tech_info.location.state, date))
            
            if not dispatches:
                return pd.DataFrame()
            
            # Filter by skill match and distance
            available_dispatches = []
            for dispatch in dispatches:
                # Check skill match
                required_skill = dispatch.get("Required_skill", "")
                if required_skill and tech_info.primary_skill != required_skill:
                    continue
                
                # Check distance
                dispatch_lat = float(dispatch.get("Customer_latitude", 0)) if dispatch.get("Customer_latitude") else 0.0
                dispatch_lon = float(dispatch.get("Customer_longitude", 0)) if dispatch.get("Customer_longitude") else 0.0
                
                if dispatch_lat == 0.0 or dispatch_lon == 0.0:
                    continue
                
                dispatch_location = Location(
                    city=dispatch.get("City", ""),
                    state=dispatch.get("State", ""),
                    latitude=dispatch_lat,
                    longitude=dispatch_lon
                )
                
                distance_km = tech_info.location.distance_to(dispatch_location)
                if distance_km > self.max_range_km:
                    continue
                
                available_dispatches.append(dispatch)
            
            if not available_dispatches:
                return pd.DataFrame()
            
            return pd.DataFrame(available_dispatches)
            
        except Exception as e:
            logger.error(f"Error finding available dispatches: {e}")
            return None
    
    def list_available_technicians(self, date: str, city: Optional[str] = None, 
                                  state: Optional[str] = None) -> Optional[pd.DataFrame]:
        """List all available technicians for a date."""
        try:
            sql = """
                SELECT 
                    t.Technician_id,
                    t.Name,
                    t.City,
                    t.State,
                    t.Primary_skill,
                    c.Start_time,
                    c.End_time,
                    c.Max_assignments
                FROM technicians t
                JOIN technician_calendar c ON t.Technician_id = c.Technician_id
                WHERE c.Date = ? AND c.Available = 1
            """
            params = [date]
            
            if city:
                sql += " AND t.City = ?"
                params.append(city)
            if state:
                sql += " AND t.State = ?"
                params.append(state)
            
            sql += " ORDER BY t.Name"
            
            techs = self.db.query(sql, tuple(params))
            
            if not techs:
                return pd.DataFrame()
            
            # Add utilization info
            for tech in techs:
                tech_id = tech["Technician_id"]
                assigned_minutes = self._get_assigned_minutes(tech_id, date)
                max_minutes = int(tech.get("Max_assignments", 0)) * MINUTES_PER_HOUR if tech.get("Max_assignments") else 0
                tech["Assigned_minutes"] = assigned_minutes
                tech["Available_minutes"] = max_minutes
                tech["Remaining_minutes"] = max_minutes - assigned_minutes
                tech["Utilization_pct"] = (assigned_minutes / max_minutes * 100) if max_minutes > 0 else 0.0
            
            return pd.DataFrame(techs)
            
        except Exception as e:
            logger.error(f"Error listing available technicians: {e}")
            return None
    
    def get_technician_availability_summary(self, start_date: str, end_date: str,
                                            city: Optional[str] = None,
                                            state: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get technician availability summary across a date range."""
        try:
            sql = """
                SELECT 
                    t.Technician_id,
                    t.Name,
                    t.City,
                    t.State,
                    t.Primary_skill,
                    c.Date,
                    c.Start_time,
                    c.End_time,
                    c.Max_assignments
                FROM technicians t
                JOIN technician_calendar c ON t.Technician_id = c.Technician_id
                WHERE c.Date >= ? AND c.Date <= ? AND c.Available = 1
            """
            params = [start_date, end_date]
            
            if city:
                sql += " AND t.City = ?"
                params.append(city)
            if state:
                sql += " AND t.State = ?"
                params.append(state)
            
            sql += " ORDER BY c.Date, t.Name"
            
            results = self.db.query(sql, tuple(params))
            
            if not results:
                return pd.DataFrame()
            
            return pd.DataFrame(results)
            
        except Exception as e:
            logger.error(f"Error getting availability summary: {e}")
            return None
    
    def auto_assign_dispatches(self, date: str, dry_run: bool = True,
                               use_scoring: bool = True,
                               enable_range_expansion: bool = True,
                               state: Optional[str] = None,
                               city: Optional[str] = None) -> Dict[str, Any]:
        """
        Auto-assign dispatches to technicians.
        
        This is a simplified version - full implementation would include
        more sophisticated scoring and assignment logic.
        """
        try:
            # Get unassigned dispatches
            dispatches = self.get_unassigned_dispatches(limit=1000, city=city, state=state, date=date)
            
            if not dispatches:
                return {
                    'total': 0,
                    'assigned': 0,
                    'unassigned': 0,
                    'assignments': [],
                    'unassignable': [],
                    'success_rate': 0.0,
                    'avg_score': 0.0,
                    'total_travel_time': 0.0
                }
            
            assignments = []
            unassignable = []
            total_travel_time = 0.0
            
            for dispatch in dispatches:
                dispatch_id = dispatch.get("Dispatch_id")
                if not dispatch_id:
                    continue
                
                available = self.find_available_technicians(dispatch_id, enable_range_expansion=enable_range_expansion)
                
                if available and len(available) > 0:
                    if use_scoring:
                        best = max(available, key=lambda t: t.get("Score", 0))
                    else:
                        best = min(available, key=lambda t: t.get("Distance_km", float('inf')))
                    
                    assignments.append({
                        "Dispatch_id": dispatch_id,
                        "Technician_id": best["Technician_id"],
                        "Technician_name": best.get("Name", ""),
                        "Distance_km": best.get("Distance_km", 0),
                        "Travel_time_min": best.get("Travel_time_min", 0),
                        "Score": best.get("Score", 0),
                        "Priority": str(dispatch.get("Priority", "Medium"))
                    })
                    total_travel_time += best.get("Travel_time_min", 0)
                else:
                    unassignable.append({
                        "Dispatch_id": dispatch_id,
                        "Reason": "No available technicians"
                    })
            
            success_rate = (len(assignments) / len(dispatches) * 100) if dispatches else 0.0
            avg_score = (sum(a.get("Score", 0) for a in assignments) / len(assignments)) if assignments else 0.0
            
            return {
                'total': len(dispatches),
                'assigned': len(assignments),
                'unassigned': len(unassignable),
                'assignments': assignments,
                'unassignable': unassignable,
                'success_rate': round(success_rate, 1),
                'avg_score': round(avg_score, 1),
                'total_travel_time': round(total_travel_time, 1)
            }
            
        except Exception as e:
            logger.error(f"Error in auto_assign_dispatches: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'total': 0,
                'assigned': 0,
                'unassigned': 0,
                'assignments': [],
                'unassignable': [],
                'success_rate': 0.0,
                'avg_score': 0.0,
                'total_travel_time': 0.0,
                'error': str(e)
            }


# Note: This is a simplified version. For full functionality, you would need
# to port all methods from SmartDispatchAI to use SQLite queries instead of Spark.
# The key methods above demonstrate the pattern.


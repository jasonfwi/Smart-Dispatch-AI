"""
Utility functions and helpers for Smart Dispatch AI.

This module provides shared utilities, query builders, and validation functions
to reduce code duplication and improve maintainability.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# Query limits
DEFAULT_SEARCH_LIMIT = 500
MAX_SEARCH_LIMIT = 5000
AUTOCOMPLETE_LIMIT = 1000

# Date formats
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# Valid enum values
VALID_PRIORITIES = ['Critical', 'High', 'Medium', 'Low']
VALID_STATUSES = ['Pending', 'In Progress', 'Completed', 'Cancelled']
VALID_ASSIGNMENT_STATUSES = ['unassigned', 'assigned']


# ============================================================================
# QUERY BUILDERS
# ============================================================================

class DispatchQueryBuilder:
    """Builder for dispatch search queries to reduce code duplication."""
    
    def __init__(self):
        self.sql = "SELECT * FROM current_dispatches WHERE 1=1"
        self.params: List[Any] = []
    
    def filter_by_id(self, dispatch_id: Optional[str]) -> 'DispatchQueryBuilder':
        """Filter by dispatch ID."""
        if dispatch_id:
            self.sql += " AND Dispatch_id = ?"
            self.params.append(dispatch_id)
        return self
    
    def filter_by_status(self, status: Optional[str]) -> 'DispatchQueryBuilder':
        """Filter by status."""
        if status:
            self.sql += " AND Status = ?"
            self.params.append(status)
        return self
    
    def filter_by_assignment_status(self, assignment_status: Optional[str]) -> 'DispatchQueryBuilder':
        """Filter by assignment status (unassigned/assigned)."""
        if assignment_status == 'unassigned':
            self.sql += " AND (Assigned_technician_id IS NULL OR Assigned_technician_id = '')"
        elif assignment_status == 'assigned':
            self.sql += " AND Assigned_technician_id IS NOT NULL AND Assigned_technician_id != ''"
        return self
    
    def filter_by_priority(self, priority: Optional[str]) -> 'DispatchQueryBuilder':
        """Filter by priority."""
        if priority:
            self.sql += " AND Priority = ?"
            self.params.append(priority)
        return self
    
    def filter_by_date_range(self, start_date: Optional[str], end_date: Optional[str]) -> 'DispatchQueryBuilder':
        """Filter by date range."""
        if start_date and end_date:
            self.sql += " AND DATE(Appointment_start_datetime) BETWEEN ? AND ?"
            self.params.extend([start_date, end_date])
        elif start_date:
            self.sql += " AND DATE(Appointment_start_datetime) >= ?"
            self.params.append(start_date)
        elif end_date:
            self.sql += " AND DATE(Appointment_start_datetime) <= ?"
            self.params.append(end_date)
        return self
    
    def filter_by_location(self, city: Optional[str], state: Optional[str]) -> 'DispatchQueryBuilder':
        """Filter by city and/or state."""
        if state:
            self.sql += " AND State = ?"
            self.params.append(state)
        if city:
            self.sql += " AND City = ?"
            self.params.append(city)
        return self
    
    def filter_by_skill(self, skill: Optional[str]) -> 'DispatchQueryBuilder':
        """Filter by required skill."""
        if skill:
            self.sql += " AND Required_skill = ?"
            self.params.append(skill)
        return self
    
    def order_by_priority_and_date(self) -> 'DispatchQueryBuilder':
        """Order by priority (desc) and appointment datetime (asc)."""
        self.sql += " ORDER BY Priority DESC, Appointment_start_datetime ASC"
        return self
    
    def limit(self, limit: int = DEFAULT_SEARCH_LIMIT) -> 'DispatchQueryBuilder':
        """Add LIMIT clause."""
        limit = min(max(1, limit), MAX_SEARCH_LIMIT)  # Clamp between 1 and MAX
        self.sql += " LIMIT ?"
        self.params.append(limit)
        return self
    
    def build(self) -> Tuple[str, Optional[Tuple]]:
        """Build the final query and parameters."""
        return self.sql, tuple(self.params) if self.params else None


def build_dispatch_search_query(
    dispatch_id: Optional[str] = None,
    status: Optional[str] = None,
    assignment_status: Optional[str] = None,
    priority: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    skill: Optional[str] = None,
    limit: int = DEFAULT_SEARCH_LIMIT
) -> Tuple[str, Optional[Tuple]]:
    """
    Build a dispatch search query using the builder pattern.
    
    Returns:
        Tuple of (SQL query string, parameters tuple or None)
    """
    builder = DispatchQueryBuilder()
    builder.filter_by_id(dispatch_id) \
           .filter_by_status(status) \
           .filter_by_assignment_status(assignment_status) \
           .filter_by_priority(priority) \
           .filter_by_date_range(start_date, end_date) \
           .filter_by_location(city, state) \
           .filter_by_skill(skill) \
           .order_by_priority_and_date() \
           .limit(limit)
    
    return builder.build()


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_priority(priority: str) -> bool:
    """Validate priority value."""
    return priority in VALID_PRIORITIES


def validate_status(status: str) -> bool:
    """Validate status value."""
    return status in VALID_STATUSES


def validate_date_format(date_str: str) -> bool:
    """Validate date string format."""
    try:
        datetime.strptime(date_str, DATE_FORMAT)
        return True
    except (ValueError, TypeError):
        return False


def validate_limit(limit: Any, default: int = DEFAULT_SEARCH_LIMIT, max_limit: int = MAX_SEARCH_LIMIT) -> int:
    """Validate and clamp limit value."""
    try:
        limit_int = int(limit)
        return min(max(1, limit_int), max_limit)
    except (ValueError, TypeError):
        return default


def sanitize_string(value: Any, max_length: Optional[int] = None) -> Optional[str]:
    """Sanitize string input."""
    if value is None:
        return None
    
    str_value = str(value).strip()
    if not str_value:
        return None
    
    if max_length:
        str_value = str_value[:max_length]
    
    return str_value


# ============================================================================
# RESPONSE BUILDERS
# ============================================================================

def success_response(data: Any = None, **kwargs) -> Dict[str, Any]:
    """Build a standard success response."""
    response = {'success': True}
    if data is not None:
        response['data'] = data
    response.update(kwargs)
    return response


def error_response(error: str, status_code: int = 400, **kwargs) -> Tuple[Dict[str, Any], int]:
    """Build a standard error response."""
    response = {
        'success': False,
        'error': error
    }
    response.update(kwargs)
    return response, status_code


# ============================================================================
# DATA TRANSFORMATION
# ============================================================================

def normalize_date(date_input: Any) -> Optional[str]:
    """Normalize date input to YYYY-MM-DD format."""
    if date_input is None:
        return None
    
    if isinstance(date_input, datetime):
        return date_input.strftime(DATE_FORMAT)
    
    if isinstance(date_input, str):
        # Try to parse and normalize
        try:
            dt = datetime.strptime(date_input, DATE_FORMAT)
            return dt.strftime(DATE_FORMAT)
        except ValueError:
            # Try other common formats
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y']:
                try:
                    dt = datetime.strptime(date_input, fmt)
                    return dt.strftime(DATE_FORMAT)
                except ValueError:
                    continue
    
    return None


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int with default."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float with default."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# ============================================================================
# CACHE HELPERS
# ============================================================================

def make_cache_key(prefix: str, **kwargs) -> str:
    """Create a cache key from prefix and keyword arguments."""
    parts = [prefix]
    for key, value in sorted(kwargs.items()):
        if value is not None:
            parts.append(f"{key}:{value}")
    return "|".join(parts)


# ============================================================================
# DISTANCE CALCULATIONS
# ============================================================================

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
    
    Returns:
        Distance in kilometers
    """
    from math import radians, sin, cos, asin, sqrt
    from constants import EARTH_RADIUS_KM
    
    if lat1 == 0.0 or lon1 == 0.0 or lat2 == 0.0 or lon2 == 0.0:
        return float('inf')  # Invalid coordinates
    
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    return EARTH_RADIUS_KM * c


def calculate_travel_time_min(distance_km: float) -> float:
    """
    Calculate travel time in minutes based on distance.
    
    Args:
        distance_km: Distance in kilometers
    
    Returns:
        Travel time in minutes (including buffer)
    """
    from constants import MINUTES_PER_KM, TRAVEL_BUFFER_MINUTES
    
    if distance_km == float('inf'):
        return float('inf')
    
    return distance_km * MINUTES_PER_KM + TRAVEL_BUFFER_MINUTES


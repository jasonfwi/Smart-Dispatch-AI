"""
Smart Dispatch AI - Constants and Data Models

Shared constants, dataclasses, and utility functions used across the application.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from math import radians, sin, cos, asin, sqrt
from datetime import datetime


# ============================================================
# CONSTANTS & CONFIGURATION
# ============================================================

EARTH_RADIUS_KM = 6371.0
DEFAULT_MAX_RANGE_KM = 15.0
MINUTES_PER_HOUR = 60

# Travel time estimation
AVERAGE_SPEED_KMH = 40.0  # Average urban driving speed
TRAVEL_BUFFER_MINUTES = 15  # Buffer time between appointments
MINUTES_PER_KM = 60.0 / AVERAGE_SPEED_KMH  # ~1.5 min/km at 40 km/h

# Range expansion for smart technician search
RANGE_EXPANSION_FACTOR = 1.5  # Expand range by 50% if better match found
RANGE_EXPANSION_THRESHOLD = 0.2  # 20% better rating threshold

# Scoring weights for technician assignment
SCORING_WEIGHTS = {
    'priority': 0.25,
    'skill_match': 0.20,
    'utilization': 0.15,
    'history': 0.15,
    'distance': 0.15,
    'travel_time': 0.10
}


# ============================================================
# DATA MODELS
# ============================================================

class Status(Enum):
    """Dispatch status types."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Location:
    """Immutable location with distance calculation."""
    city: str
    state: str
    latitude: float
    longitude: float
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance to another location using Haversine formula."""
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return EARTH_RADIUS_KM * c


@dataclass
class TechnicianInfo:
    """Technician information container."""
    technician_id: str
    name: str
    location: Location
    primary_skill: str
    current_assignments: int
    workload_capacity: int
    
    @property
    def utilization_pct(self) -> float:
        """Calculate utilization percentage."""
        return (self.current_assignments / self.workload_capacity * 100 
                if self.workload_capacity > 0 else 0)


@dataclass
class AvailabilityInfo:
    """Technician availability information."""
    available: bool
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    available_minutes: Optional[int] = None
    assigned_minutes: Optional[int] = None
    remaining_minutes: Optional[int] = None
    reason: Optional[str] = None
    
    @property
    def utilization_pct(self) -> float:
        """Calculate utilization percentage."""
        if not self.available or not self.available_minutes:
            return 0.0
        return (self.assigned_minutes / self.available_minutes * 100 
                if self.assigned_minutes else 0.0)


@dataclass
class RangeCheckResult:
    """Range check result container."""
    in_range: bool
    distance_km: Optional[float] = None
    reason: Optional[str] = None


@dataclass
class Assignment:
    """Assignment recommendation container."""
    dispatch_id: str
    technician_id: str
    technician_name: str
    distance_km: float
    travel_time_min: float
    score: float
    priority: str = "Medium"


@dataclass
class NewDispatch:
    """New dispatch creation container."""
    customer_address: str
    city: str
    state: str
    customer_latitude: float
    customer_longitude: float
    appointment_start_datetime: datetime
    duration_min: int
    required_skill: str
    priority: str
    dispatch_reason: str
    dispatch_id: Optional[str] = None
    assigned_technician_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'dispatch_id': self.dispatch_id,
            'customer_address': self.customer_address,
            'city': self.city,
            'state': self.state,
            'customer_latitude': self.customer_latitude,
            'customer_longitude': self.customer_longitude,
            'appointment_start_datetime': self.appointment_start_datetime.isoformat(),
            'duration_min': self.duration_min,
            'required_skill': self.required_skill,
            'priority': self.priority,
            'dispatch_reason': self.dispatch_reason,
            'assigned_technician_id': self.assigned_technician_id
        }


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def round_minutes_to_nearest_hour(minutes: int) -> int:
    """
    Round duration in minutes to the nearest hour.
    
    Args:
        minutes: Duration in minutes
        
    Returns:
        Rounded duration in minutes (to nearest hour)
    """
    if minutes <= 0:
        return 0
    
    # Round to nearest hour (60 minutes)
    rounded = round(minutes / 60) * 60
    return int(rounded)


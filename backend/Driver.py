"""
Driver.py - Driver entity for ride-sharing system.

This module defines the Driver class with:
- Location tracking
- Availability status management
- Utilization metrics
"""

from typing import Optional
from enum import Enum
import copy


class DriverStatus(Enum):
    """Driver availability status."""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class Driver:
    """
    Represents a driver in the ride-sharing system.
    
    Attributes:
        driver_id: Unique identifier
        name: Driver's name
        current_location: Current node ID in the city graph
        zone: Current zone the driver is in
        status: Availability status
        total_trips: Number of completed trips
        total_distance: Total distance traveled
        active_time: Total time driver has been active (for utilization)
    """
    
    def __init__(
        self,
        driver_id: str,
        name: str,
        current_location: str,
        zone: str
    ):
        self.driver_id = driver_id
        self.name = name
        self.current_location = current_location
        self.zone = zone
        self.status = DriverStatus.AVAILABLE
        
        # Utilization tracking
        self.total_trips = 0
        self.total_distance = 0.0
        self.active_time = 0.0  # Minutes spent on trips
        self.idle_time = 0.0    # Minutes spent waiting
        
        # Current assignment
        self.current_trip_id: Optional[str] = None
    
    def is_available(self) -> bool:
        """Check if driver is available for new assignments."""
        return self.status == DriverStatus.AVAILABLE
    
    def assign_trip(self, trip_id: str) -> None:
        """
        Assign a trip to this driver.
        
        Args:
            trip_id: ID of the trip being assigned
        """
        if not self.is_available():
            raise ValueError(f"Driver {self.driver_id} is not available")
        
        self.status = DriverStatus.BUSY
        self.current_trip_id = trip_id
    
    def complete_trip(self, distance: float, duration: float) -> None:
        """
        Mark the current trip as completed.
        
        Args:
            distance: Distance traveled in this trip
            duration: Time spent on this trip (minutes)
        """
        self.status = DriverStatus.AVAILABLE
        self.current_trip_id = None
        self.total_trips += 1
        self.total_distance += distance
        self.active_time += duration
    
    def cancel_current_trip(self) -> None:
        """Cancel the current assigned trip and become available."""
        self.status = DriverStatus.AVAILABLE
        self.current_trip_id = None
    
    def update_location(self, new_location: str, new_zone: str) -> None:
        """
        Update the driver's current location and zone.
        
        Args:
            new_location: New node ID
            new_zone: New zone name
        """
        self.current_location = new_location
        self.zone = new_zone
    
    def go_offline(self) -> None:
        """Set driver status to offline."""
        if self.current_trip_id is not None:
            raise ValueError("Cannot go offline while on a trip")
        self.status = DriverStatus.OFFLINE
    
    def go_online(self) -> None:
        """Set driver status to available."""
        self.status = DriverStatus.AVAILABLE
    
    def get_utilization_rate(self) -> float:
        """
        Calculate driver utilization rate.
        
        Returns:
            Ratio of active time to total time (active + idle), 0-1
        """
        total_time = self.active_time + self.idle_time
        if total_time == 0:
            return 0.0
        return self.active_time / total_time
    
    def add_idle_time(self, minutes: float) -> None:
        """Add idle time to the driver's record."""
        self.idle_time += minutes
    
    def create_snapshot(self) -> 'DriverSnapshot':
        """
        Create a snapshot of the current driver state for rollback purposes.
        
        Returns:
            DriverSnapshot object containing current state
        """
        return DriverSnapshot(
            driver_id=self.driver_id,
            name=self.name,
            current_location=self.current_location,
            zone=self.zone,
            status=self.status,
            total_trips=self.total_trips,
            total_distance=self.total_distance,
            active_time=self.active_time,
            idle_time=self.idle_time,
            current_trip_id=self.current_trip_id
        )
    
    def restore_from_snapshot(self, snapshot: 'DriverSnapshot') -> None:
        """
        Restore driver state from a snapshot.
        
        Args:
            snapshot: DriverSnapshot to restore from
        """
        self.name = snapshot.name
        self.current_location = snapshot.current_location
        self.zone = snapshot.zone
        self.status = snapshot.status
        self.total_trips = snapshot.total_trips
        self.total_distance = snapshot.total_distance
        self.active_time = snapshot.active_time
        self.idle_time = snapshot.idle_time
        self.current_trip_id = snapshot.current_trip_id
    
    def to_dict(self) -> dict:
        """Convert driver to dictionary for serialization."""
        return {
            "driver_id": self.driver_id,
            "name": self.name,
            "current_location": self.current_location,
            "zone": self.zone,
            "status": self.status.value,
            "total_trips": self.total_trips,
            "total_distance": self.total_distance,
            "active_time": self.active_time,
            "idle_time": self.idle_time,
            "current_trip_id": self.current_trip_id,
            "utilization_rate": self.get_utilization_rate()
        }


class DriverSnapshot:
    """
    Immutable snapshot of driver state for rollback purposes.
    """
    
    def __init__(
        self,
        driver_id: str,
        name: str,
        current_location: str,
        zone: str,
        status: DriverStatus,
        total_trips: int,
        total_distance: float,
        active_time: float,
        idle_time: float,
        current_trip_id: Optional[str]
    ):
        self.driver_id = driver_id
        self.name = name
        self.current_location = current_location
        self.zone = zone
        self.status = status
        self.total_trips = total_trips
        self.total_distance = total_distance
        self.active_time = active_time
        self.idle_time = idle_time
        self.current_trip_id = current_trip_id

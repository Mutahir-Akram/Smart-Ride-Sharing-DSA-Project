"""
Rider.py - Rider entity for ride-sharing system.

This module defines the Rider class with:
- Pickup and drop-off location management
- Trip history tracking
"""

from typing import Optional, List


class Rider:
    """
    Represents a rider/customer in the ride-sharing system.
    
    Attributes:
        rider_id: Unique identifier
        name: Rider's name
        current_location: Current/pickup node ID
        trip_history: List of trip IDs this rider has taken
    """
    
    def __init__(
        self,
        rider_id: str,
        name: str,
        current_location: str
    ):
        self.rider_id = rider_id
        self.name = name
        self.current_location = current_location
        
        # Trip tracking
        self.trip_history: List[str] = []
        self.current_trip_id: Optional[str] = None
        self.total_trips = 0
        self.total_distance = 0.0
        self.total_spent = 0.0  # Total amount spent on rides
    
    def request_trip(self, trip_id: str) -> None:
        """
        Register that this rider has requested a trip.
        
        Args:
            trip_id: ID of the requested trip
        """
        if self.current_trip_id is not None:
            raise ValueError(f"Rider {self.rider_id} already has an active trip")
        self.current_trip_id = trip_id
    
    def complete_trip(self, trip_id: str, distance: float, cost: float) -> None:
        """
        Mark the current trip as completed.
        
        Args:
            trip_id: ID of the completed trip
            distance: Distance of the trip
            cost: Cost of the trip
        """
        self.trip_history.append(trip_id)
        self.current_trip_id = None
        self.total_trips += 1
        self.total_distance += distance
        self.total_spent += cost
    
    def cancel_trip(self) -> None:
        """Cancel the current active trip."""
        self.current_trip_id = None
    
    def update_location(self, new_location: str) -> None:
        """
        Update the rider's current location.
        
        Args:
            new_location: New node ID
        """
        self.current_location = new_location
    
    def has_active_trip(self) -> bool:
        """Check if rider has an active trip."""
        return self.current_trip_id is not None
    
    def create_snapshot(self) -> 'RiderSnapshot':
        """
        Create a snapshot of the current rider state for rollback purposes.
        
        Returns:
            RiderSnapshot object containing current state
        """
        return RiderSnapshot(
            rider_id=self.rider_id,
            name=self.name,
            current_location=self.current_location,
            trip_history=self.trip_history.copy(),
            current_trip_id=self.current_trip_id,
            total_trips=self.total_trips,
            total_distance=self.total_distance,
            total_spent=self.total_spent
        )
    
    def restore_from_snapshot(self, snapshot: 'RiderSnapshot') -> None:
        """
        Restore rider state from a snapshot.
        
        Args:
            snapshot: RiderSnapshot to restore from
        """
        self.name = snapshot.name
        self.current_location = snapshot.current_location
        self.trip_history = snapshot.trip_history.copy()
        self.current_trip_id = snapshot.current_trip_id
        self.total_trips = snapshot.total_trips
        self.total_distance = snapshot.total_distance
        self.total_spent = snapshot.total_spent
    
    def to_dict(self) -> dict:
        """Convert rider to dictionary for serialization."""
        return {
            "rider_id": self.rider_id,
            "name": self.name,
            "current_location": self.current_location,
            "trip_history": self.trip_history,
            "current_trip_id": self.current_trip_id,
            "total_trips": self.total_trips,
            "total_distance": self.total_distance,
            "total_spent": self.total_spent,
            "has_active_trip": self.has_active_trip()
        }


class RiderSnapshot:
    """
    Immutable snapshot of rider state for rollback purposes.
    """
    
    def __init__(
        self,
        rider_id: str,
        name: str,
        current_location: str,
        trip_history: List[str],
        current_trip_id: Optional[str],
        total_trips: int,
        total_distance: float,
        total_spent: float
    ):
        self.rider_id = rider_id
        self.name = name
        self.current_location = current_location
        self.trip_history = trip_history
        self.current_trip_id = current_trip_id
        self.total_trips = total_trips
        self.total_distance = total_distance
        self.total_spent = total_spent

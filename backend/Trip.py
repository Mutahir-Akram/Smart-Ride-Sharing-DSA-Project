"""
Trip.py - Trip entity with state machine for ride-sharing system.

This module defines the Trip class with:
- Strict state machine transitions
- Trip lifecycle management
- Distance and cost calculation
"""

from typing import Optional, List
from enum import Enum
from datetime import datetime


class TripState(Enum):
    """
    Trip states following the strict state machine:
    REQUESTED → ASSIGNED → ONGOING → COMPLETED
    REQUESTED → CANCELLED
    ASSIGNED → CANCELLED
    """
    REQUESTED = "requested"
    ASSIGNED = "assigned"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class Trip:
    """
    Represents a trip in the ride-sharing system.
    
    Implements a strict state machine with validated transitions.
    
    Attributes:
        trip_id: Unique identifier
        rider_id: ID of the rider who requested the trip
        driver_id: ID of the assigned driver (None if not assigned)
        pickup_location: Node ID for pickup
        dropoff_location: Node ID for drop-off
        state: Current trip state
        distance: Total trip distance
        cost: Total trip cost
        path: List of node IDs representing the route
    """
    
    # Valid state transitions: current_state -> list of valid next states
    VALID_TRANSITIONS = {
        TripState.REQUESTED: [TripState.ASSIGNED, TripState.CANCELLED],
        TripState.ASSIGNED: [TripState.ONGOING, TripState.CANCELLED],
        TripState.ONGOING: [TripState.COMPLETED],
        TripState.COMPLETED: [],  # Terminal state
        TripState.CANCELLED: [],  # Terminal state
    }
    
    # Base fare and per-km rate for cost calculation
    BASE_FARE = 5.0
    PER_KM_RATE = 2.0
    CROSS_ZONE_PENALTY = 1.5  # Multiplier for cross-zone trips
    
    def __init__(
        self,
        trip_id: str,
        rider_id: str,
        pickup_location: str,
        dropoff_location: str,
        pickup_zone: str,
        dropoff_zone: str
    ):
        self.trip_id = trip_id
        self.rider_id = rider_id
        self.driver_id: Optional[str] = None
        self.pickup_location = pickup_location
        self.dropoff_location = dropoff_location
        self.pickup_zone = pickup_zone
        self.dropoff_zone = dropoff_zone
        
        # State management
        self.state = TripState.REQUESTED
        self.state_history: List[tuple] = [(TripState.REQUESTED, datetime.now())]
        
        # Trip metrics
        self.distance: float = 0.0
        self.estimated_duration: float = 0.0  # Minutes
        self.actual_duration: float = 0.0  # Minutes
        self.cost: float = 0.0
        self.path: List[str] = []
        
        # Cross-zone flag
        self.is_cross_zone = pickup_zone != dropoff_zone
        
        # Timestamps
        self.created_at = datetime.now()
        self.assigned_at: Optional[datetime] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.cancelled_at: Optional[datetime] = None
    
    def can_transition_to(self, new_state: TripState) -> bool:
        """
        Check if transition to new_state is valid.
        
        Args:
            new_state: The state to transition to
        
        Returns:
            True if transition is valid, False otherwise
        """
        return new_state in self.VALID_TRANSITIONS.get(self.state, [])
    
    def _transition(self, new_state: TripState) -> None:
        """
        Internal method to perform state transition.
        
        Args:
            new_state: The state to transition to
        
        Raises:
            InvalidStateTransitionError: If transition is not valid
        """
        if not self.can_transition_to(new_state):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.state.value} to {new_state.value}"
            )
        
        self.state = new_state
        self.state_history.append((new_state, datetime.now()))
    
    def assign_driver(self, driver_id: str, distance: float, path: List[str]) -> None:
        """
        Assign a driver to this trip.
        
        Args:
            driver_id: ID of the driver to assign
            distance: Calculated trip distance
            path: List of node IDs for the route
        
        Raises:
            InvalidStateTransitionError: If trip is not in REQUESTED state
        """
        self._transition(TripState.ASSIGNED)
        
        self.driver_id = driver_id
        self.distance = distance
        self.path = path
        self.assigned_at = datetime.now()
        
        # Calculate estimated duration (assume 30 km/h average speed)
        self.estimated_duration = (distance / 30) * 60  # Minutes
        
        # Calculate cost
        self.cost = self._calculate_cost(distance)
    
    def start_trip(self) -> None:
        """
        Start the trip (driver picked up rider).
        
        Raises:
            InvalidStateTransitionError: If trip is not in ASSIGNED state
        """
        self._transition(TripState.ONGOING)
        self.started_at = datetime.now()
    
    def complete_trip(self, actual_duration: Optional[float] = None) -> None:
        """
        Complete the trip.
        
        Args:
            actual_duration: Actual trip duration in minutes (optional)
        
        Raises:
            InvalidStateTransitionError: If trip is not in ONGOING state
        """
        self._transition(TripState.COMPLETED)
        self.completed_at = datetime.now()
        
        if actual_duration is not None:
            self.actual_duration = actual_duration
        else:
            self.actual_duration = self.estimated_duration
    
    def cancel(self) -> None:
        """
        Cancel the trip.
        
        Raises:
            InvalidStateTransitionError: If trip cannot be cancelled
        """
        self._transition(TripState.CANCELLED)
        self.cancelled_at = datetime.now()
    
    def _calculate_cost(self, distance: float) -> float:
        """
        Calculate trip cost based on distance and zones.
        
        Args:
            distance: Trip distance in km
        
        Returns:
            Total trip cost
        """
        base_cost = self.BASE_FARE + (distance * self.PER_KM_RATE)
        
        # Apply cross-zone penalty
        if self.is_cross_zone:
            base_cost *= self.CROSS_ZONE_PENALTY
        
        return round(base_cost, 2)
    
    def is_terminal(self) -> bool:
        """Check if trip is in a terminal state."""
        return self.state in [TripState.COMPLETED, TripState.CANCELLED]
    
    def create_snapshot(self) -> 'TripSnapshot':
        """
        Create a snapshot of the current trip state for rollback purposes.
        
        Returns:
            TripSnapshot object containing current state
        """
        return TripSnapshot(
            trip_id=self.trip_id,
            rider_id=self.rider_id,
            driver_id=self.driver_id,
            pickup_location=self.pickup_location,
            dropoff_location=self.dropoff_location,
            pickup_zone=self.pickup_zone,
            dropoff_zone=self.dropoff_zone,
            state=self.state,
            state_history=self.state_history.copy(),
            distance=self.distance,
            estimated_duration=self.estimated_duration,
            actual_duration=self.actual_duration,
            cost=self.cost,
            path=self.path.copy(),
            is_cross_zone=self.is_cross_zone,
            created_at=self.created_at,
            assigned_at=self.assigned_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            cancelled_at=self.cancelled_at
        )
    
    def restore_from_snapshot(self, snapshot: 'TripSnapshot') -> None:
        """
        Restore trip state from a snapshot.
        
        Args:
            snapshot: TripSnapshot to restore from
        """
        self.rider_id = snapshot.rider_id
        self.driver_id = snapshot.driver_id
        self.pickup_location = snapshot.pickup_location
        self.dropoff_location = snapshot.dropoff_location
        self.pickup_zone = snapshot.pickup_zone
        self.dropoff_zone = snapshot.dropoff_zone
        self.state = snapshot.state
        self.state_history = snapshot.state_history.copy()
        self.distance = snapshot.distance
        self.estimated_duration = snapshot.estimated_duration
        self.actual_duration = snapshot.actual_duration
        self.cost = snapshot.cost
        self.path = snapshot.path.copy()
        self.is_cross_zone = snapshot.is_cross_zone
        self.created_at = snapshot.created_at
        self.assigned_at = snapshot.assigned_at
        self.started_at = snapshot.started_at
        self.completed_at = snapshot.completed_at
        self.cancelled_at = snapshot.cancelled_at
    
    def to_dict(self) -> dict:
        """Convert trip to dictionary for serialization."""
        return {
            "trip_id": self.trip_id,
            "rider_id": self.rider_id,
            "driver_id": self.driver_id,
            "pickup_location": self.pickup_location,
            "dropoff_location": self.dropoff_location,
            "pickup_zone": self.pickup_zone,
            "dropoff_zone": self.dropoff_zone,
            "state": self.state.value,
            "distance": self.distance,
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration,
            "cost": self.cost,
            "path": self.path,
            "is_cross_zone": self.is_cross_zone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None
        }


class TripSnapshot:
    """
    Immutable snapshot of trip state for rollback purposes.
    """
    
    def __init__(
        self,
        trip_id: str,
        rider_id: str,
        driver_id: Optional[str],
        pickup_location: str,
        dropoff_location: str,
        pickup_zone: str,
        dropoff_zone: str,
        state: TripState,
        state_history: List[tuple],
        distance: float,
        estimated_duration: float,
        actual_duration: float,
        cost: float,
        path: List[str],
        is_cross_zone: bool,
        created_at: datetime,
        assigned_at: Optional[datetime],
        started_at: Optional[datetime],
        completed_at: Optional[datetime],
        cancelled_at: Optional[datetime]
    ):
        self.trip_id = trip_id
        self.rider_id = rider_id
        self.driver_id = driver_id
        self.pickup_location = pickup_location
        self.dropoff_location = dropoff_location
        self.pickup_zone = pickup_zone
        self.dropoff_zone = dropoff_zone
        self.state = state
        self.state_history = state_history
        self.distance = distance
        self.estimated_duration = estimated_duration
        self.actual_duration = actual_duration
        self.cost = cost
        self.path = path
        self.is_cross_zone = is_cross_zone
        self.created_at = created_at
        self.assigned_at = assigned_at
        self.started_at = started_at
        self.completed_at = completed_at
        self.cancelled_at = cancelled_at

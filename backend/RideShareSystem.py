"""
RideShareSystem.py - Main system facade integrating all components.

This module provides:
- Unified API for the ride-sharing system
- Trip lifecycle management
- Analytics computation
- Rollback coordination
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math

from City import City
from Driver import Driver, DriverStatus
from Rider import Rider
from Trip import Trip, TripState, InvalidStateTransitionError
from DispatchEngine import DispatchEngine
from RollbackManager import RollbackManager, OperationType


class RideShareSystem:
    """
    Main facade for the ride-sharing system.
    
    Integrates all components and provides a unified API for:
    - Driver and rider management
    - Trip request and lifecycle management
    - Analytics
    - Rollback operations
    """
    
    def __init__(self, city: Optional[City] = None):
        """
        Initialize the ride-sharing system.
        
        Args:
            city: City graph (creates sample city if None)
        """
        # Initialize city
        self._city = city if city else City.create_sample_city()
        
        # Entity storage
        self._drivers: Dict[str, Driver] = {}
        self._riders: Dict[str, Rider] = {}
        self._trips: Dict[str, Trip] = {}
        
        # ID counters
        self._driver_counter = 0
        self._rider_counter = 0
        self._trip_counter = 0
        
        # Initialize dispatch engine
        self._dispatch_engine = DispatchEngine(self._city)
        
        # Initialize rollback manager
        self._rollback_manager = RollbackManager()
        self._rollback_manager.set_system_references(
            self._drivers, self._riders, self._trips
        )
    
    # ==================== Driver Management ====================
    
    def create_driver(self, name: str, location: str) -> Driver:
        """
        Create and register a new driver.
        
        Args:
            name: Driver's name
            location: Initial node ID
        
        Returns:
            Created Driver object
        
        Raises:
            ValueError: If location doesn't exist
        """
        zone = self._city.get_zone(location)
        if zone is None:
            raise ValueError(f"Location {location} does not exist")
        
        # Generate ID
        self._driver_counter += 1
        driver_id = f"D-{self._driver_counter:04d}"
        
        # Log operation BEFORE creating
        self._rollback_manager.log_operation(
            operation_type=OperationType.CREATE_DRIVER,
            description=f"Create driver {driver_id}: {name} at {location}",
            created_entity_id=driver_id,
            created_entity_type="driver"
        )
        
        # Create driver
        driver = Driver(driver_id, name, location, zone)
        self._drivers[driver_id] = driver
        self._dispatch_engine.register_driver(driver)
        
        return driver
    
    def get_driver(self, driver_id: str) -> Optional[Driver]:
        """Get a driver by ID."""
        return self._drivers.get(driver_id)
    
    def get_all_drivers(self) -> List[Driver]:
        """Get all drivers."""
        return list(self._drivers.values())
    
    def get_available_drivers(self) -> List[Driver]:
        """Get all available drivers."""
        return [d for d in self._drivers.values() if d.is_available()]
    
    def update_driver_location(self, driver_id: str, new_location: str) -> bool:
        """
        Update a driver's location.
        
        Args:
            driver_id: ID of the driver
            new_location: New node ID
        
        Returns:
            True if successful
        """
        driver = self._drivers.get(driver_id)
        if driver is None:
            return False
        
        new_zone = self._city.get_zone(new_location)
        if new_zone is None:
            return False
        
        # Log operation
        self._rollback_manager.log_operation(
            operation_type=OperationType.UPDATE_DRIVER_LOCATION,
            description=f"Update driver {driver_id} location to {new_location}",
            affected_driver_ids=[driver_id]
        )
        
        driver.update_location(new_location, new_zone)
        return True
    
    # ==================== Rider Management ====================
    
    def create_rider(self, name: str, location: str) -> Rider:
        """
        Create and register a new rider.
        
        Args:
            name: Rider's name
            location: Initial node ID
        
        Returns:
            Created Rider object
        
        Raises:
            ValueError: If location doesn't exist
        """
        if self._city.get_zone(location) is None:
            raise ValueError(f"Location {location} does not exist")
        
        # Generate ID
        self._rider_counter += 1
        rider_id = f"R-{self._rider_counter:04d}"
        
        # Log operation
        self._rollback_manager.log_operation(
            operation_type=OperationType.CREATE_RIDER,
            description=f"Create rider {rider_id}: {name} at {location}",
            created_entity_id=rider_id,
            created_entity_type="rider"
        )
        
        # Create rider
        rider = Rider(rider_id, name, location)
        self._riders[rider_id] = rider
        
        return rider
    
    def get_rider(self, rider_id: str) -> Optional[Rider]:
        """Get a rider by ID."""
        return self._riders.get(rider_id)
    
    def get_all_riders(self) -> List[Rider]:
        """Get all riders."""
        return list(self._riders.values())
    
    # ==================== Trip Management ====================
    
    def request_trip(
        self, 
        rider_id: str, 
        pickup_location: str, 
        dropoff_location: str
    ) -> Optional[Trip]:
        """
        Request a new trip.
        
        Args:
            rider_id: ID of the rider requesting
            pickup_location: Pickup node ID
            dropoff_location: Drop-off node ID
        
        Returns:
            Created Trip object, or None if request fails
        
        Raises:
            ValueError: If rider not found or locations invalid
        """
        # Validate rider
        rider = self._riders.get(rider_id)
        if rider is None:
            raise ValueError(f"Rider {rider_id} not found")
        if rider.has_active_trip():
            raise ValueError(f"Rider {rider_id} already has an active trip")
        
        # Validate locations
        pickup_zone = self._city.get_zone(pickup_location)
        dropoff_zone = self._city.get_zone(dropoff_location)
        
        if pickup_zone is None:
            raise ValueError(f"Pickup location {pickup_location} does not exist")
        if dropoff_zone is None:
            raise ValueError(f"Drop-off location {dropoff_location} does not exist")
        
        # Generate trip ID
        self._trip_counter += 1
        trip_id = f"T-{self._trip_counter:04d}"
        
        # Log operation
        self._rollback_manager.log_operation(
            operation_type=OperationType.REQUEST_TRIP,
            description=f"Request trip {trip_id} for rider {rider_id}",
            affected_rider_ids=[rider_id],
            created_entity_id=trip_id,
            created_entity_type="trip"
        )
        
        # Create trip
        trip = Trip(trip_id, rider_id, pickup_location, dropoff_location, 
                    pickup_zone, dropoff_zone)
        self._trips[trip_id] = trip
        
        # Update rider
        rider.request_trip(trip_id)
        
        return trip
    
    def assign_trip(self, trip_id: str) -> Optional[Driver]:
        """
        Assign the best available driver to a trip.
        
        Args:
            trip_id: ID of the trip to assign
        
        Returns:
            Assigned Driver, or None if no driver available
        
        Raises:
            ValueError: If trip not found or not in REQUESTED state
        """
        trip = self._trips.get(trip_id)
        if trip is None:
            raise ValueError(f"Trip {trip_id} not found")
        if trip.state != TripState.REQUESTED:
            raise InvalidStateTransitionError(
                f"Trip {trip_id} is not in REQUESTED state"
            )
        
        # Find best driver
        result = self._dispatch_engine.find_best_driver(trip.pickup_location)
        if result is None:
            return None
        
        driver, _, _ = result
        
        # Log operation
        self._rollback_manager.log_operation(
            operation_type=OperationType.ASSIGN_TRIP,
            description=f"Assign driver {driver.driver_id} to trip {trip_id}",
            affected_driver_ids=[driver.driver_id],
            affected_trip_ids=[trip_id]
        )
        
        # Perform assignment
        return self._dispatch_engine.assign_driver_to_trip(trip)
    
    def start_trip(self, trip_id: str) -> bool:
        """
        Start a trip (driver picked up rider).
        
        Args:
            trip_id: ID of the trip to start
        
        Returns:
            True if successful
        """
        trip = self._trips.get(trip_id)
        if trip is None:
            raise ValueError(f"Trip {trip_id} not found")
        
        # Log operation
        self._rollback_manager.log_operation(
            operation_type=OperationType.START_TRIP,
            description=f"Start trip {trip_id}",
            affected_trip_ids=[trip_id]
        )
        
        trip.start_trip()
        return True
    
    def complete_trip(self, trip_id: str, actual_duration: Optional[float] = None) -> bool:
        """
        Complete a trip.
        
        Args:
            trip_id: ID of the trip to complete
            actual_duration: Actual trip duration in minutes (optional)
        
        Returns:
            True if successful
        """
        trip = self._trips.get(trip_id)
        if trip is None:
            raise ValueError(f"Trip {trip_id} not found")
        
        rider = self._riders.get(trip.rider_id)
        driver = self._drivers.get(trip.driver_id) if trip.driver_id else None
        
        # Log operation
        affected_drivers = [trip.driver_id] if trip.driver_id else []
        self._rollback_manager.log_operation(
            operation_type=OperationType.COMPLETE_TRIP,
            description=f"Complete trip {trip_id}",
            affected_driver_ids=affected_drivers,
            affected_rider_ids=[trip.rider_id],
            affected_trip_ids=[trip_id]
        )
        
        # Complete the trip
        trip.complete_trip(actual_duration)
        
        # Update driver
        if driver:
            duration = actual_duration if actual_duration else trip.estimated_duration
            driver.complete_trip(trip.distance, duration)
            # Update driver location to drop-off
            driver.update_location(trip.dropoff_location, trip.dropoff_zone)
        
        # Update rider
        if rider:
            rider.complete_trip(trip_id, trip.distance, trip.cost)
            rider.update_location(trip.dropoff_location)
        
        return True
    
    def cancel_trip(self, trip_id: str) -> bool:
        """
        Cancel a trip.
        
        Args:
            trip_id: ID of the trip to cancel
        
        Returns:
            True if successful
        """
        trip = self._trips.get(trip_id)
        if trip is None:
            raise ValueError(f"Trip {trip_id} not found")
        
        rider = self._riders.get(trip.rider_id)
        driver = self._drivers.get(trip.driver_id) if trip.driver_id else None
        
        # Log operation
        affected_drivers = [trip.driver_id] if trip.driver_id else []
        self._rollback_manager.log_operation(
            operation_type=OperationType.CANCEL_TRIP,
            description=f"Cancel trip {trip_id}",
            affected_driver_ids=affected_drivers,
            affected_rider_ids=[trip.rider_id],
            affected_trip_ids=[trip_id]
        )
        
        # Cancel the trip
        trip.cancel()
        
        # Restore driver availability
        if driver:
            driver.cancel_current_trip()
        
        # Update rider
        if rider:
            rider.cancel_trip()
        
        return True
    
    def get_trip(self, trip_id: str) -> Optional[Trip]:
        """Get a trip by ID."""
        return self._trips.get(trip_id)
    
    def get_all_trips(self) -> List[Trip]:
        """Get all trips."""
        return list(self._trips.values())
    
    def get_active_trips(self) -> List[Trip]:
        """Get all active (non-terminal) trips."""
        return [t for t in self._trips.values() if not t.is_terminal()]
    
    def get_trip_estimate(
        self, 
        pickup_location: str, 
        dropoff_location: str
    ) -> Optional[Dict]:
        """
        Get estimated cost and duration for a potential trip.
        
        Args:
            pickup_location: Pickup node ID
            dropoff_location: Drop-off node ID
        
        Returns:
            Dictionary with estimates or None if invalid
        """
        return self._dispatch_engine.calculate_trip_estimate(
            pickup_location, dropoff_location
        )
    
    # ==================== Analytics ====================
    
    def get_analytics(self) -> Dict:
        """
        Get comprehensive system analytics.
        
        Returns:
            Dictionary containing various metrics
        """
        all_trips = list(self._trips.values())
        completed_trips = [t for t in all_trips if t.state == TripState.COMPLETED]
        cancelled_trips = [t for t in all_trips if t.state == TripState.CANCELLED]
        active_trips = [t for t in all_trips if not t.is_terminal()]
        
        # Calculate average trip distance
        avg_distance = 0.0
        if completed_trips:
            total_distance = sum(t.distance for t in completed_trips)
            avg_distance = total_distance / len(completed_trips)
        
        # Calculate driver utilization
        all_drivers = list(self._drivers.values())
        total_utilization = 0.0
        active_drivers = 0
        
        for driver in all_drivers:
            util = driver.get_utilization_rate()
            if driver.total_trips > 0 or driver.active_time > 0:
                total_utilization += util
                active_drivers += 1
        
        avg_utilization = total_utilization / active_drivers if active_drivers > 0 else 0.0
        
        # Calculate revenue
        total_revenue = sum(t.cost for t in completed_trips)
        
        # Calculate cross-zone stats
        cross_zone_completed = [t for t in completed_trips if t.is_cross_zone]
        
        return {
            "total_trips": len(all_trips),
            "completed_trips": len(completed_trips),
            "cancelled_trips": len(cancelled_trips),
            "active_trips": len(active_trips),
            "completion_rate": len(completed_trips) / len(all_trips) if all_trips else 0.0,
            "cancellation_rate": len(cancelled_trips) / len(all_trips) if all_trips else 0.0,
            "average_trip_distance": round(avg_distance, 2),
            "total_distance_covered": round(sum(t.distance for t in completed_trips), 2),
            "average_driver_utilization": round(avg_utilization, 4),
            "total_drivers": len(all_drivers),
            "available_drivers": len([d for d in all_drivers if d.is_available()]),
            "busy_drivers": len([d for d in all_drivers if d.status == DriverStatus.BUSY]),
            "total_revenue": round(total_revenue, 2),
            "cross_zone_trips": len(cross_zone_completed),
            "cross_zone_percentage": len(cross_zone_completed) / len(completed_trips) if completed_trips else 0.0,
            "total_riders": len(self._riders),
            "zone_statistics": self._dispatch_engine.get_zone_statistics()
        }
    
    def get_driver_analytics(self, driver_id: str) -> Optional[Dict]:
        """
        Get analytics for a specific driver.
        
        Args:
            driver_id: ID of the driver
        
        Returns:
            Analytics dictionary or None if driver not found
        """
        driver = self._drivers.get(driver_id)
        if driver is None:
            return None
        
        driver_trips = [t for t in self._trips.values() if t.driver_id == driver_id]
        completed = [t for t in driver_trips if t.state == TripState.COMPLETED]
        cancelled = [t for t in driver_trips if t.state == TripState.CANCELLED]
        
        return {
            "driver_id": driver_id,
            "name": driver.name,
            "total_trips": driver.total_trips,
            "total_distance": round(driver.total_distance, 2),
            "utilization_rate": round(driver.get_utilization_rate(), 4),
            "active_time": round(driver.active_time, 2),
            "idle_time": round(driver.idle_time, 2),
            "cancelled_trips": len(cancelled),
            "total_earnings": round(sum(t.cost for t in completed), 2),
            "current_status": driver.status.value,
            "current_zone": driver.zone
        }
    
    # ==================== Rollback Operations ====================
    
    def rollback_last(self) -> Optional[Dict]:
        """
        Rollback the most recent operation.
        
        Returns:
            Details of rolled back operation, or None if nothing to rollback
        """
        operation = self._rollback_manager.rollback_last()
        
        if operation is None:
            return None
        
        # Re-sync dispatch engine with current driver states
        for driver in self._drivers.values():
            if driver.driver_id not in [d.driver_id for d in self._dispatch_engine.get_all_drivers()]:
                self._dispatch_engine.register_driver(driver)
        
        return {
            "operation_id": operation.operation_id,
            "operation_type": operation.operation_type.value,
            "description": operation.description,
            "timestamp": operation.timestamp.isoformat()
        }
    
    def rollback_k(self, k: int) -> List[Dict]:
        """
        Rollback the last K operations.
        
        Args:
            k: Number of operations to rollback
        
        Returns:
            List of rolled back operation details
        """
        operations = self._rollback_manager.rollback_k(k)
        
        # Re-sync dispatch engine
        for driver in self._drivers.values():
            if driver.driver_id not in [d.driver_id for d in self._dispatch_engine.get_all_drivers()]:
                self._dispatch_engine.register_driver(driver)
        
        return [
            {
                "operation_id": op.operation_id,
                "operation_type": op.operation_type.value,
                "description": op.description,
                "timestamp": op.timestamp.isoformat()
            }
            for op in operations
        ]
    
    def can_rollback(self) -> bool:
        """Check if rollback is available."""
        return self._rollback_manager.can_rollback()
    
    def get_rollback_history(self, count: int = 10) -> List[Dict]:
        """Get recent operation history for rollback."""
        return self._rollback_manager.get_history(count)
    
    # ==================== City Access ====================
    
    def get_city(self) -> City:
        """Get the city graph."""
        return self._city
    
    def get_shortest_path(self, start: str, end: str) -> Tuple[List[str], float]:
        """Get shortest path between two locations."""
        return self._city.shortest_path(start, end)
    
    # ==================== Serialization ====================
    
    def to_dict(self) -> Dict:
        """
        Serialize the entire system state to a dictionary.
        
        Returns:
            Complete system state as dictionary
        """
        return {
            "city": self._city.to_dict(),
            "drivers": [d.to_dict() for d in self._drivers.values()],
            "riders": [r.to_dict() for r in self._riders.values()],
            "trips": [t.to_dict() for t in self._trips.values()],
            "analytics": self.get_analytics(),
            "rollback_available": self.can_rollback(),
            "operation_history": self.get_rollback_history()
        }

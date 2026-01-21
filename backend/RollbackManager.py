"""
RollbackManager.py - Operation logging and rollback system for ride-sharing.

This module implements:
- Command pattern for operation tracking
- Operation log with snapshots
- Rollback of last K operations
"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import copy

from Driver import Driver, DriverSnapshot
from Rider import Rider, RiderSnapshot
from Trip import Trip, TripSnapshot


class OperationType(Enum):
    """Types of operations that can be rolled back."""
    CREATE_DRIVER = "create_driver"
    CREATE_RIDER = "create_rider"
    REQUEST_TRIP = "request_trip"
    ASSIGN_TRIP = "assign_trip"
    START_TRIP = "start_trip"
    COMPLETE_TRIP = "complete_trip"
    CANCEL_TRIP = "cancel_trip"
    UPDATE_DRIVER_LOCATION = "update_driver_location"


@dataclass
class SystemSnapshot:
    """
    Complete snapshot of system state at a point in time.
    Used for rollback operations.
    """
    driver_snapshots: Dict[str, DriverSnapshot] = field(default_factory=dict)
    rider_snapshots: Dict[str, RiderSnapshot] = field(default_factory=dict)
    trip_snapshots: Dict[str, TripSnapshot] = field(default_factory=dict)
    # Track which entities existed at this point
    existing_driver_ids: List[str] = field(default_factory=list)
    existing_rider_ids: List[str] = field(default_factory=list)
    existing_trip_ids: List[str] = field(default_factory=list)


@dataclass
class Operation:
    """
    Represents a single operation in the system.
    Contains all information needed to undo the operation.
    """
    operation_id: str
    operation_type: OperationType
    timestamp: datetime
    description: str
    
    # Snapshot of affected entities BEFORE the operation
    before_snapshot: SystemSnapshot
    
    # IDs of entities affected by this operation
    affected_driver_ids: List[str] = field(default_factory=list)
    affected_rider_ids: List[str] = field(default_factory=list)
    affected_trip_ids: List[str] = field(default_factory=list)
    
    # For entity creation operations, track the created ID
    created_entity_id: Optional[str] = None
    created_entity_type: Optional[str] = None  # "driver", "rider", or "trip"


class OperationStack:
    """
    Custom stack implementation for operation history.
    Avoids global variables by encapsulating all state.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize the operation stack.
        
        Args:
            max_size: Maximum number of operations to store
        """
        self._stack: List[Operation] = []
        self._max_size = max_size
    
    def push(self, operation: Operation) -> None:
        """
        Push an operation onto the stack.
        
        Args:
            operation: Operation to push
        """
        if len(self._stack) >= self._max_size:
            # Remove oldest operation to make room
            self._stack.pop(0)
        self._stack.append(operation)
    
    def pop(self) -> Optional[Operation]:
        """
        Pop the most recent operation from the stack.
        
        Returns:
            Most recent operation, or None if stack is empty
        """
        if not self._stack:
            return None
        return self._stack.pop()
    
    def peek(self) -> Optional[Operation]:
        """
        View the most recent operation without removing it.
        
        Returns:
            Most recent operation, or None if stack is empty
        """
        if not self._stack:
            return None
        return self._stack[-1]
    
    def is_empty(self) -> bool:
        """Check if stack is empty."""
        return len(self._stack) == 0
    
    def size(self) -> int:
        """Get number of operations in the stack."""
        return len(self._stack)
    
    def clear(self) -> None:
        """Clear all operations from the stack."""
        self._stack.clear()
    
    def get_history(self, count: int = 10) -> List[Operation]:
        """
        Get the most recent operations.
        
        Args:
            count: Number of operations to retrieve
        
        Returns:
            List of recent operations (most recent first)
        """
        return list(reversed(self._stack[-count:]))


class RollbackManager:
    """
    Manages operation logging and rollback functionality.
    
    Implements the Command pattern for tracking and undoing operations.
    All state is encapsulated - no global variables are used.
    """
    
    def __init__(self, max_operations: int = 100):
        """
        Initialize the rollback manager.
        
        Args:
            max_operations: Maximum number of operations to track
        """
        self._operation_stack = OperationStack(max_operations)
        self._operation_counter = 0
        
        # References to system components (set during initialization)
        self._drivers: Optional[Dict[str, Driver]] = None
        self._riders: Optional[Dict[str, Rider]] = None
        self._trips: Optional[Dict[str, Trip]] = None
    
    def set_system_references(
        self,
        drivers: Dict[str, Driver],
        riders: Dict[str, Rider],
        trips: Dict[str, Trip]
    ) -> None:
        """
        Set references to system data structures.
        Must be called before logging operations.
        
        Args:
            drivers: Reference to drivers dictionary
            riders: Reference to riders dictionary
            trips: Reference to trips dictionary
        """
        self._drivers = drivers
        self._riders = riders
        self._trips = trips
    
    def _generate_operation_id(self) -> str:
        """Generate a unique operation ID."""
        self._operation_counter += 1
        return f"OP-{self._operation_counter:06d}"
    
    def _create_system_snapshot(
        self,
        driver_ids: Optional[List[str]] = None,
        rider_ids: Optional[List[str]] = None,
        trip_ids: Optional[List[str]] = None
    ) -> SystemSnapshot:
        """
        Create a snapshot of specified entities.
        
        Args:
            driver_ids: List of driver IDs to snapshot (None = all)
            rider_ids: List of rider IDs to snapshot (None = all)
            trip_ids: List of trip IDs to snapshot (None = all)
        
        Returns:
            SystemSnapshot containing entity states
        """
        snapshot = SystemSnapshot()
        
        # Snapshot existing entity IDs
        if self._drivers:
            snapshot.existing_driver_ids = list(self._drivers.keys())
        if self._riders:
            snapshot.existing_rider_ids = list(self._riders.keys())
        if self._trips:
            snapshot.existing_trip_ids = list(self._trips.keys())
        
        # Snapshot drivers
        if self._drivers:
            ids_to_snapshot = driver_ids if driver_ids else list(self._drivers.keys())
            for driver_id in ids_to_snapshot:
                if driver_id in self._drivers:
                    snapshot.driver_snapshots[driver_id] = \
                        self._drivers[driver_id].create_snapshot()
        
        # Snapshot riders
        if self._riders:
            ids_to_snapshot = rider_ids if rider_ids else list(self._riders.keys())
            for rider_id in ids_to_snapshot:
                if rider_id in self._riders:
                    snapshot.rider_snapshots[rider_id] = \
                        self._riders[rider_id].create_snapshot()
        
        # Snapshot trips
        if self._trips:
            ids_to_snapshot = trip_ids if trip_ids else list(self._trips.keys())
            for trip_id in ids_to_snapshot:
                if trip_id in self._trips:
                    snapshot.trip_snapshots[trip_id] = \
                        self._trips[trip_id].create_snapshot()
        
        return snapshot
    
    def log_operation(
        self,
        operation_type: OperationType,
        description: str,
        affected_driver_ids: Optional[List[str]] = None,
        affected_rider_ids: Optional[List[str]] = None,
        affected_trip_ids: Optional[List[str]] = None,
        created_entity_id: Optional[str] = None,
        created_entity_type: Optional[str] = None
    ) -> str:
        """
        Log an operation for potential rollback.
        Must be called BEFORE the operation is performed.
        
        Args:
            operation_type: Type of operation
            description: Human-readable description
            affected_driver_ids: IDs of drivers affected by this operation
            affected_rider_ids: IDs of riders affected by this operation
            affected_trip_ids: IDs of trips affected by this operation
            created_entity_id: ID of entity being created (if applicable)
            created_entity_type: Type of entity being created (if applicable)
        
        Returns:
            Operation ID for reference
        """
        operation_id = self._generate_operation_id()
        
        # Create snapshot of affected entities
        snapshot = self._create_system_snapshot(
            driver_ids=affected_driver_ids,
            rider_ids=affected_rider_ids,
            trip_ids=affected_trip_ids
        )
        
        operation = Operation(
            operation_id=operation_id,
            operation_type=operation_type,
            timestamp=datetime.now(),
            description=description,
            before_snapshot=snapshot,
            affected_driver_ids=affected_driver_ids or [],
            affected_rider_ids=affected_rider_ids or [],
            affected_trip_ids=affected_trip_ids or [],
            created_entity_id=created_entity_id,
            created_entity_type=created_entity_type
        )
        
        self._operation_stack.push(operation)
        return operation_id
    
    def rollback_last(self) -> Optional[Operation]:
        """
        Rollback the most recent operation.
        
        Returns:
            The rolled back operation, or None if no operations to rollback
        """
        operation = self._operation_stack.pop()
        
        if operation is None:
            return None
        
        self._apply_rollback(operation)
        return operation
    
    def rollback_k(self, k: int) -> List[Operation]:
        """
        Rollback the last K operations.
        
        Args:
            k: Number of operations to rollback
        
        Returns:
            List of rolled back operations (most recent first)
        """
        rolled_back = []
        
        for _ in range(k):
            operation = self.rollback_last()
            if operation is None:
                break
            rolled_back.append(operation)
        
        return rolled_back
    
    def _apply_rollback(self, operation: Operation) -> None:
        """
        Apply a rollback by restoring entity states from the snapshot.
        
        Args:
            operation: Operation to rollback
        """
        snapshot = operation.before_snapshot
        
        # Handle entity creation rollback (delete the created entity)
        if operation.created_entity_id and operation.created_entity_type:
            if operation.created_entity_type == "driver" and self._drivers:
                if operation.created_entity_id in self._drivers:
                    del self._drivers[operation.created_entity_id]
            elif operation.created_entity_type == "rider" and self._riders:
                if operation.created_entity_id in self._riders:
                    del self._riders[operation.created_entity_id]
            elif operation.created_entity_type == "trip" and self._trips:
                if operation.created_entity_id in self._trips:
                    del self._trips[operation.created_entity_id]
        
        # Restore driver states
        if self._drivers:
            for driver_id, driver_snapshot in snapshot.driver_snapshots.items():
                if driver_id in self._drivers:
                    self._drivers[driver_id].restore_from_snapshot(driver_snapshot)
        
        # Restore rider states
        if self._riders:
            for rider_id, rider_snapshot in snapshot.rider_snapshots.items():
                if rider_id in self._riders:
                    self._riders[rider_id].restore_from_snapshot(rider_snapshot)
        
        # Restore trip states
        if self._trips:
            for trip_id, trip_snapshot in snapshot.trip_snapshots.items():
                if trip_id in self._trips:
                    self._trips[trip_id].restore_from_snapshot(trip_snapshot)
        
        # Restore deleted entities (entities that existed before but don't now)
        # This handles cases where we need to restore a deleted entity
        if self._drivers:
            for driver_id in snapshot.existing_driver_ids:
                if driver_id not in self._drivers and driver_id in snapshot.driver_snapshots:
                    # Entity was deleted, restore it
                    driver_snapshot = snapshot.driver_snapshots[driver_id]
                    restored_driver = Driver(
                        driver_id=driver_snapshot.driver_id,
                        name=driver_snapshot.name,
                        current_location=driver_snapshot.current_location,
                        zone=driver_snapshot.zone
                    )
                    restored_driver.restore_from_snapshot(driver_snapshot)
                    self._drivers[driver_id] = restored_driver
        
        if self._riders:
            for rider_id in snapshot.existing_rider_ids:
                if rider_id not in self._riders and rider_id in snapshot.rider_snapshots:
                    rider_snapshot = snapshot.rider_snapshots[rider_id]
                    restored_rider = Rider(
                        rider_id=rider_snapshot.rider_id,
                        name=rider_snapshot.name,
                        current_location=rider_snapshot.current_location
                    )
                    restored_rider.restore_from_snapshot(rider_snapshot)
                    self._riders[rider_id] = restored_rider
        
        if self._trips:
            for trip_id in snapshot.existing_trip_ids:
                if trip_id not in self._trips and trip_id in snapshot.trip_snapshots:
                    trip_snapshot = snapshot.trip_snapshots[trip_id]
                    restored_trip = Trip(
                        trip_id=trip_snapshot.trip_id,
                        rider_id=trip_snapshot.rider_id,
                        pickup_location=trip_snapshot.pickup_location,
                        dropoff_location=trip_snapshot.dropoff_location,
                        pickup_zone=trip_snapshot.pickup_zone,
                        dropoff_zone=trip_snapshot.dropoff_zone
                    )
                    restored_trip.restore_from_snapshot(trip_snapshot)
                    self._trips[trip_id] = restored_trip
    
    def can_rollback(self) -> bool:
        """Check if there are operations to rollback."""
        return not self._operation_stack.is_empty()
    
    def get_operation_count(self) -> int:
        """Get the number of operations available for rollback."""
        return self._operation_stack.size()
    
    def get_history(self, count: int = 10) -> List[Dict]:
        """
        Get recent operation history.
        
        Args:
            count: Number of operations to retrieve
        
        Returns:
            List of operation dictionaries (most recent first)
        """
        operations = self._operation_stack.get_history(count)
        return [
            {
                "operation_id": op.operation_id,
                "operation_type": op.operation_type.value,
                "timestamp": op.timestamp.isoformat(),
                "description": op.description,
                "affected_drivers": op.affected_driver_ids,
                "affected_riders": op.affected_rider_ids,
                "affected_trips": op.affected_trip_ids
            }
            for op in operations
        ]
    
    def clear_history(self) -> None:
        """Clear all operation history."""
        self._operation_stack.clear()

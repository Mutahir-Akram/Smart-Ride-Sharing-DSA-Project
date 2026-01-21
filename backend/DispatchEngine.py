"""
DispatchEngine.py - Driver assignment and dispatch logic for ride-sharing system.

This module implements:
- Zone-based driver assignment (prefer same zone)
- Cross-zone assignment with penalty
- Optimal driver selection based on distance
"""

from typing import Dict, List, Optional, Tuple
import math

from City import City
from Driver import Driver, DriverStatus
from Trip import Trip


class DispatchEngine:
    """
    Handles driver assignment and dispatch decisions.
    
    Assignment rules:
    1. Prefer drivers in the same zone as the pickup location
    2. Allow cross-zone assignments with higher cost/penalty
    3. Select the closest available driver
    """
    
    # Penalty multiplier for cross-zone assignments
    CROSS_ZONE_PENALTY = 1.5
    
    def __init__(self, city: City):
        """
        Initialize the dispatch engine.
        
        Args:
            city: City graph for routing calculations
        """
        self._city = city
        self._drivers: Dict[str, Driver] = {}
    
    def register_driver(self, driver: Driver) -> None:
        """
        Register a driver with the dispatch engine.
        
        Args:
            driver: Driver to register
        """
        self._drivers[driver.driver_id] = driver
    
    def unregister_driver(self, driver_id: str) -> None:
        """
        Unregister a driver from the dispatch engine.
        
        Args:
            driver_id: ID of driver to unregister
        """
        if driver_id in self._drivers:
            del self._drivers[driver_id]
    
    def get_driver(self, driver_id: str) -> Optional[Driver]:
        """Get a driver by ID."""
        return self._drivers.get(driver_id)
    
    def get_all_drivers(self) -> List[Driver]:
        """Get all registered drivers."""
        return list(self._drivers.values())
    
    def get_available_drivers(self) -> List[Driver]:
        """Get all available drivers."""
        return [d for d in self._drivers.values() if d.is_available()]
    
    def get_drivers_in_zone(self, zone: str) -> List[Driver]:
        """Get all drivers currently in a specific zone."""
        return [d for d in self._drivers.values() if d.zone == zone]
    
    def get_available_drivers_in_zone(self, zone: str) -> List[Driver]:
        """Get all available drivers in a specific zone."""
        return [d for d in self._drivers.values() 
                if d.zone == zone and d.is_available()]
    
    def find_best_driver(self, pickup_location: str) -> Optional[Tuple[Driver, float, bool]]:
        """
        Find the best available driver for a pickup location.
        
        Algorithm:
        1. Get the zone of the pickup location
        2. Search for available drivers in the same zone first
        3. If no same-zone drivers, search all zones
        4. Select the closest driver by distance
        5. Apply cross-zone penalty if applicable
        
        Args:
            pickup_location: Node ID for the pickup location
        
        Returns:
            Tuple of (driver, distance_to_pickup, is_cross_zone) or None if no driver available
        """
        pickup_zone = self._city.get_zone(pickup_location)
        if pickup_zone is None:
            return None
        
        # First, try to find drivers in the same zone
        same_zone_drivers = self.get_available_drivers_in_zone(pickup_zone)
        
        best_driver: Optional[Driver] = None
        best_distance = math.inf
        is_cross_zone = False
        
        # Check same-zone drivers first (no penalty)
        for driver in same_zone_drivers:
            distance = self._city.calculate_distance(
                driver.current_location, pickup_location
            )
            if distance < best_distance:
                best_distance = distance
                best_driver = driver
        
        # If found a same-zone driver, return it
        if best_driver is not None:
            return (best_driver, best_distance, False)
        
        # Otherwise, check all available drivers (cross-zone)
        all_available = self.get_available_drivers()
        
        for driver in all_available:
            distance = self._city.calculate_distance(
                driver.current_location, pickup_location
            )
            # Apply cross-zone penalty for comparison
            effective_distance = distance * self.CROSS_ZONE_PENALTY
            
            if effective_distance < best_distance:
                best_distance = effective_distance
                best_driver = driver
                is_cross_zone = True
        
        if best_driver is not None:
            # Return actual distance, not penalized distance
            actual_distance = self._city.calculate_distance(
                best_driver.current_location, pickup_location
            )
            return (best_driver, actual_distance, True)
        
        return None
    
    def assign_driver_to_trip(self, trip: Trip) -> Optional[Driver]:
        """
        Find and assign the best driver to a trip.
        
        Args:
            trip: Trip to assign a driver to
        
        Returns:
            Assigned driver, or None if no driver available
        """
        result = self.find_best_driver(trip.pickup_location)
        
        if result is None:
            return None
        
        driver, pickup_distance, is_cross_zone = result
        
        # Calculate route distance and path
        path, trip_distance = self._city.shortest_path(
            trip.pickup_location, trip.dropoff_location
        )
        
        if trip_distance == math.inf:
            return None  # No valid route
        
        # Assign the driver to the trip
        driver.assign_trip(trip.trip_id)
        trip.assign_driver(driver.driver_id, trip_distance, path)
        
        return driver
    
    def calculate_trip_estimate(
        self, 
        pickup_location: str, 
        dropoff_location: str
    ) -> Optional[Dict]:
        """
        Calculate estimates for a potential trip without assigning.
        
        Args:
            pickup_location: Node ID for pickup
            dropoff_location: Node ID for drop-off
        
        Returns:
            Dictionary with estimates or None if invalid locations
        """
        pickup_zone = self._city.get_zone(pickup_location)
        dropoff_zone = self._city.get_zone(dropoff_location)
        
        if pickup_zone is None or dropoff_zone is None:
            return None
        
        # Calculate route
        path, distance = self._city.shortest_path(pickup_location, dropoff_location)
        
        if distance == math.inf:
            return None
        
        # Calculate cost
        is_cross_zone = pickup_zone != dropoff_zone
        base_cost = Trip.BASE_FARE + (distance * Trip.PER_KM_RATE)
        
        if is_cross_zone:
            cost = base_cost * Trip.CROSS_ZONE_PENALTY
        else:
            cost = base_cost
        
        # Estimate duration (30 km/h average)
        estimated_duration = (distance / 30) * 60  # minutes
        
        # Find best available driver
        driver_result = self.find_best_driver(pickup_location)
        driver_eta = None
        
        if driver_result:
            driver, pickup_distance, _ = driver_result
            driver_eta = (pickup_distance / 30) * 60  # minutes
        
        return {
            "distance": round(distance, 2),
            "estimated_duration": round(estimated_duration, 1),
            "cost": round(cost, 2),
            "is_cross_zone": is_cross_zone,
            "path": path,
            "driver_available": driver_result is not None,
            "driver_eta": round(driver_eta, 1) if driver_eta else None
        }
    
    def update_driver_location(
        self, 
        driver_id: str, 
        new_location: str
    ) -> bool:
        """
        Update a driver's current location.
        
        Args:
            driver_id: ID of the driver
            new_location: New node ID
        
        Returns:
            True if successful, False if driver not found
        """
        driver = self._drivers.get(driver_id)
        if driver is None:
            return False
        
        new_zone = self._city.get_zone(new_location)
        if new_zone is None:
            return False
        
        driver.update_location(new_location, new_zone)
        return True
    
    def get_zone_statistics(self) -> Dict:
        """
        Get statistics about driver distribution across zones.
        
        Returns:
            Dictionary with zone-level statistics
        """
        zones = self._city.get_all_zones()
        stats = {}
        
        for zone in zones:
            zone_drivers = self.get_drivers_in_zone(zone)
            available = [d for d in zone_drivers if d.is_available()]
            busy = [d for d in zone_drivers if d.status == DriverStatus.BUSY]
            offline = [d for d in zone_drivers if d.status == DriverStatus.OFFLINE]
            
            stats[zone] = {
                "total_drivers": len(zone_drivers),
                "available": len(available),
                "busy": len(busy),
                "offline": len(offline)
            }
        
        return stats

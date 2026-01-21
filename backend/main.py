"""
main.py - Demo script for the ride-sharing system.

This script demonstrates:
- Driver and rider creation
- Trip request and lifecycle
- Cancellation handling
- Rollback operations
- Analytics computation
"""

from RideShareSystem import RideShareSystem
from Trip import TripState


def print_separator(title: str = "") -> None:
    """Print a visual separator."""
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def print_trip_info(trip) -> None:
    """Print trip details."""
    print(f"  Trip ID: {trip.trip_id}")
    print(f"  Rider: {trip.rider_id}")
    print(f"  Driver: {trip.driver_id or 'Not assigned'}")
    print(f"  State: {trip.state.value}")
    print(f"  Pickup: {trip.pickup_location} ({trip.pickup_zone})")
    print(f"  Drop-off: {trip.dropoff_location} ({trip.dropoff_zone})")
    print(f"  Distance: {trip.distance} km")
    print(f"  Cost: ${trip.cost}")
    print(f"  Cross-zone: {trip.is_cross_zone}")


def print_analytics(analytics: dict) -> None:
    """Print analytics summary."""
    print(f"  Total Trips: {analytics['total_trips']}")
    print(f"  Completed: {analytics['completed_trips']}")
    print(f"  Cancelled: {analytics['cancelled_trips']}")
    print(f"  Active: {analytics['active_trips']}")
    print(f"  Completion Rate: {analytics['completion_rate']:.1%}")
    print(f"  Avg Distance: {analytics['average_trip_distance']} km")
    print(f"  Total Revenue: ${analytics['total_revenue']}")
    print(f"  Avg Driver Utilization: {analytics['average_driver_utilization']:.1%}")
    print(f"  Cross-zone Trips: {analytics['cross_zone_trips']} ({analytics['cross_zone_percentage']:.1%})")


def main():
    """Main demo function."""
    print_separator("RIDE-SHARING SYSTEM DEMO")
    
    # Initialize system
    print("\nInitializing system with sample city...")
    system = RideShareSystem()
    
    city = system.get_city()
    print(f"City: {city.name}")
    print(f"Zones: {', '.join(city.get_all_zones())}")
    print(f"Nodes: {len(city.get_all_nodes())}")
    
    # ==================== Create Drivers ====================
    print_separator("CREATING DRIVERS")
    
    drivers = [
        system.create_driver("Alice", "A1"),   # Zone A
        system.create_driver("Bob", "A2"),     # Zone A
        system.create_driver("Charlie", "B1"), # Zone B
        system.create_driver("Diana", "B2"),   # Zone B
        system.create_driver("Eve", "C1"),     # Zone C
    ]
    
    for driver in drivers:
        print(f"  Created: {driver.driver_id} - {driver.name} at {driver.current_location} ({driver.zone})")
    
    # ==================== Create Riders ====================
    print_separator("CREATING RIDERS")
    
    riders = [
        system.create_rider("John", "A1"),
        system.create_rider("Jane", "B1"),
        system.create_rider("Mike", "C1"),
    ]
    
    for rider in riders:
        print(f"  Created: {rider.rider_id} - {rider.name} at {rider.current_location}")
    
    # ==================== Shortest Path Demo ====================
    print_separator("SHORTEST PATH CALCULATION")
    
    path, distance = system.get_shortest_path("A1", "B3")
    print(f"  From A1 to B3:")
    print(f"  Path: {' -> '.join(path)}")
    print(f"  Distance: {distance} km")
    
    # ==================== Trip Request (Same Zone) ====================
    print_separator("TRIP 1: SAME-ZONE TRIP")
    
    # Get estimate first
    estimate = system.get_trip_estimate("A1", "A3")
    print("  Trip Estimate (A1 to A3):")
    print(f"    Distance: {estimate['distance']} km")
    print(f"    Duration: {estimate['estimated_duration']} min")
    print(f"    Cost: ${estimate['cost']}")
    print(f"    Cross-zone: {estimate['is_cross_zone']}")
    
    # Request trip
    trip1 = system.request_trip("R-0001", "A1", "A3")
    print(f"\n  Trip requested: {trip1.trip_id}")
    
    # Assign driver
    assigned_driver = system.assign_trip(trip1.trip_id)
    print(f"  Driver assigned: {assigned_driver.driver_id} - {assigned_driver.name}")
    print_trip_info(trip1)
    
    # Start and complete trip
    system.start_trip(trip1.trip_id)
    print(f"\n  Trip started")
    
    system.complete_trip(trip1.trip_id, actual_duration=15.0)
    print(f"  Trip completed")
    print_trip_info(trip1)
    
    # ==================== Trip Request (Cross Zone) ====================
    print_separator("TRIP 2: CROSS-ZONE TRIP")
    
    trip2 = system.request_trip("R-0002", "B1", "C2")
    print(f"  Trip requested: {trip2.trip_id}")
    
    assigned_driver = system.assign_trip(trip2.trip_id)
    print(f"  Driver assigned: {assigned_driver.driver_id} - {assigned_driver.name}")
    print_trip_info(trip2)
    
    system.start_trip(trip2.trip_id)
    system.complete_trip(trip2.trip_id, actual_duration=20.0)
    print(f"\n  Trip completed")
    
    # ==================== Trip Cancellation ====================
    print_separator("TRIP 3: CANCELLATION DEMO")
    
    trip3 = system.request_trip("R-0003", "C1", "A1")
    print(f"  Trip requested: {trip3.trip_id}")
    
    assigned_driver = system.assign_trip(trip3.trip_id)
    print(f"  Driver assigned: {assigned_driver.driver_id}")
    print(f"  Driver status before cancel: {assigned_driver.status.value}")
    
    system.cancel_trip(trip3.trip_id)
    print(f"\n  Trip cancelled")
    print(f"  Trip state: {trip3.state.value}")
    print(f"  Driver status after cancel: {assigned_driver.status.value}")
    
    # ==================== Analytics Before Rollback ====================
    print_separator("ANALYTICS (BEFORE ROLLBACK)")
    
    analytics = system.get_analytics()
    print_analytics(analytics)
    
    # ==================== Rollback Demo ====================
    print_separator("ROLLBACK DEMONSTRATION")
    
    print("  Operation history:")
    history = system.get_rollback_history(5)
    for op in history:
        print(f"    {op['operation_id']}: {op['description']}")
    
    print("\n  Performing rollback of last operation...")
    rolled_back = system.rollback_last()
    print(f"  Rolled back: {rolled_back['description']}")
    
    # Check trip3 state after rollback
    trip3 = system.get_trip(trip3.trip_id)
    print(f"\n  Trip 3 state after rollback: {trip3.state.value}")
    
    # ==================== Multiple Rollbacks ====================
    print_separator("MULTIPLE ROLLBACKS (K=2)")
    
    print("  Before rollback:")
    print(f"    Trip 3 state: {trip3.state.value}")
    print(f"    Driver status: {system.get_driver(trip3.driver_id).status.value if trip3.driver_id else 'N/A'}")
    
    rolled_back_ops = system.rollback_k(2)
    print(f"\n  Rolled back {len(rolled_back_ops)} operations:")
    for op in rolled_back_ops:
        print(f"    - {op['description']}")
    
    trip3 = system.get_trip(trip3.trip_id)
    print(f"\n  After rollback:")
    print(f"    Trip 3 state: {trip3.state.value}")
    
    # ==================== Analytics After Rollback ====================
    print_separator("ANALYTICS (AFTER ROLLBACK)")
    
    analytics = system.get_analytics()
    print_analytics(analytics)
    
    # ==================== Driver Analytics ====================
    print_separator("INDIVIDUAL DRIVER ANALYTICS")
    
    for driver in drivers[:2]:  # Show first 2 drivers
        driver_analytics = system.get_driver_analytics(driver.driver_id)
        print(f"\n  {driver_analytics['name']} ({driver_analytics['driver_id']}):")
        print(f"    Trips: {driver_analytics['total_trips']}")
        print(f"    Distance: {driver_analytics['total_distance']} km")
        print(f"    Earnings: ${driver_analytics['total_earnings']}")
        print(f"    Status: {driver_analytics['current_status']}")
    
    # ==================== Zone Statistics ====================
    print_separator("ZONE STATISTICS")
    
    zone_stats = analytics['zone_statistics']
    for zone, stats in zone_stats.items():
        print(f"  {zone}:")
        print(f"    Total drivers: {stats['total_drivers']}")
        print(f"    Available: {stats['available']}")
        print(f"    Busy: {stats['busy']}")
    
    print_separator("DEMO COMPLETE")
    print("\nThe ride-sharing system demo has completed successfully!")
    print("All features demonstrated: creation, trips, cancellation, rollback, analytics.")


if __name__ == "__main__":
    main()

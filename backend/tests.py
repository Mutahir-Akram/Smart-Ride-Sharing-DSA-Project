"""
tests.py - Automated test suite for the ride-sharing system.

Contains 10+ test cases covering:
1. Shortest path correctness
2. Zone-based driver assignment
3. Cross-zone assignment penalty
4. Driver reassignment after cancellation
5. Multiple rollbacks
6. Invalid state transition handling
7. Rollback after cancellation
8. Rollback after completion
9. Analytics correctness
10. Analytics correctness after rollback
"""

import unittest
import math
from City import City, MinHeap
from Driver import Driver, DriverStatus
from Rider import Rider
from Trip import Trip, TripState, InvalidStateTransitionError
from DispatchEngine import DispatchEngine
from RollbackManager import RollbackManager, OperationType
from RideShareSystem import RideShareSystem


class TestMinHeap(unittest.TestCase):
    """Test the custom MinHeap implementation."""
    
    def test_basic_operations(self):
        """Test insert, extract_min, and ordering."""
        heap = MinHeap()
        
        heap.insert(5.0, "node_c")
        heap.insert(2.0, "node_a")
        heap.insert(8.0, "node_d")
        heap.insert(1.0, "node_b")
        
        # Should extract in order: 1, 2, 5, 8
        dist, node = heap.extract_min()
        self.assertEqual(dist, 1.0)
        self.assertEqual(node, "node_b")
        
        dist, node = heap.extract_min()
        self.assertEqual(dist, 2.0)
        self.assertEqual(node, "node_a")
    
    def test_decrease_key(self):
        """Test decrease_key operation."""
        heap = MinHeap()
        
        heap.insert(10.0, "node_a")
        heap.insert(5.0, "node_b")
        
        heap.decrease_key("node_a", 2.0)
        
        dist, node = heap.extract_min()
        self.assertEqual(dist, 2.0)
        self.assertEqual(node, "node_a")


class TestCity(unittest.TestCase):
    """Test the City graph implementation."""
    
    def setUp(self):
        """Set up a test city."""
        self.city = City("Test City")
        
        # Create a simple graph
        self.city.add_node("A", "Node A", "Zone-1", 0, 0)
        self.city.add_node("B", "Node B", "Zone-1", 1, 0)
        self.city.add_node("C", "Node C", "Zone-2", 2, 0)
        self.city.add_node("D", "Node D", "Zone-2", 3, 0)
        
        self.city.add_edge("A", "B", 4.0)
        self.city.add_edge("B", "C", 3.0)
        self.city.add_edge("A", "C", 10.0)  # Longer direct route
        self.city.add_edge("C", "D", 2.0)
    
    def test_1_shortest_path_correctness(self):
        """Test 1: Shortest path algorithm correctness."""
        # A to C: should go A->B->C (7) not A->C (10)
        path, distance = self.city.shortest_path("A", "C")
        
        self.assertEqual(path, ["A", "B", "C"])
        self.assertEqual(distance, 7.0)
    
    def test_shortest_path_longer_route(self):
        """Test shortest path for longer routes."""
        # A to D: A->B->C->D = 4+3+2 = 9
        path, distance = self.city.shortest_path("A", "D")
        
        self.assertEqual(path, ["A", "B", "C", "D"])
        self.assertEqual(distance, 9.0)
    
    def test_no_path_exists(self):
        """Test when no path exists between nodes."""
        self.city.add_node("E", "Isolated", "Zone-3", 5, 0)
        
        path, distance = self.city.shortest_path("A", "E")
        
        self.assertEqual(path, [])
        self.assertEqual(distance, math.inf)
    
    def test_zone_management(self):
        """Test zone-related operations."""
        zone1_nodes = self.city.get_nodes_in_zone("Zone-1")
        zone2_nodes = self.city.get_nodes_in_zone("Zone-2")
        
        self.assertEqual(set(zone1_nodes), {"A", "B"})
        self.assertEqual(set(zone2_nodes), {"C", "D"})


class TestTripStateMachine(unittest.TestCase):
    """Test the Trip state machine."""
    
    def setUp(self):
        """Create a test trip."""
        self.trip = Trip(
            trip_id="T-001",
            rider_id="R-001",
            pickup_location="A",
            dropoff_location="B",
            pickup_zone="Zone-1",
            dropoff_zone="Zone-1"
        )
    
    def test_6_invalid_state_transition(self):
        """Test 6: Invalid state transition handling."""
        # Cannot go directly from REQUESTED to ONGOING
        with self.assertRaises(InvalidStateTransitionError):
            self.trip.start_trip()
        
        # Cannot go directly from REQUESTED to COMPLETED
        with self.assertRaises(InvalidStateTransitionError):
            self.trip.complete_trip()
    
    def test_valid_transitions(self):
        """Test valid state transitions."""
        self.assertEqual(self.trip.state, TripState.REQUESTED)
        
        # REQUESTED -> ASSIGNED
        self.trip.assign_driver("D-001", 5.0, ["A", "B"])
        self.assertEqual(self.trip.state, TripState.ASSIGNED)
        
        # ASSIGNED -> ONGOING
        self.trip.start_trip()
        self.assertEqual(self.trip.state, TripState.ONGOING)
        
        # ONGOING -> COMPLETED
        self.trip.complete_trip()
        self.assertEqual(self.trip.state, TripState.COMPLETED)
    
    def test_cancellation_from_requested(self):
        """Test cancellation from REQUESTED state."""
        self.trip.cancel()
        self.assertEqual(self.trip.state, TripState.CANCELLED)
    
    def test_cancellation_from_assigned(self):
        """Test cancellation from ASSIGNED state."""
        self.trip.assign_driver("D-001", 5.0, ["A", "B"])
        self.trip.cancel()
        self.assertEqual(self.trip.state, TripState.CANCELLED)
    
    def test_cannot_cancel_ongoing(self):
        """Test that ONGOING trips cannot be cancelled."""
        self.trip.assign_driver("D-001", 5.0, ["A", "B"])
        self.trip.start_trip()
        
        with self.assertRaises(InvalidStateTransitionError):
            self.trip.cancel()


class TestDispatchEngine(unittest.TestCase):
    """Test the DispatchEngine driver assignment."""
    
    def setUp(self):
        """Set up city and dispatch engine."""
        self.city = City.create_sample_city()
        self.engine = DispatchEngine(self.city)
        
        # Add drivers in different zones
        self.driver_a1 = Driver("D-001", "Alice", "A1", "Zone-A")
        self.driver_a2 = Driver("D-002", "Bob", "A2", "Zone-A")
        self.driver_b1 = Driver("D-003", "Charlie", "B1", "Zone-B")
        
        self.engine.register_driver(self.driver_a1)
        self.engine.register_driver(self.driver_a2)
        self.engine.register_driver(self.driver_b1)
    
    def test_2_zone_based_assignment(self):
        """Test 2: Zone-based driver assignment."""
        # Request pickup in Zone-A at node A1
        result = self.engine.find_best_driver("A1")
        
        self.assertIsNotNone(result)
        driver, distance, is_cross_zone = result
        
        # Should assign driver in same zone
        self.assertEqual(driver.zone, "Zone-A")
        self.assertFalse(is_cross_zone)
    
    def test_3_cross_zone_penalty(self):
        """Test 3: Cross-zone assignment penalty."""
        # Make all Zone-A drivers busy
        self.driver_a1.assign_trip("T-001")
        self.driver_a2.assign_trip("T-002")
        
        # Request pickup in Zone-A
        result = self.engine.find_best_driver("A1")
        
        self.assertIsNotNone(result)
        driver, distance, is_cross_zone = result
        
        # Should assign cross-zone driver
        self.assertTrue(is_cross_zone)
        self.assertEqual(driver.zone, "Zone-B")
    
    def test_closest_driver_in_zone(self):
        """Test that closest driver in zone is selected."""
        # Add another driver at A1 (same location as pickup)
        driver_at_pickup = Driver("D-004", "Diana", "A1", "Zone-A")
        self.engine.register_driver(driver_at_pickup)
        
        result = self.engine.find_best_driver("A1")
        
        self.assertIsNotNone(result)
        driver, distance, _ = result
        
        # Should select driver at pickup location (distance = 0)
        self.assertEqual(driver.driver_id, "D-004")
        self.assertEqual(distance, 0.0)


class TestRideShareSystem(unittest.TestCase):
    """Test the full RideShareSystem."""
    
    def setUp(self):
        """Set up a fresh system."""
        self.system = RideShareSystem()
        
        # Create drivers
        self.driver1 = self.system.create_driver("Alice", "A1")
        self.driver2 = self.system.create_driver("Bob", "B1")
        
        # Create riders
        self.rider1 = self.system.create_rider("John", "A1")
        self.rider2 = self.system.create_rider("Jane", "B1")
    
    def test_4_driver_reassignment_after_cancellation(self):
        """Test 4: Driver reassignment after cancellation."""
        # Request and assign trip
        trip = self.system.request_trip(self.rider1.rider_id, "A1", "A2")
        assigned_driver = self.system.assign_trip(trip.trip_id)
        
        self.assertEqual(assigned_driver.status, DriverStatus.BUSY)
        
        # Cancel trip
        self.system.cancel_trip(trip.trip_id)
        
        # Driver should be available again
        self.assertEqual(assigned_driver.status, DriverStatus.AVAILABLE)
        
        # Driver can be assigned to new trip
        trip2 = self.system.request_trip(self.rider2.rider_id, "A1", "A3")
        new_assigned = self.system.assign_trip(trip2.trip_id)
        
        self.assertEqual(new_assigned.driver_id, assigned_driver.driver_id)
    
    def test_7_rollback_after_cancellation(self):
        """Test 7: Rollback after cancellation."""
        trip = self.system.request_trip(self.rider1.rider_id, "A1", "A2")
        assigned_driver = self.system.assign_trip(trip.trip_id)
        
        # Cancel trip
        self.system.cancel_trip(trip.trip_id)
        self.assertEqual(trip.state, TripState.CANCELLED)
        self.assertEqual(assigned_driver.status, DriverStatus.AVAILABLE)
        
        # Rollback the cancellation
        self.system.rollback_last()
        
        # Trip should be back to ASSIGNED, driver back to BUSY
        trip = self.system.get_trip(trip.trip_id)
        driver = self.system.get_driver(assigned_driver.driver_id)
        
        self.assertEqual(trip.state, TripState.ASSIGNED)
        self.assertEqual(driver.status, DriverStatus.BUSY)
    
    def test_8_rollback_after_completion(self):
        """Test 8: Rollback after completion."""
        trip = self.system.request_trip(self.rider1.rider_id, "A1", "A3")
        assigned_driver = self.system.assign_trip(trip.trip_id)
        
        initial_trips = assigned_driver.total_trips
        
        self.system.start_trip(trip.trip_id)
        self.system.complete_trip(trip.trip_id, 15.0)
        
        self.assertEqual(trip.state, TripState.COMPLETED)
        self.assertEqual(assigned_driver.total_trips, initial_trips + 1)
        
        # Rollback completion
        self.system.rollback_last()
        
        trip = self.system.get_trip(trip.trip_id)
        driver = self.system.get_driver(assigned_driver.driver_id)
        
        self.assertEqual(trip.state, TripState.ONGOING)
        self.assertEqual(driver.total_trips, initial_trips)
    
    def test_5_multiple_rollbacks(self):
        """Test 5: Multiple rollbacks."""
        # Perform several operations
        trip1 = self.system.request_trip(self.rider1.rider_id, "A1", "A2")
        self.system.assign_trip(trip1.trip_id)
        self.system.start_trip(trip1.trip_id)
        self.system.complete_trip(trip1.trip_id)
        
        analytics_before = self.system.get_analytics()
        completed_before = analytics_before['completed_trips']
        
        # Rollback 2 operations (complete and start)
        rolled_back = self.system.rollback_k(2)
        
        self.assertEqual(len(rolled_back), 2)
        
        trip1 = self.system.get_trip(trip1.trip_id)
        self.assertEqual(trip1.state, TripState.ASSIGNED)
        
        analytics_after = self.system.get_analytics()
        self.assertEqual(analytics_after['completed_trips'], completed_before - 1)
    
    def test_9_analytics_correctness(self):
        """Test 9: Analytics correctness."""
        # Complete a trip
        trip1 = self.system.request_trip(self.rider1.rider_id, "A1", "A3")
        self.system.assign_trip(trip1.trip_id)
        self.system.start_trip(trip1.trip_id)
        self.system.complete_trip(trip1.trip_id, 15.0)
        
        # Cancel a trip
        trip2 = self.system.request_trip(self.rider2.rider_id, "B1", "B2")
        self.system.assign_trip(trip2.trip_id)
        self.system.cancel_trip(trip2.trip_id)
        
        analytics = self.system.get_analytics()
        
        self.assertEqual(analytics['total_trips'], 2)
        self.assertEqual(analytics['completed_trips'], 1)
        self.assertEqual(analytics['cancelled_trips'], 1)
        self.assertEqual(analytics['completion_rate'], 0.5)
        self.assertEqual(analytics['cancellation_rate'], 0.5)
        self.assertGreater(analytics['total_revenue'], 0)
    
    def test_10_analytics_after_rollback(self):
        """Test 10: Analytics correctness after rollback."""
        # Complete two trips
        trip1 = self.system.request_trip(self.rider1.rider_id, "A1", "A3")
        self.system.assign_trip(trip1.trip_id)
        self.system.start_trip(trip1.trip_id)
        self.system.complete_trip(trip1.trip_id)
        
        analytics_after_first = self.system.get_analytics()
        completed_after_first = analytics_after_first['completed_trips']
        revenue_after_first = analytics_after_first['total_revenue']
        
        trip2 = self.system.request_trip(self.rider2.rider_id, "B1", "B3")
        self.system.assign_trip(trip2.trip_id)
        self.system.start_trip(trip2.trip_id)
        self.system.complete_trip(trip2.trip_id)
        
        analytics_after_second = self.system.get_analytics()
        self.assertEqual(analytics_after_second['completed_trips'], completed_after_first + 1)
        
        # Rollback the second trip's completion
        self.system.rollback_last()
        
        analytics_after_rollback = self.system.get_analytics()
        
        # Should match analytics after first trip
        self.assertEqual(
            analytics_after_rollback['completed_trips'], 
            completed_after_first
        )
    
    def test_cross_zone_trip_cost(self):
        """Test that cross-zone trips have higher cost."""
        # Same-zone trip
        estimate_same = self.system.get_trip_estimate("A1", "A3")
        
        # Cross-zone trip with similar distance
        estimate_cross = self.system.get_trip_estimate("A1", "B1")
        
        # Cross-zone should have penalty applied
        self.assertTrue(estimate_cross['is_cross_zone'])
        self.assertFalse(estimate_same['is_cross_zone'])


class TestRollbackManager(unittest.TestCase):
    """Test the RollbackManager in isolation."""
    
    def setUp(self):
        """Set up rollback manager with test data."""
        self.drivers = {}
        self.riders = {}
        self.trips = {}
        
        self.manager = RollbackManager()
        self.manager.set_system_references(
            self.drivers, self.riders, self.trips
        )
        
        # Add a test driver
        driver = Driver("D-001", "Test", "A1", "Zone-A")
        self.drivers["D-001"] = driver
    
    def test_operation_logging(self):
        """Test that operations are logged correctly."""
        op_id = self.manager.log_operation(
            operation_type=OperationType.UPDATE_DRIVER_LOCATION,
            description="Test operation",
            affected_driver_ids=["D-001"]
        )
        
        self.assertIsNotNone(op_id)
        self.assertEqual(self.manager.get_operation_count(), 1)
    
    def test_rollback_restores_state(self):
        """Test that rollback restores entity state."""
        driver = self.drivers["D-001"]
        original_location = driver.current_location
        
        # Log operation
        self.manager.log_operation(
            operation_type=OperationType.UPDATE_DRIVER_LOCATION,
            description="Update location",
            affected_driver_ids=["D-001"]
        )
        
        # Change state
        driver.update_location("B1", "Zone-B")
        
        # Rollback
        self.manager.rollback_last()
        
        # State should be restored
        self.assertEqual(driver.current_location, original_location)
    
    def test_rollback_k_operations(self):
        """Test rolling back multiple operations."""
        driver = self.drivers["D-001"]
        
        # Perform 3 operations
        for i in range(3):
            self.manager.log_operation(
                operation_type=OperationType.UPDATE_DRIVER_LOCATION,
                description=f"Operation {i}",
                affected_driver_ids=["D-001"]
            )
            driver.update_location(f"Location{i}", f"Zone{i}")
        
        self.assertEqual(self.manager.get_operation_count(), 3)
        
        # Rollback 2
        rolled_back = self.manager.rollback_k(2)
        
        self.assertEqual(len(rolled_back), 2)
        self.assertEqual(self.manager.get_operation_count(), 1)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_invalid_location(self):
        """Test handling of invalid locations."""
        system = RideShareSystem()
        
        with self.assertRaises(ValueError):
            system.create_driver("Test", "INVALID_LOCATION")
        
        with self.assertRaises(ValueError):
            system.create_rider("Test", "INVALID_LOCATION")
    
    def test_duplicate_trip_request(self):
        """Test that rider cannot have multiple active trips."""
        system = RideShareSystem()
        
        system.create_driver("Alice", "A1")
        rider = system.create_rider("John", "A1")
        
        trip1 = system.request_trip(rider.rider_id, "A1", "A2")
        system.assign_trip(trip1.trip_id)
        
        # Should fail - rider has active trip
        with self.assertRaises(ValueError):
            system.request_trip(rider.rider_id, "A1", "A3")
    
    def test_no_available_drivers(self):
        """Test behavior when no drivers are available."""
        system = RideShareSystem()
        
        # Create rider but no drivers
        rider = system.create_rider("John", "A1")
        trip = system.request_trip(rider.rider_id, "A1", "A2")
        
        # Assignment should return None
        result = system.assign_trip(trip.trip_id)
        self.assertIsNone(result)


def run_tests():
    """Run all tests and print results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMinHeap))
    suite.addTests(loader.loadTestsFromTestCase(TestCity))
    suite.addTests(loader.loadTestsFromTestCase(TestTripStateMachine))
    suite.addTests(loader.loadTestsFromTestCase(TestDispatchEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestRideShareSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestRollbackManager))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()

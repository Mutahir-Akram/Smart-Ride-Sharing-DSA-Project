# Ride-Sharing Dispatch & Trip Management System - Design Document

## 1. Overview

This document describes the design and implementation of a ride-sharing system similar to Uber or Careem. The system manages drivers, riders, and trips using custom data structures without relying on STL containers for core logic.

## 2. Graph Representation and Routing Approach

### 2.1 City Graph Structure

The city is represented as a **weighted undirected graph** using an **adjacency list** representation:

```
Location (Vertex):
+----+-------+--------+-----+-----+----------+
| id | name  | zoneId |  x  |  y  | isActive |
+----+-------+--------+-----+-----+----------+

Edge:
+---------------+----------+------+
| destinationId | distance | next |
+---------------+----------+------+
```

**Why Adjacency List?**
- Memory efficient for sparse graphs (typical city road networks)
- O(V + E) space complexity vs O(V²) for adjacency matrix
- Efficient iteration over neighbors for Dijkstra's algorithm

### 2.2 Zone Partitioning

The city is divided into zones for efficient driver dispatch:
- Each location belongs to exactly one zone
- Zones are identified by integer IDs
- Zone information is stored directly in the Location structure

### 2.3 Shortest Path Algorithm: Dijkstra's Algorithm

**Implementation:**
```cpp
dijkstra(sourceId):
    1. Initialize distances[] = INFINITY for all vertices
    2. Set distances[source] = 0
    3. Insert source into min-heap priority queue
    4. While priority queue is not empty:
        a. Extract minimum distance vertex u
        b. For each neighbor v of u:
            - If distances[u] + weight(u,v) < distances[v]:
                - Update distances[v]
                - Update priority in heap (or insert)
    5. Return distances array
```

**Time Complexity:** O((V + E) log V)
- Each vertex extracted once: O(V log V)
- Each edge relaxed once with heap update: O(E log V)

**Space Complexity:** O(V)
- distances array: O(V)
- visited array: O(V)
- priority queue: O(V)
- predecessors array (for path reconstruction): O(V)

### 2.4 Custom Priority Queue (Min-Heap)

```cpp
PriorityQueue:
- heap[]: Array of HeapNode (nodeId, priority)
- nodePositions[]: Maps nodeId to heap position for O(1) lookup
- Operations:
  - insert(nodeId, priority): O(log n)
  - extractMin(): O(log n)
  - decreaseKey(nodeId, newPriority): O(log n)
```

## 3. Trip State Machine Design

### 3.1 States

| State | Description |
|-------|-------------|
| REQUESTED | Trip created by rider, awaiting driver assignment |
| ASSIGNED | Driver assigned, en route to pickup location |
| ONGOING | Rider picked up, trip in progress |
| COMPLETED | Trip finished successfully (terminal) |
| CANCELLED | Trip cancelled (terminal) |

### 3.2 State Transition Diagram

```
                    +------------+
                    |  REQUESTED |
                    +-----+------+
                          |
           +--------------+--------------+
           |                             |
           v                             v
    +------+------+               +------+------+
    |   ASSIGNED  |               |  CANCELLED  |
    +------+------+               +-------------+
           |
     +-----+-----+
     |           |
     v           v
+----+----+  +---+-------+
| ONGOING |  | CANCELLED |
+----+----+  +-----------+
     |
     v
+----+-----+
| COMPLETED |
+-----------+
```

### 3.3 Transition Validation

```cpp
isValidTransition(TripState current, TripState target):
    switch(current):
        case REQUESTED: return target == ASSIGNED || target == CANCELLED
        case ASSIGNED:  return target == ONGOING || target == CANCELLED
        case ONGOING:   return target == COMPLETED
        case COMPLETED: return false  // terminal
        case CANCELLED: return false  // terminal
```

**Time Complexity:** O(1) for state transition validation and execution

## 4. Rollback Strategy

### 4.1 Command Pattern Implementation

Each operation is recorded with sufficient information to reverse it:

```cpp
struct Operation {
    OperationType type;      // Type of operation
    int tripId;              // Affected trip
    TripState previousState; // State before operation
    int driverId;            // Affected driver
    bool wasDriverAvailable; // Driver state before operation
    int riderId;             // Affected rider
    long timestamp;          // When operation occurred
};
```

### 4.2 Operation Types

| Operation | Rollback Action |
|-----------|----------------|
| TRIP_CREATED | Mark trip cancelled, clear rider's current trip |
| TRIP_ASSIGNED | Restore trip to REQUESTED, restore driver availability |
| TRIP_STARTED | Restore trip to ASSIGNED |
| TRIP_COMPLETED | Cannot rollback (business rule) |
| TRIP_CANCELLED | Restore previous state, restore driver if was assigned |
| DRIVER_REGISTERED | Remove driver from system |
| RIDER_REGISTERED | Remove rider from system |

### 4.3 Stack-Based History

```cpp
RollbackManager:
- operationStack[]: Array-based stack of Operations
- stackTop: Index of top element

rollbackLast():
    1. Pop operation from stack
    2. Based on operation type, call appropriate restore function
    3. Return success/failure

rollbackK(k):
    for i = 1 to k:
        if not rollbackLast(): return false
    return true
```

### 4.4 Rollback Constraints

- **Completed trips cannot be rolled back** (business rule - payment processed)
- **Ongoing trips can be rolled back** to ASSIGNED state
- **Rollback is LIFO** - operations must be undone in reverse order

**Time Complexity:** O(1) per rollback operation
**Space Complexity:** O(n) where n = number of recorded operations

## 5. Dispatch Strategy

### 5.1 Zone-Based Assignment

```cpp
findNearestDriver(pickupLocation):
    pickupZone = getZone(pickupLocation)

    // Phase 1: Search same zone
    for each available driver:
        if driver.zone == pickupZone:
            distance = dijkstra(driver.location, pickupLocation)
            if distance < minCost:
                minCost = distance
                bestDriver = driver

    // Phase 2: If no same-zone driver, search all zones
    if bestDriver == null:
        for each available driver:
            distance = dijkstra(driver.location, pickupLocation)
            cost = distance + CROSS_ZONE_PENALTY
            if cost < minCost:
                minCost = cost
                bestDriver = driver

    return bestDriver
```

### 5.2 Cost Calculation

```
Cost = Distance + (isCrossZone ? CROSS_ZONE_PENALTY : 0)

where:
  CROSS_ZONE_PENALTY = 5.0 units
  Distance = Dijkstra's shortest path distance
```

**Time Complexity:** O(D × (V + E) log V) where D = number of drivers
- Each driver requires a Dijkstra computation

## 6. Data Structures Summary

### 6.1 Custom Data Structures

| Structure | Purpose | Key Operations |
|-----------|---------|---------------|
| ArrayList<T> | Dynamic array | add: O(1)*, get: O(1), remove: O(n) |
| Stack<T> | Rollback history | push: O(1), pop: O(1), peek: O(1) |
| PriorityQueue | Dijkstra's algorithm | insert: O(log n), extractMin: O(log n) |
| HashMap<K,V> | Entity lookups | put: O(1)*, get: O(1)*, remove: O(1)* |

*Amortized

### 6.2 Entity Classes

| Class | Description |
|-------|-------------|
| Location | Graph vertex with zone info |
| Edge | Graph edge with weight |
| City | Graph manager with Dijkstra |
| Driver | Driver entity with availability |
| Rider | Rider entity with trip reference |
| Trip | Trip with state machine |
| DispatchEngine | Driver assignment logic |
| RollbackManager | Operation history and undo |
| RideShareSystem | Main orchestrator |

## 7. Complexity Analysis

### 7.1 Time Complexity

| Operation | Complexity |
|-----------|------------|
| Add location | O(1)* |
| Add road | O(1) |
| Shortest path query | O((V + E) log V) |
| Register driver/rider | O(1)* |
| Request trip | O(1)* |
| Assign trip (auto) | O(D × (V + E) log V) |
| Start/Complete/Cancel trip | O(1) |
| Rollback operation | O(1) |
| Get analytics | O(T) where T = total trips |

*Amortized, may require array resize

### 7.2 Space Complexity

| Component | Complexity |
|-----------|------------|
| City graph | O(V + E) |
| Drivers array | O(D) |
| Riders array | O(R) |
| Trips array | O(T) |
| Rollback stack | O(O) where O = operations |
| **Total** | O(V + E + D + R + T + O) |

## 8. File Structure

```
sufyan_project/
├── ArrayList.h / .cpp       # Dynamic array template
├── Stack.h / .cpp           # Stack for rollback
├── PriorityQueue.h / .cpp   # Min-heap for Dijkstra
├── HashMap.h / .cpp         # Hash map for lookups
├── City.h / .cpp            # Graph and routing
├── Driver.h / .cpp          # Driver entity
├── Rider.h / .cpp           # Rider entity
├── Trip.h / .cpp            # Trip state machine
├── DispatchEngine.h / .cpp  # Driver assignment
├── RollbackManager.h / .cpp # Undo operations
├── RideShareSystem.h / .cpp # Main orchestrator
├── main.cpp                 # Entry point and tests
├── design.md                # This document
└── Makefile                 # Build configuration
```

## 9. Testing Strategy

The system includes 12 test cases covering:

1. **Shortest Path Correctness** - Dijkstra's algorithm accuracy
2. **Zone Assignment** - Correct zone-based driver selection
3. **Complete Trip Lifecycle** - Full state machine traversal
4. **Invalid State Transitions** - Rejection of invalid operations
5. **Cancellation Restores Driver** - Proper state restoration
6. **Single Rollback** - Undo last operation
7. **Multiple Rollback** - Undo k operations
8. **Driver Reassignment** - Reuse of freed drivers
9. **Cross-Zone Assignment** - Fallback to other zones
10. **Average Distance Analytics** - Correct calculation
11. **Driver Utilization** - Correct utilization metric
12. **Analytics After Rollback** - Consistency after undo

## 10. Limitations and Future Improvements

### Current Limitations
- Driver search is O(D × shortest_path) - could be optimized with spatial indexing
- No persistent storage - all data is in-memory
- Single-threaded - no concurrent operation support

### Potential Improvements
- Add R-tree or quadtree for faster spatial queries
- Implement A* algorithm for faster single-source single-target queries
- Add database persistence
- Implement concurrent operation support

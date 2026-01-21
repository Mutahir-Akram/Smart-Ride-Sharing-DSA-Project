# Ride-Share Dispatch System - Design Document

## 1. Graph Representation & Routing Approach

### City Graph Structure

The city is represented as a **weighted undirected graph** using a custom adjacency list structure:

```
City
├── _nodes: Dict[str, Node]        # node_id -> Node object
├── _adjacency: Dict[str, List[Tuple[str, float]]]  # node_id -> [(neighbor_id, distance)]
├── _zones: Dict[str, List[str]]   # zone_name -> [node_ids]
└── _edges: List[Edge]             # All edges for visualization
```

**Key Design Decisions:**

1. **No Built-in Graph Libraries**: All graph operations use custom data structures
2. **Zone-Based Organization**: Nodes are grouped into zones for locality-aware dispatching
3. **Bidirectional Edges**: Roads are traversable in both directions by default
4. **Coordinate System**: Nodes have (x, y) coordinates for visualization

### Shortest Path Algorithm

**Dijkstra's Algorithm** is implemented from scratch with a custom min-heap:

```python
class MinHeap:
    - _heap: List[Tuple[float, str]]  # (distance, node_id)
    - _positions: Dict[str, int]       # node_id -> heap index
    
    Operations:
    - insert(distance, node_id): O(log n)
    - extract_min(): O(log n)
    - decrease_key(node_id, new_distance): O(log n)
```

**Algorithm Complexity:**
- Time: O((V + E) log V) where V = nodes, E = edges
- Space: O(V) for distances, predecessors, and heap

### Zone System

Zones enable locality-aware driver assignment:
- Drivers preferentially serve trips in their zone
- Cross-zone assignments incur a 1.5x penalty multiplier
- Zone statistics track driver distribution

---

## 2. Trip State Machine Design

### State Diagram

```
                    ┌─────────────┐
                    │  REQUESTED  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            │
       ┌──────────┐  ┌──────────┐      │
       │ ASSIGNED │  │CANCELLED │◄─────┘
       └────┬─────┘  └──────────┘
            │              ▲
            ▼              │
       ┌──────────┐        │
       │ ONGOING  │────────┘ (not allowed)
       └────┬─────┘
            │
            ▼
       ┌──────────┐
       │COMPLETED │
       └──────────┘
```

### Valid Transitions

| Current State | Valid Next States |
|---------------|-------------------|
| REQUESTED | ASSIGNED, CANCELLED |
| ASSIGNED | ONGOING, CANCELLED |
| ONGOING | COMPLETED |
| COMPLETED | (terminal) |
| CANCELLED | (terminal) |

### Implementation

```python
class Trip:
    VALID_TRANSITIONS = {
        TripState.REQUESTED: [TripState.ASSIGNED, TripState.CANCELLED],
        TripState.ASSIGNED: [TripState.ONGOING, TripState.CANCELLED],
        TripState.ONGOING: [TripState.COMPLETED],
        TripState.COMPLETED: [],
        TripState.CANCELLED: [],
    }
    
    def _transition(self, new_state):
        if not self.can_transition_to(new_state):
            raise InvalidStateTransitionError(...)
        self.state = new_state
        self.state_history.append((new_state, datetime.now()))
```

**Design Principles:**
1. All transitions are validated before execution
2. State history is maintained for auditing
3. Invalid transitions raise explicit exceptions
4. Terminal states (COMPLETED, CANCELLED) cannot transition

---

## 3. Rollback Strategy & Data Structures

### Architecture Overview

The rollback system uses the **Command Pattern** with snapshots:

```
RollbackManager
├── _operation_stack: OperationStack  # Custom stack implementation
├── _drivers: Dict[str, Driver]       # Reference to system data
├── _riders: Dict[str, Rider]
└── _trips: Dict[str, Trip]
```

### Operation Stack

```python
class OperationStack:
    _stack: List[Operation]  # LIFO structure
    _max_size: int          # Prevents unbounded growth
    
    Operations:
    - push(operation): O(1)
    - pop(): O(1)
    - peek(): O(1)
```

### Snapshot System

Each operation captures a `SystemSnapshot` BEFORE execution:

```python
@dataclass
class SystemSnapshot:
    driver_snapshots: Dict[str, DriverSnapshot]
    rider_snapshots: Dict[str, RiderSnapshot]
    trip_snapshots: Dict[str, TripSnapshot]
    existing_driver_ids: List[str]  # Track entity existence
    existing_rider_ids: List[str]
    existing_trip_ids: List[str]
```

### Rollback Process

1. **Pop** operation from stack
2. **Identify** affected entities
3. **Restore** entity states from snapshots
4. **Handle creation rollbacks** by deleting created entities
5. **Restore deleted entities** if they existed before

```python
def rollback_last(self):
    operation = self._operation_stack.pop()
    
    # Delete created entities
    if operation.created_entity_id:
        del self._entities[operation.created_entity_id]
    
    # Restore snapshots
    for entity_id, snapshot in operation.before_snapshot.items():
        self._entities[entity_id].restore_from_snapshot(snapshot)
```

### Supported Rollback Operations

| Operation Type | Rollback Action |
|----------------|-----------------|
| CREATE_DRIVER | Delete driver |
| CREATE_RIDER | Delete rider |
| REQUEST_TRIP | Delete trip, restore rider state |
| ASSIGN_TRIP | Restore driver/trip to pre-assignment |
| START_TRIP | Restore trip to ASSIGNED state |
| COMPLETE_TRIP | Restore trip/driver/rider states |
| CANCEL_TRIP | Restore trip/driver states |

---

## 4. Time & Space Complexity Analysis

### City Operations

| Operation | Time | Space |
|-----------|------|-------|
| add_node | O(1) | O(1) |
| add_edge | O(1) | O(1) |
| shortest_path | O((V+E) log V) | O(V) |
| get_nodes_in_zone | O(1) | O(1) |

### Trip Operations

| Operation | Time | Space |
|-----------|------|-------|
| request_trip | O(1) + snapshot | O(S) |
| assign_trip | O((V+E) log V) | O(V) |
| start_trip | O(1) | O(S) |
| complete_trip | O(1) | O(S) |
| cancel_trip | O(1) | O(S) |

Where S = snapshot size (proportional to affected entities)

### Rollback Operations

| Operation | Time | Space |
|-----------|------|-------|
| log_operation | O(A) | O(A) |
| rollback_last | O(A) | O(1) |
| rollback_k | O(K × A) | O(1) |

Where A = number of affected entities in snapshot

### Space Usage

- **Operation Stack**: O(M × A) where M = max operations, A = avg entities per operation
- **Entity Storage**: O(D + R + T) for drivers, riders, trips
- **City Graph**: O(V + E) for nodes and edges

---

## 5. Design Decisions & Trade-offs

### 1. In-Memory vs. Persistent Storage

**Decision**: Pure in-memory storage

**Trade-offs**:
- (+) Simpler implementation, no database dependencies
- (+) Fast operations, no I/O latency
- (-) Data lost on restart
- (-) Limited by available memory

### 2. Full Snapshots vs. Delta Encoding

**Decision**: Full snapshots of affected entities

**Trade-offs**:
- (+) Simple rollback logic
- (+) Complete state restoration
- (-) Higher memory usage
- (-) Redundant data storage

**Mitigation**: Limit operation history (default: 100 operations)

### 3. Eager vs. Lazy Driver Assignment

**Decision**: Lazy assignment (manual trigger)

**Trade-offs**:
- (+) UI control over when assignment happens
- (+) Allows trip estimates before commitment
- (-) Two-step process (request → assign)

### 4. Single vs. Composite Operations

**Decision**: Each action is a separate operation

**Trade-offs**:
- (+) Fine-grained rollback control
- (+) Clear operation history
- (-) Multiple rollbacks needed for compound actions

### 5. Zone Penalty Approach

**Decision**: Cost multiplier (1.5x) for cross-zone trips

**Trade-offs**:
- (+) Encourages local service
- (+) Compensates drivers for longer travel
- (-) May make cross-zone trips expensive

### 6. Custom Data Structures

**Decision**: No built-in collections for core graph/heap

**Trade-offs**:
- (+) Full control over implementation
- (+) Educational value
- (+) No external dependencies
- (-) More code to maintain
- (-) Potentially less optimized than stdlib

---

## 6. File Structure

```
backend/
├── City.py           # Graph representation, routing
├── Driver.py         # Driver entity, snapshots
├── Rider.py          # Rider entity, snapshots
├── Trip.py           # Trip entity, state machine
├── DispatchEngine.py # Driver assignment logic
├── RollbackManager.py # Operation logging, rollback
├── RideShareSystem.py # Main facade, analytics
├── main.py           # Demo script
├── tests.py          # Automated test suite
└── design.md         # This document
```

---

## 7. Testing Coverage

The test suite covers all 10 required scenarios:

1. **Shortest path correctness** - Verifies Dijkstra implementation
2. **Zone-based driver assignment** - Same-zone preference
3. **Cross-zone assignment penalty** - Penalty application
4. **Driver reassignment after cancellation** - Availability restoration
5. **Multiple rollbacks** - K-operation rollback
6. **Invalid state transition handling** - Exception throwing
7. **Rollback after cancellation** - State restoration
8. **Rollback after completion** - Metric restoration
9. **Analytics correctness** - Calculation verification
10. **Analytics after rollback** - Post-rollback accuracy

---

## 8. GUI Architecture

The Next.js GUI provides:

- **City Map Visualization**: Interactive SVG graph with zone coloring
- **Trip Management**: Request, assign, start, complete, cancel
- **Driver/Rider Management**: Create and view entities
- **Analytics Dashboard**: Real-time metrics and charts
- **Operations Panel**: History and rollback controls

Communication uses a TypeScript port of the core system logic for client-side execution.

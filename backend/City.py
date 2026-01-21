"""
City.py - Graph-based city representation for ride-sharing system.

This module implements a weighted graph representing the city map with:
- Custom adjacency list structure (no built-in graph libraries)
- Zone/sector division
- Dijkstra's shortest path algorithm from scratch
"""

from typing import Dict, List, Tuple, Optional
import math


class MinHeap:
    """
    Custom min-heap implementation for Dijkstra's algorithm.
    Stores (distance, node_id) tuples and extracts minimum distance.
    """
    
    def __init__(self):
        self._heap: List[Tuple[float, str]] = []
        self._positions: Dict[str, int] = {}  # Track node positions for decrease-key
    
    def is_empty(self) -> bool:
        return len(self._heap) == 0
    
    def _parent(self, i: int) -> int:
        return (i - 1) // 2
    
    def _left_child(self, i: int) -> int:
        return 2 * i + 1
    
    def _right_child(self, i: int) -> int:
        return 2 * i + 2
    
    def _swap(self, i: int, j: int) -> None:
        """Swap elements and update position tracking."""
        self._positions[self._heap[i][1]] = j
        self._positions[self._heap[j][1]] = i
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]
    
    def _heapify_up(self, i: int) -> None:
        """Restore heap property upward from index i."""
        while i > 0 and self._heap[i][0] < self._heap[self._parent(i)][0]:
            self._swap(i, self._parent(i))
            i = self._parent(i)
    
    def _heapify_down(self, i: int) -> None:
        """Restore heap property downward from index i."""
        smallest = i
        left = self._left_child(i)
        right = self._right_child(i)
        
        if left < len(self._heap) and self._heap[left][0] < self._heap[smallest][0]:
            smallest = left
        if right < len(self._heap) and self._heap[right][0] < self._heap[smallest][0]:
            smallest = right
        
        if smallest != i:
            self._swap(i, smallest)
            self._heapify_down(smallest)
    
    def insert(self, distance: float, node_id: str) -> None:
        """Insert a new (distance, node) pair into the heap."""
        self._heap.append((distance, node_id))
        self._positions[node_id] = len(self._heap) - 1
        self._heapify_up(len(self._heap) - 1)
    
    def extract_min(self) -> Tuple[float, str]:
        """Remove and return the minimum distance element."""
        if self.is_empty():
            raise IndexError("Heap is empty")
        
        min_elem = self._heap[0]
        del self._positions[min_elem[1]]
        
        if len(self._heap) > 1:
            self._heap[0] = self._heap.pop()
            self._positions[self._heap[0][1]] = 0
            self._heapify_down(0)
        else:
            self._heap.pop()
        
        return min_elem
    
    def decrease_key(self, node_id: str, new_distance: float) -> None:
        """Decrease the distance value for a given node."""
        if node_id not in self._positions:
            return
        
        i = self._positions[node_id]
        if new_distance < self._heap[i][0]:
            self._heap[i] = (new_distance, node_id)
            self._heapify_up(i)
    
    def contains(self, node_id: str) -> bool:
        """Check if node is in the heap."""
        return node_id in self._positions


class Node:
    """
    Represents a location/intersection in the city.
    """
    
    def __init__(self, node_id: str, name: str, zone: str, x: float = 0, y: float = 0):
        self.node_id = node_id
        self.name = name
        self.zone = zone  # Zone/sector this node belongs to
        self.x = x  # X coordinate for visualization
        self.y = y  # Y coordinate for visualization
    
    def to_dict(self) -> dict:
        """Convert node to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "name": self.name,
            "zone": self.zone,
            "x": self.x,
            "y": self.y
        }


class Edge:
    """
    Represents a road between two locations.
    """
    
    def __init__(self, from_node: str, to_node: str, distance: float):
        self.from_node = from_node
        self.to_node = to_node
        self.distance = distance
    
    def to_dict(self) -> dict:
        """Convert edge to dictionary for serialization."""
        return {
            "from_node": self.from_node,
            "to_node": self.to_node,
            "distance": self.distance
        }


class City:
    """
    Weighted graph representing the city map.
    
    Uses custom adjacency list structure without built-in graph libraries.
    Supports zone-based organization and shortest path computation.
    """
    
    def __init__(self, name: str = "Default City"):
        self.name = name
        # Custom adjacency list: node_id -> list of (neighbor_id, distance)
        self._adjacency: Dict[str, List[Tuple[str, float]]] = {}
        # Node storage: node_id -> Node object
        self._nodes: Dict[str, Node] = {}
        # Zone mapping: zone_name -> list of node_ids
        self._zones: Dict[str, List[str]] = {}
        # Edge list for visualization
        self._edges: List[Edge] = []
    
    def add_node(self, node_id: str, name: str, zone: str, x: float = 0, y: float = 0) -> Node:
        """
        Add a location/intersection to the city.
        
        Args:
            node_id: Unique identifier for the node
            name: Human-readable name
            zone: Zone/sector the node belongs to
            x, y: Coordinates for visualization
        
        Returns:
            The created Node object
        """
        if node_id in self._nodes:
            raise ValueError(f"Node {node_id} already exists")
        
        node = Node(node_id, name, zone, x, y)
        self._nodes[node_id] = node
        self._adjacency[node_id] = []
        
        # Add to zone mapping
        if zone not in self._zones:
            self._zones[zone] = []
        self._zones[zone].append(node_id)
        
        return node
    
    def add_edge(self, from_node: str, to_node: str, distance: float, bidirectional: bool = True) -> None:
        """
        Add a road between two locations.
        
        Args:
            from_node: Source node ID
            to_node: Destination node ID
            distance: Road distance/weight
            bidirectional: If True, add edge in both directions
        """
        if from_node not in self._nodes:
            raise ValueError(f"Node {from_node} does not exist")
        if to_node not in self._nodes:
            raise ValueError(f"Node {to_node} does not exist")
        if distance < 0:
            raise ValueError("Distance cannot be negative")
        
        self._adjacency[from_node].append((to_node, distance))
        self._edges.append(Edge(from_node, to_node, distance))
        
        if bidirectional:
            self._adjacency[to_node].append((from_node, distance))
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self._nodes.get(node_id)
    
    def get_zone(self, node_id: str) -> Optional[str]:
        """Get the zone of a node."""
        node = self._nodes.get(node_id)
        return node.zone if node else None
    
    def get_nodes_in_zone(self, zone: str) -> List[str]:
        """Get all node IDs in a zone."""
        return self._zones.get(zone, [])
    
    def get_all_zones(self) -> List[str]:
        """Get all zone names."""
        return list(self._zones.keys())
    
    def get_all_nodes(self) -> List[Node]:
        """Get all nodes in the city."""
        return list(self._nodes.values())
    
    def get_all_edges(self) -> List[Edge]:
        """Get all edges in the city."""
        return self._edges
    
    def get_neighbors(self, node_id: str) -> List[Tuple[str, float]]:
        """Get all neighbors of a node with distances."""
        return self._adjacency.get(node_id, [])
    
    def shortest_path(self, start: str, end: str) -> Tuple[List[str], float]:
        """
        Find the shortest path between two nodes using Dijkstra's algorithm.
        Implemented from scratch without external libraries.
        
        Args:
            start: Starting node ID
            end: Ending node ID
        
        Returns:
            Tuple of (path as list of node IDs, total distance)
            Returns ([], infinity) if no path exists
        """
        if start not in self._nodes:
            raise ValueError(f"Start node {start} does not exist")
        if end not in self._nodes:
            raise ValueError(f"End node {end} does not exist")
        
        # Initialize distances and predecessors
        distances: Dict[str, float] = {}
        predecessors: Dict[str, Optional[str]] = {}
        visited: Dict[str, bool] = {}
        
        for node_id in self._nodes:
            distances[node_id] = math.inf
            predecessors[node_id] = None
            visited[node_id] = False
        
        distances[start] = 0
        
        # Use custom min-heap for efficient extraction
        heap = MinHeap()
        heap.insert(0, start)
        
        while not heap.is_empty():
            current_dist, current_node = heap.extract_min()
            
            if visited[current_node]:
                continue
            
            visited[current_node] = True
            
            # Early termination if we reached the destination
            if current_node == end:
                break
            
            # Relax all edges from current node
            for neighbor, edge_weight in self._adjacency[current_node]:
                if visited[neighbor]:
                    continue
                
                new_dist = current_dist + edge_weight
                
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    predecessors[neighbor] = current_node
                    
                    if heap.contains(neighbor):
                        heap.decrease_key(neighbor, new_dist)
                    else:
                        heap.insert(new_dist, neighbor)
        
        # Reconstruct path
        if distances[end] == math.inf:
            return [], math.inf
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = predecessors[current]
        
        path.reverse()
        return path, distances[end]
    
    def calculate_distance(self, start: str, end: str) -> float:
        """
        Calculate the shortest distance between two nodes.
        
        Returns:
            Distance value, or infinity if no path exists
        """
        _, distance = self.shortest_path(start, end)
        return distance
    
    def to_dict(self) -> dict:
        """Convert city to dictionary for serialization."""
        return {
            "name": self.name,
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges],
            "zones": self._zones
        }
    
    @classmethod
    def create_sample_city(cls) -> 'City':
        """
        Create a sample city with multiple zones for testing.
        
        Layout:
        Zone A (North): A1, A2, A3
        Zone B (South): B1, B2, B3
        Zone C (East): C1, C2
        """
        city = cls("Sample City")
        
        # Zone A - North area
        city.add_node("A1", "North Station", "Zone-A", 100, 50)
        city.add_node("A2", "North Mall", "Zone-A", 200, 50)
        city.add_node("A3", "North Park", "Zone-A", 300, 100)
        
        # Zone B - South area
        city.add_node("B1", "South Station", "Zone-B", 100, 300)
        city.add_node("B2", "South Mall", "Zone-B", 200, 300)
        city.add_node("B3", "South Park", "Zone-B", 300, 250)
        
        # Zone C - East area
        city.add_node("C1", "East Hub", "Zone-C", 400, 150)
        city.add_node("C2", "East Center", "Zone-C", 400, 250)
        
        # Central connector
        city.add_node("M1", "Central Hub", "Zone-M", 250, 175)
        
        # Edges within Zone A
        city.add_edge("A1", "A2", 5.0)
        city.add_edge("A2", "A3", 6.0)
        city.add_edge("A1", "A3", 10.0)
        
        # Edges within Zone B
        city.add_edge("B1", "B2", 5.0)
        city.add_edge("B2", "B3", 4.0)
        city.add_edge("B1", "B3", 8.0)
        
        # Edges within Zone C
        city.add_edge("C1", "C2", 6.0)
        
        # Cross-zone connections via central hub
        city.add_edge("A2", "M1", 7.0)
        city.add_edge("B2", "M1", 7.0)
        city.add_edge("M1", "C1", 8.0)
        city.add_edge("A3", "C1", 6.0)
        city.add_edge("B3", "C2", 5.0)
        
        return city

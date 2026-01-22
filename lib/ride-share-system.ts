/**
 * In-memory ride-sharing system implementation in TypeScript.
 * This mirrors the Python backend for the GUI to use directly.
 */

// ==================== Types ====================

export interface Node {
  nodeId: string;
  name: string;
  zone: string;
  x: number;
  y: number;
}

export interface Edge {
  fromNode: string;
  toNode: string;
  distance: number;
}

export type DriverStatus = "available" | "busy" | "offline";

export interface Driver {
  driverId: string;
  name: string;
  currentLocation: string;
  zone: string;
  status: DriverStatus;
  totalTrips: number;
  totalDistance: number;
  activeTime: number;
  idleTime: number;
  currentTripId: string | null;
}

export interface Rider {
  riderId: string;
  name: string;
  currentLocation: string;
  tripHistory: string[];
  currentTripId: string | null;
  totalTrips: number;
  totalDistance: number;
  totalSpent: number;
}

export type TripState =
  | "requested"
  | "assigned"
  | "ongoing"
  | "completed"
  | "cancelled";

export interface Trip {
  tripId: string;
  riderId: string;
  driverId: string | null;
  pickupLocation: string;
  dropoffLocation: string;
  pickupZone: string;
  dropoffZone: string;
  state: TripState;
  distance: number;
  estimatedDuration: number;
  actualDuration: number;
  cost: number;
  path: string[];
  isCrossZone: boolean;
  createdAt: Date;
  assignedAt: Date | null;
  startedAt: Date | null;
  completedAt: Date | null;
  cancelledAt: Date | null;
}

export interface TripEstimate {
  distance: number;
  estimatedDuration: number;
  cost: number;
  isCrossZone: boolean;
  path: string[];
  driverAvailable: boolean;
  driverEta: number | null;
}

export interface Analytics {
  totalTrips: number;
  completedTrips: number;
  cancelledTrips: number;
  activeTrips: number;
  completionRate: number;
  cancellationRate: number;
  averageTripDistance: number;
  totalDistanceCovered: number;
  averageDriverUtilization: number;
  totalDrivers: number;
  availableDrivers: number;
  busyDrivers: number;
  totalRevenue: number;
  crossZoneTrips: number;
  crossZonePercentage: number;
  totalRiders: number;
  zoneStatistics: Record<
    string,
    { totalDrivers: number; available: number; busy: number; offline: number }
  >;
}

export interface Operation {
  operationId: string;
  operationType: string;
  timestamp: string;
  description: string;
}

// ==================== Min Heap ====================

class MinHeap {
  private heap: [number, string][] = [];
  private positions: Map<string, number> = new Map();

  isEmpty(): boolean {
    return this.heap.length === 0;
  }

  private parent(i: number): number {
    return Math.floor((i - 1) / 2);
  }

  private leftChild(i: number): number {
    return 2 * i + 1;
  }

  private rightChild(i: number): number {
    return 2 * i + 2;
  }

  private swap(i: number, j: number): void {
    this.positions.set(this.heap[i][1], j);
    this.positions.set(this.heap[j][1], i);
    [this.heap[i], this.heap[j]] = [this.heap[j], this.heap[i]];
  }

  private heapifyUp(i: number): void {
    while (i > 0 && this.heap[i][0] < this.heap[this.parent(i)][0]) {
      this.swap(i, this.parent(i));
      i = this.parent(i);
    }
  }

  private heapifyDown(i: number): void {
    let smallest = i;
    const left = this.leftChild(i);
    const right = this.rightChild(i);

    if (left < this.heap.length && this.heap[left][0] < this.heap[smallest][0]) {
      smallest = left;
    }
    if (
      right < this.heap.length &&
      this.heap[right][0] < this.heap[smallest][0]
    ) {
      smallest = right;
    }

    if (smallest !== i) {
      this.swap(i, smallest);
      this.heapifyDown(smallest);
    }
  }

  insert(distance: number, nodeId: string): void {
    this.heap.push([distance, nodeId]);
    this.positions.set(nodeId, this.heap.length - 1);
    this.heapifyUp(this.heap.length - 1);
  }

  extractMin(): [number, string] | null {
    if (this.isEmpty()) return null;

    const min = this.heap[0];
    this.positions.delete(min[1]);

    if (this.heap.length > 1) {
      this.heap[0] = this.heap.pop()!;
      this.positions.set(this.heap[0][1], 0);
      this.heapifyDown(0);
    } else {
      this.heap.pop();
    }

    return min;
  }

  decreaseKey(nodeId: string, newDistance: number): void {
    const i = this.positions.get(nodeId);
    if (i === undefined) return;

    if (newDistance < this.heap[i][0]) {
      this.heap[i] = [newDistance, nodeId];
      this.heapifyUp(i);
    }
  }

  contains(nodeId: string): boolean {
    return this.positions.has(nodeId);
  }
}

// ==================== City Graph ====================

class City {
  name: string;
  private adjacency: Map<string, [string, number][]> = new Map();
  private nodes: Map<string, Node> = new Map();
  private zones: Map<string, string[]> = new Map();
  private edges: Edge[] = [];

  constructor(name: string = "Default City") {
    this.name = name;
  }

  addNode(
    nodeId: string,
    name: string,
    zone: string,
    x: number = 0,
    y: number = 0
  ): Node {
    const node: Node = { nodeId, name, zone, x, y };
    this.nodes.set(nodeId, node);
    this.adjacency.set(nodeId, []);

    if (!this.zones.has(zone)) {
      this.zones.set(zone, []);
    }
    this.zones.get(zone)!.push(nodeId);

    return node;
  }

  addEdge(
    fromNode: string,
    toNode: string,
    distance: number,
    bidirectional: boolean = true
  ): void {
    this.adjacency.get(fromNode)!.push([toNode, distance]);
    this.edges.push({ fromNode, toNode, distance });

    if (bidirectional) {
      this.adjacency.get(toNode)!.push([fromNode, distance]);
    }
  }

  getNode(nodeId: string): Node | undefined {
    return this.nodes.get(nodeId);
  }

  getZone(nodeId: string): string | undefined {
    return this.nodes.get(nodeId)?.zone;
  }

  getNodesInZone(zone: string): string[] {
    return this.zones.get(zone) || [];
  }

  getAllZones(): string[] {
    return Array.from(this.zones.keys());
  }

  getAllNodes(): Node[] {
    return Array.from(this.nodes.values());
  }

  getAllEdges(): Edge[] {
    return this.edges;
  }

  shortestPath(start: string, end: string): [string[], number] {
    const distances: Map<string, number> = new Map();
    const predecessors: Map<string, string | null> = new Map();
    const visited: Set<string> = new Set();

    for (const nodeId of this.nodes.keys()) {
      distances.set(nodeId, Infinity);
      predecessors.set(nodeId, null);
    }

    distances.set(start, 0);
    const heap = new MinHeap();
    heap.insert(0, start);

    while (!heap.isEmpty()) {
      const result = heap.extractMin();
      if (!result) break;

      const [currentDist, currentNode] = result;

      if (visited.has(currentNode)) continue;
      visited.add(currentNode);

      if (currentNode === end) break;

      const neighbors = this.adjacency.get(currentNode) || [];
      for (const [neighbor, weight] of neighbors) {
        if (visited.has(neighbor)) continue;

        const newDist = currentDist + weight;

        if (newDist < distances.get(neighbor)!) {
          distances.set(neighbor, newDist);
          predecessors.set(neighbor, currentNode);

          if (heap.contains(neighbor)) {
            heap.decreaseKey(neighbor, newDist);
          } else {
            heap.insert(newDist, neighbor);
          }
        }
      }
    }

    const distance = distances.get(end)!;
    if (distance === Infinity) {
      return [[], Infinity];
    }

    const path: string[] = [];
    let current: string | null = end;
    while (current !== null) {
      path.unshift(current);
      current = predecessors.get(current) || null;
    }

    return [path, distance];
  }

  calculateDistance(start: string, end: string): number {
    const [, distance] = this.shortestPath(start, end);
    return distance;
  }

  static createSampleCity(): City {
    const city = new City("Sample City");

    // Zone A - North area
    city.addNode("A1", "North Station", "Zone-A", 100, 50);
    city.addNode("A2", "North Mall", "Zone-A", 200, 50);
    city.addNode("A3", "North Park", "Zone-A", 300, 100);

    // Zone B - South area
    city.addNode("B1", "South Station", "Zone-B", 100, 300);
    city.addNode("B2", "South Mall", "Zone-B", 200, 300);
    city.addNode("B3", "South Park", "Zone-B", 300, 250);

    // Zone C - East area
    city.addNode("C1", "East Hub", "Zone-C", 400, 150);
    city.addNode("C2", "East Center", "Zone-C", 400, 250);

    // Central connector
    city.addNode("M1", "Central Hub", "Zone-M", 250, 175);

    // Edges within Zone A
    city.addEdge("A1", "A2", 5.0);
    city.addEdge("A2", "A3", 6.0);
    city.addEdge("A1", "A3", 10.0);

    // Edges within Zone B
    city.addEdge("B1", "B2", 5.0);
    city.addEdge("B2", "B3", 4.0);
    city.addEdge("B1", "B3", 8.0);

    // Edges within Zone C
    city.addEdge("C1", "C2", 6.0);

    // Cross-zone connections
    city.addEdge("A2", "M1", 7.0);
    city.addEdge("B2", "M1", 7.0);
    city.addEdge("M1", "C1", 8.0);
    city.addEdge("A3", "C1", 6.0);
    city.addEdge("B3", "C2", 5.0);

    return city;
  }
}

// ==================== Snapshots ====================

interface DriverSnapshot {
  driverId: string;
  name: string;
  currentLocation: string;
  zone: string;
  status: DriverStatus;
  totalTrips: number;
  totalDistance: number;
  activeTime: number;
  idleTime: number;
  currentTripId: string | null;
}

interface RiderSnapshot {
  riderId: string;
  name: string;
  currentLocation: string;
  tripHistory: string[];
  currentTripId: string | null;
  totalTrips: number;
  totalDistance: number;
  totalSpent: number;
}

interface TripSnapshot {
  tripId: string;
  riderId: string;
  driverId: string | null;
  pickupLocation: string;
  dropoffLocation: string;
  pickupZone: string;
  dropoffZone: string;
  state: TripState;
  distance: number;
  estimatedDuration: number;
  actualDuration: number;
  cost: number;
  path: string[];
  isCrossZone: boolean;
  createdAt: Date;
  assignedAt: Date | null;
  startedAt: Date | null;
  completedAt: Date | null;
  cancelledAt: Date | null;
}

interface SystemSnapshot {
  driverSnapshots: Map<string, DriverSnapshot>;
  riderSnapshots: Map<string, RiderSnapshot>;
  tripSnapshots: Map<string, TripSnapshot>;
  existingDriverIds: string[];
  existingRiderIds: string[];
  existingTripIds: string[];
}

interface OperationRecord {
  operationId: string;
  operationType: string;
  timestamp: Date;
  description: string;
  beforeSnapshot: SystemSnapshot;
  affectedDriverIds: string[];
  affectedRiderIds: string[];
  affectedTripIds: string[];
  createdEntityId: string | null;
  createdEntityType: string | null;
}

// ==================== Main System ====================

const VALID_TRANSITIONS: Record<TripState, TripState[]> = {
  requested: ["assigned", "cancelled"],
  assigned: ["ongoing", "cancelled"],
  ongoing: ["completed"],
  completed: [],
  cancelled: [],
};

const BASE_FARE = 5.0;
const PER_KM_RATE = 2.0;
const CROSS_ZONE_PENALTY = 1.5;

export class RideShareSystem {
  private city: City;
  private drivers: Map<string, Driver> = new Map();
  private riders: Map<string, Rider> = new Map();
  private trips: Map<string, Trip> = new Map();
  private operationStack: OperationRecord[] = [];
  private operationCounter = 0;
  private driverCounter = 0;
  private riderCounter = 0;
  private tripCounter = 0;

  constructor() {
    this.city = City.createSampleCity();
  }

  // ==================== Snapshot Helpers ====================

  private createDriverSnapshot(driver: Driver): DriverSnapshot {
    return { ...driver };
  }

  private createRiderSnapshot(rider: Rider): RiderSnapshot {
    return { ...rider, tripHistory: [...rider.tripHistory] };
  }

  private createTripSnapshot(trip: Trip): TripSnapshot {
    return { ...trip, path: [...trip.path] };
  }

  private createSystemSnapshot(
    driverIds?: string[],
    riderIds?: string[],
    tripIds?: string[]
  ): SystemSnapshot {
    const snapshot: SystemSnapshot = {
      driverSnapshots: new Map(),
      riderSnapshots: new Map(),
      tripSnapshots: new Map(),
      existingDriverIds: Array.from(this.drivers.keys()),
      existingRiderIds: Array.from(this.riders.keys()),
      existingTripIds: Array.from(this.trips.keys()),
    };

    const driverIdsToSnapshot = driverIds || Array.from(this.drivers.keys());
    for (const id of driverIdsToSnapshot) {
      const driver = this.drivers.get(id);
      if (driver) {
        snapshot.driverSnapshots.set(id, this.createDriverSnapshot(driver));
      }
    }

    const riderIdsToSnapshot = riderIds || Array.from(this.riders.keys());
    for (const id of riderIdsToSnapshot) {
      const rider = this.riders.get(id);
      if (rider) {
        snapshot.riderSnapshots.set(id, this.createRiderSnapshot(rider));
      }
    }

    const tripIdsToSnapshot = tripIds || Array.from(this.trips.keys());
    for (const id of tripIdsToSnapshot) {
      const trip = this.trips.get(id);
      if (trip) {
        snapshot.tripSnapshots.set(id, this.createTripSnapshot(trip));
      }
    }

    return snapshot;
  }

  private logOperation(
    type: string,
    description: string,
    driverIds?: string[],
    riderIds?: string[],
    tripIds?: string[],
    createdEntityId?: string,
    createdEntityType?: string
  ): void {
    this.operationCounter++;
    const operation: OperationRecord = {
      operationId: `OP-${String(this.operationCounter).padStart(6, "0")}`,
      operationType: type,
      timestamp: new Date(),
      description,
      beforeSnapshot: this.createSystemSnapshot(driverIds, riderIds, tripIds),
      affectedDriverIds: driverIds || [],
      affectedRiderIds: riderIds || [],
      affectedTripIds: tripIds || [],
      createdEntityId: createdEntityId || null,
      createdEntityType: createdEntityType || null,
    };
    this.operationStack.push(operation);
  }

  // ==================== Driver Management ====================

  createDriver(name: string, location: string): Driver {
    const zone = this.city.getZone(location);
    if (!zone) {
      throw new Error(`Location ${location} does not exist`);
    }

    this.driverCounter++;
    const driverId = `D-${String(this.driverCounter).padStart(4, "0")}`;

    this.logOperation(
      "create_driver",
      `Create driver ${driverId}: ${name} at ${location}`,
      undefined,
      undefined,
      undefined,
      driverId,
      "driver"
    );

    const driver: Driver = {
      driverId,
      name,
      currentLocation: location,
      zone,
      status: "available",
      totalTrips: 0,
      totalDistance: 0,
      activeTime: 0,
      idleTime: 0,
      currentTripId: null,
    };

    this.drivers.set(driverId, driver);
    return driver;
  }

  getDriver(driverId: string): Driver | undefined {
    return this.drivers.get(driverId);
  }

  getAllDrivers(): Driver[] {
    return Array.from(this.drivers.values());
  }

  getAvailableDrivers(): Driver[] {
    return Array.from(this.drivers.values()).filter(
      (d) => d.status === "available"
    );
  }

  // ==================== Rider Management ====================

  createRider(name: string, location: string): Rider {
    if (!this.city.getZone(location)) {
      throw new Error(`Location ${location} does not exist`);
    }

    this.riderCounter++;
    const riderId = `R-${String(this.riderCounter).padStart(4, "0")}`;

    this.logOperation(
      "create_rider",
      `Create rider ${riderId}: ${name} at ${location}`,
      undefined,
      undefined,
      undefined,
      riderId,
      "rider"
    );

    const rider: Rider = {
      riderId,
      name,
      currentLocation: location,
      tripHistory: [],
      currentTripId: null,
      totalTrips: 0,
      totalDistance: 0,
      totalSpent: 0,
    };

    this.riders.set(riderId, rider);
    return rider;
  }

  getRider(riderId: string): Rider | undefined {
    return this.riders.get(riderId);
  }

  getAllRiders(): Rider[] {
    return Array.from(this.riders.values());
  }

  // ==================== Trip Management ====================

  private findBestDriver(
    pickupLocation: string
  ): [Driver, number, boolean] | null {
    const pickupZone = this.city.getZone(pickupLocation);
    if (!pickupZone) return null;

    const availableDrivers = this.getAvailableDrivers();
    const sameZoneDrivers = availableDrivers.filter(
      (d) => d.zone === pickupZone
    );

    let bestDriver: Driver | null = null;
    let bestDistance = Infinity;
    let isCrossZone = false;

    // Check same-zone drivers first
    for (const driver of sameZoneDrivers) {
      const distance = this.city.calculateDistance(
        driver.currentLocation,
        pickupLocation
      );
      if (distance < bestDistance) {
        bestDistance = distance;
        bestDriver = driver;
      }
    }

    if (bestDriver) {
      return [bestDriver, bestDistance, false];
    }

    // Check all available drivers (cross-zone)
    for (const driver of availableDrivers) {
      const distance = this.city.calculateDistance(
        driver.currentLocation,
        pickupLocation
      );
      const effectiveDistance = distance * CROSS_ZONE_PENALTY;

      if (effectiveDistance < bestDistance) {
        bestDistance = effectiveDistance;
        bestDriver = driver;
        isCrossZone = true;
      }
    }

    if (bestDriver) {
      const actualDistance = this.city.calculateDistance(
        bestDriver.currentLocation,
        pickupLocation
      );
      return [bestDriver, actualDistance, true];
    }

    return null;
  }

  requestTrip(
    riderId: string,
    pickupLocation: string,
    dropoffLocation: string
  ): Trip {
    const rider = this.riders.get(riderId);
    if (!rider) {
      throw new Error(`Rider ${riderId} not found`);
    }
    if (rider.currentTripId) {
      throw new Error(`Rider ${riderId} already has an active trip`);
    }

    const pickupZone = this.city.getZone(pickupLocation);
    const dropoffZone = this.city.getZone(dropoffLocation);

    if (!pickupZone) {
      throw new Error(`Pickup location ${pickupLocation} does not exist`);
    }
    if (!dropoffZone) {
      throw new Error(`Drop-off location ${dropoffLocation} does not exist`);
    }

    this.tripCounter++;
    const tripId = `T-${String(this.tripCounter).padStart(4, "0")}`;

    this.logOperation(
      "request_trip",
      `Request trip ${tripId} for rider ${riderId}`,
      undefined,
      [riderId],
      undefined,
      tripId,
      "trip"
    );

    const trip: Trip = {
      tripId,
      riderId,
      driverId: null,
      pickupLocation,
      dropoffLocation,
      pickupZone,
      dropoffZone,
      state: "requested",
      distance: 0,
      estimatedDuration: 0,
      actualDuration: 0,
      cost: 0,
      path: [],
      isCrossZone: pickupZone !== dropoffZone,
      createdAt: new Date(),
      assignedAt: null,
      startedAt: null,
      completedAt: null,
      cancelledAt: null,
    };

    this.trips.set(tripId, trip);
    rider.currentTripId = tripId;

    return trip;
  }

  assignTrip(tripId: string): Driver | null {
    const trip = this.trips.get(tripId);
    if (!trip) {
      throw new Error(`Trip ${tripId} not found`);
    }
    if (trip.state !== "requested") {
      throw new Error(`Trip ${tripId} is not in REQUESTED state`);
    }

    const result = this.findBestDriver(trip.pickupLocation);
    if (!result) {
      return null;
    }

    const [driver] = result;

    this.logOperation(
      "assign_trip",
      `Assign driver ${driver.driverId} to trip ${tripId}`,
      [driver.driverId],
      undefined,
      [tripId]
    );

    // Calculate route
    const [path, distance] = this.city.shortestPath(
      trip.pickupLocation,
      trip.dropoffLocation
    );

    // Update trip
    trip.state = "assigned";
    trip.driverId = driver.driverId;
    trip.distance = distance;
    trip.path = path;
    trip.estimatedDuration = (distance / 30) * 60;
    trip.cost = this.calculateCost(distance, trip.isCrossZone);
    trip.assignedAt = new Date();

    // Update driver
    driver.status = "busy";
    driver.currentTripId = tripId;

    return driver;
  }

  private calculateCost(distance: number, isCrossZone: boolean): number {
    let cost = BASE_FARE + distance * PER_KM_RATE;
    if (isCrossZone) {
      cost *= CROSS_ZONE_PENALTY;
    }
    return Math.round(cost * 100) / 100;
  }

  startTrip(tripId: string): boolean {
    const trip = this.trips.get(tripId);
    if (!trip) {
      throw new Error(`Trip ${tripId} not found`);
    }

    if (!VALID_TRANSITIONS[trip.state].includes("ongoing")) {
      throw new Error(`Cannot start trip in ${trip.state} state`);
    }

    this.logOperation("start_trip", `Start trip ${tripId}`, undefined, undefined, [
      tripId,
    ]);

    trip.state = "ongoing";
    trip.startedAt = new Date();

    return true;
  }

  completeTrip(tripId: string, actualDuration?: number): boolean {
    const trip = this.trips.get(tripId);
    if (!trip) {
      throw new Error(`Trip ${tripId} not found`);
    }

    if (!VALID_TRANSITIONS[trip.state].includes("completed")) {
      throw new Error(`Cannot complete trip in ${trip.state} state`);
    }

    const driver = trip.driverId ? this.drivers.get(trip.driverId) : null;
    const rider = this.riders.get(trip.riderId);

    const affectedDrivers = trip.driverId ? [trip.driverId] : [];
    this.logOperation(
      "complete_trip",
      `Complete trip ${tripId}`,
      affectedDrivers,
      [trip.riderId],
      [tripId]
    );

    trip.state = "completed";
    trip.completedAt = new Date();
    trip.actualDuration = actualDuration ?? trip.estimatedDuration;

    if (driver) {
      driver.status = "available";
      driver.currentTripId = null;
      driver.totalTrips++;
      driver.totalDistance += trip.distance;
      driver.activeTime += trip.actualDuration;
      driver.currentLocation = trip.dropoffLocation;
      driver.zone = trip.dropoffZone;
    }

    if (rider) {
      rider.tripHistory.push(tripId);
      rider.currentTripId = null;
      rider.totalTrips++;
      rider.totalDistance += trip.distance;
      rider.totalSpent += trip.cost;
      rider.currentLocation = trip.dropoffLocation;
    }

    return true;
  }

  cancelTrip(tripId: string): boolean {
    const trip = this.trips.get(tripId);
    if (!trip) {
      throw new Error(`Trip ${tripId} not found`);
    }

    if (!VALID_TRANSITIONS[trip.state].includes("cancelled")) {
      throw new Error(`Cannot cancel trip in ${trip.state} state`);
    }

    const driver = trip.driverId ? this.drivers.get(trip.driverId) : null;
    const rider = this.riders.get(trip.riderId);

    const affectedDrivers = trip.driverId ? [trip.driverId] : [];
    this.logOperation(
      "cancel_trip",
      `Cancel trip ${tripId}`,
      affectedDrivers,
      [trip.riderId],
      [tripId]
    );

    trip.state = "cancelled";
    trip.cancelledAt = new Date();

    if (driver) {
      driver.status = "available";
      driver.currentTripId = null;
    }

    if (rider) {
      rider.currentTripId = null;
    }

    return true;
  }

  getTrip(tripId: string): Trip | undefined {
    return this.trips.get(tripId);
  }

  getAllTrips(): Trip[] {
    return Array.from(this.trips.values());
  }

  getActiveTrips(): Trip[] {
    return Array.from(this.trips.values()).filter(
      (t) => t.state !== "completed" && t.state !== "cancelled"
    );
  }

  getTripEstimate(
    pickupLocation: string,
    dropoffLocation: string
  ): TripEstimate | null {
    const pickupZone = this.city.getZone(pickupLocation);
    const dropoffZone = this.city.getZone(dropoffLocation);

    if (!pickupZone || !dropoffZone) return null;

    const [path, distance] = this.city.shortestPath(
      pickupLocation,
      dropoffLocation
    );

    if (distance === Infinity) return null;

    const isCrossZone = pickupZone !== dropoffZone;
    const cost = this.calculateCost(distance, isCrossZone);
    const estimatedDuration = (distance / 30) * 60;

    const driverResult = this.findBestDriver(pickupLocation);
    let driverEta: number | null = null;

    if (driverResult) {
      const [, pickupDistance] = driverResult;
      driverEta = Math.round((pickupDistance / 30) * 60 * 10) / 10;
    }

    return {
      distance: Math.round(distance * 100) / 100,
      estimatedDuration: Math.round(estimatedDuration * 10) / 10,
      cost,
      isCrossZone,
      path,
      driverAvailable: driverResult !== null,
      driverEta,
    };
  }

  // ==================== Analytics ====================

  getAnalytics(): Analytics {
    const allTrips = Array.from(this.trips.values());
    const completedTrips = allTrips.filter((t) => t.state === "completed");
    const cancelledTrips = allTrips.filter((t) => t.state === "cancelled");
    const activeTrips = allTrips.filter(
      (t) => t.state !== "completed" && t.state !== "cancelled"
    );

    const avgDistance =
      completedTrips.length > 0
        ? completedTrips.reduce((sum, t) => sum + t.distance, 0) /
          completedTrips.length
        : 0;

    const allDrivers = Array.from(this.drivers.values());
    let totalUtilization = 0;
    let activeDriverCount = 0;

    for (const driver of allDrivers) {
      const totalTime = driver.activeTime + driver.idleTime;
      if (totalTime > 0) {
        totalUtilization += driver.activeTime / totalTime;
        activeDriverCount++;
      }
    }

    const avgUtilization =
      activeDriverCount > 0 ? totalUtilization / activeDriverCount : 0;

    const totalRevenue = completedTrips.reduce((sum, t) => sum + t.cost, 0);
    const crossZoneCompleted = completedTrips.filter((t) => t.isCrossZone);

    const zoneStats: Record<
      string,
      { totalDrivers: number; available: number; busy: number; offline: number }
    > = {};

    for (const zone of this.city.getAllZones()) {
      const zoneDrivers = allDrivers.filter((d) => d.zone === zone);
      zoneStats[zone] = {
        totalDrivers: zoneDrivers.length,
        available: zoneDrivers.filter((d) => d.status === "available").length,
        busy: zoneDrivers.filter((d) => d.status === "busy").length,
        offline: zoneDrivers.filter((d) => d.status === "offline").length,
      };
    }

    return {
      totalTrips: allTrips.length,
      completedTrips: completedTrips.length,
      cancelledTrips: cancelledTrips.length,
      activeTrips: activeTrips.length,
      completionRate:
        allTrips.length > 0 ? completedTrips.length / allTrips.length : 0,
      cancellationRate:
        allTrips.length > 0 ? cancelledTrips.length / allTrips.length : 0,
      averageTripDistance: Math.round(avgDistance * 100) / 100,
      totalDistanceCovered:
        Math.round(
          completedTrips.reduce((sum, t) => sum + t.distance, 0) * 100
        ) / 100,
      averageDriverUtilization: Math.round(avgUtilization * 10000) / 10000,
      totalDrivers: allDrivers.length,
      availableDrivers: allDrivers.filter((d) => d.status === "available")
        .length,
      busyDrivers: allDrivers.filter((d) => d.status === "busy").length,
      totalRevenue: Math.round(totalRevenue * 100) / 100,
      crossZoneTrips: crossZoneCompleted.length,
      crossZonePercentage:
        completedTrips.length > 0
          ? crossZoneCompleted.length / completedTrips.length
          : 0,
      totalRiders: this.riders.size,
      zoneStatistics: zoneStats,
    };
  }

  // ==================== Rollback ====================

  rollbackLast(): Operation | null {
    const operation = this.operationStack.pop();
    if (!operation) return null;

    this.applyRollback(operation);

    return {
      operationId: operation.operationId,
      operationType: operation.operationType,
      timestamp: operation.timestamp.toISOString(),
      description: operation.description,
    };
  }

  private applyRollback(operation: OperationRecord): void {
    const snapshot = operation.beforeSnapshot;

    // Handle entity creation rollback
    if (operation.createdEntityId && operation.createdEntityType) {
      if (operation.createdEntityType === "driver") {
        this.drivers.delete(operation.createdEntityId);
      } else if (operation.createdEntityType === "rider") {
        this.riders.delete(operation.createdEntityId);
      } else if (operation.createdEntityType === "trip") {
        this.trips.delete(operation.createdEntityId);
      }
    }

    // Restore driver states
    for (const [id, driverSnapshot] of snapshot.driverSnapshots) {
      const driver = this.drivers.get(id);
      if (driver) {
        Object.assign(driver, driverSnapshot);
      }
    }

    // Restore rider states
    for (const [id, riderSnapshot] of snapshot.riderSnapshots) {
      const rider = this.riders.get(id);
      if (rider) {
        Object.assign(rider, {
          ...riderSnapshot,
          tripHistory: [...riderSnapshot.tripHistory],
        });
      }
    }

    // Restore trip states
    for (const [id, tripSnapshot] of snapshot.tripSnapshots) {
      const trip = this.trips.get(id);
      if (trip) {
        Object.assign(trip, { ...tripSnapshot, path: [...tripSnapshot.path] });
      }
    }
  }

  rollbackK(k: number): Operation[] {
    const rolledBack: Operation[] = [];

    for (let i = 0; i < k; i++) {
      const op = this.rollbackLast();
      if (!op) break;
      rolledBack.push(op);
    }

    return rolledBack;
  }

  canRollback(): boolean {
    return this.operationStack.length > 0;
  }

  getOperationCount(): number {
    return this.operationStack.length;
  }

  getOperationHistory(count: number = 10): Operation[] {
    return this.operationStack
      .slice(-count)
      .reverse()
      .map((op) => ({
        operationId: op.operationId,
        operationType: op.operationType,
        timestamp: op.timestamp.toISOString(),
        description: op.description,
      }));
  }

  // ==================== City Access ====================

  getCity(): { name: string; nodes: Node[]; edges: Edge[]; zones: string[] } {
    return {
      name: this.city.name,
      nodes: this.city.getAllNodes(),
      edges: this.city.getAllEdges(),
      zones: this.city.getAllZones(),
    };
  }

  getShortestPath(start: string, end: string): [string[], number] {
    return this.city.shortestPath(start, end);
  }
}

// Singleton instance
let systemInstance: RideShareSystem | null = null;

export function getRideShareSystem(): RideShareSystem {
  if (!systemInstance) {
    systemInstance = new RideShareSystem();
  }
  return systemInstance;
}

export function resetRideShareSystem(): RideShareSystem {
  systemInstance = new RideShareSystem();
  return systemInstance;
}

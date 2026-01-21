"use client";

import { useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CityGraph } from "@/components/city-graph";
import { AnalyticsPanel } from "@/components/analytics-panel";
import { TripPanel } from "@/components/trip-panel";
import { OperationsPanel } from "@/components/operations-panel";
import {
  getRideShareSystem,
  resetRideShareSystem,
  type Driver,
  type Rider,
  type Trip,
  type Analytics,
  type Operation,
  type Node,
  type Edge,
  type TripEstimate,
} from "@/lib/ride-share-system";

export default function RideShareDashboard() {
  // System state
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [riders, setRiders] = useState<Rider[]>([]);
  const [trips, setTrips] = useState<Trip[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [operations, setOperations] = useState<Operation[]>([]);
  const [operationCount, setOperationCount] = useState(0);
  const [canRollback, setCanRollback] = useState(false);

  // City data
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  // Form state
  const [newDriverName, setNewDriverName] = useState("");
  const [newDriverLocation, setNewDriverLocation] = useState("");
  const [newRiderName, setNewRiderName] = useState("");
  const [newRiderLocation, setNewRiderLocation] = useState("");
  const [selectedRider, setSelectedRider] = useState("");
  const [pickupLocation, setPickupLocation] = useState("");
  const [dropoffLocation, setDropoffLocation] = useState("");
  const [tripEstimate, setTripEstimate] = useState<TripEstimate | null>(null);

  // Selection mode for map
  const [selectionMode, setSelectionMode] = useState<"pickup" | "dropoff" | null>(null);

  // Refresh state from system
  const refreshState = useCallback(() => {
    const system = getRideShareSystem();
    setDrivers(system.getAllDrivers());
    setRiders(system.getAllRiders());
    setTrips(system.getAllTrips());
    setAnalytics(system.getAnalytics());
    setOperations(system.getOperationHistory(20));
    setOperationCount(system.getOperationCount());
    setCanRollback(system.canRollback());

    const city = system.getCity();
    setNodes(city.nodes);
    setEdges(city.edges);
  }, []);

  // Initialize
  useEffect(() => {
    refreshState();
  }, [refreshState]);

  // Update estimate when locations change
  useEffect(() => {
    if (pickupLocation && dropoffLocation) {
      const system = getRideShareSystem();
      const estimate = system.getTripEstimate(pickupLocation, dropoffLocation);
      setTripEstimate(estimate);
    } else {
      setTripEstimate(null);
    }
  }, [pickupLocation, dropoffLocation]);

  // Handlers
  const handleCreateDriver = () => {
    if (!newDriverName || !newDriverLocation) return;
    try {
      const system = getRideShareSystem();
      system.createDriver(newDriverName, newDriverLocation);
      setNewDriverName("");
      setNewDriverLocation("");
      refreshState();
    } catch (error) {
      console.error("[v0] Error creating driver:", error);
    }
  };

  const handleCreateRider = () => {
    if (!newRiderName || !newRiderLocation) return;
    try {
      const system = getRideShareSystem();
      system.createRider(newRiderName, newRiderLocation);
      setNewRiderName("");
      setNewRiderLocation("");
      refreshState();
    } catch (error) {
      console.error("[v0] Error creating rider:", error);
    }
  };

  const handleRequestTrip = () => {
    if (!selectedRider || !pickupLocation || !dropoffLocation) return;
    try {
      const system = getRideShareSystem();
      const trip = system.requestTrip(selectedRider, pickupLocation, dropoffLocation);

      // Try to assign immediately
      system.assignTrip(trip.tripId);

      setSelectedRider("");
      setPickupLocation("");
      setDropoffLocation("");
      setTripEstimate(null);
      refreshState();
    } catch (error) {
      console.error("[v0] Error requesting trip:", error);
    }
  };

  const handleStartTrip = (tripId: string) => {
    try {
      const system = getRideShareSystem();
      system.startTrip(tripId);
      refreshState();
    } catch (error) {
      console.error("[v0] Error starting trip:", error);
    }
  };

  const handleCompleteTrip = (tripId: string) => {
    try {
      const system = getRideShareSystem();
      system.completeTrip(tripId);
      refreshState();
    } catch (error) {
      console.error("[v0] Error completing trip:", error);
    }
  };

  const handleCancelTrip = (tripId: string) => {
    try {
      const system = getRideShareSystem();
      system.cancelTrip(tripId);
      refreshState();
    } catch (error) {
      console.error("[v0] Error cancelling trip:", error);
    }
  };

  const handleRollbackLast = () => {
    try {
      const system = getRideShareSystem();
      system.rollbackLast();
      refreshState();
    } catch (error) {
      console.error("[v0] Error rolling back:", error);
    }
  };

  const handleRollbackK = (k: number) => {
    try {
      const system = getRideShareSystem();
      system.rollbackK(k);
      refreshState();
    } catch (error) {
      console.error("[v0] Error rolling back:", error);
    }
  };

  const handleResetSystem = () => {
    resetRideShareSystem();
    refreshState();
  };

  const handleNodeClick = (nodeId: string) => {
    if (selectionMode === "pickup") {
      setPickupLocation(nodeId);
      setSelectionMode("dropoff");
    } else if (selectionMode === "dropoff") {
      setDropoffLocation(nodeId);
      setSelectionMode(null);
    }
  };

  // Get available riders (no active trip)
  const availableRiders = riders.filter((r) => !r.currentTripId);

  // Get active trip for visualization
  const activeTrip = trips.find(
    (t) => t.state === "ongoing" || t.state === "assigned"
  );

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Ride-Share Dispatch System</h1>
            <p className="text-sm text-muted-foreground">
              Trip management, routing, and analytics dashboard
            </p>
          </div>
          <Button variant="outline" onClick={handleResetSystem}>
            Reset System
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - City Map */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle>City Map</CardTitle>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant={selectionMode === "pickup" ? "default" : "outline"}
                      onClick={() => setSelectionMode(selectionMode === "pickup" ? null : "pickup")}
                    >
                      Select Pickup
                    </Button>
                    <Button
                      size="sm"
                      variant={selectionMode === "dropoff" ? "default" : "outline"}
                      onClick={() => setSelectionMode(selectionMode === "dropoff" ? null : "dropoff")}
                    >
                      Select Drop-off
                    </Button>
                  </div>
                </div>
                {selectionMode && (
                  <p className="text-sm text-muted-foreground">
                    Click a node on the map to select {selectionMode} location
                  </p>
                )}
              </CardHeader>
              <CardContent>
                <div className="h-[400px] bg-muted/30 rounded-lg">
                  <CityGraph
                    nodes={nodes}
                    edges={edges}
                    drivers={drivers}
                    activeTrip={activeTrip}
                    selectedPickup={pickupLocation}
                    selectedDropoff={dropoffLocation}
                    onNodeClick={handleNodeClick}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Analytics */}
            {analytics && <AnalyticsPanel analytics={analytics} />}
          </div>

          {/* Right Column - Controls */}
          <div className="space-y-6">
            <Tabs defaultValue="trip" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="trip">Trip</TabsTrigger>
                <TabsTrigger value="drivers">Drivers</TabsTrigger>
                <TabsTrigger value="riders">Riders</TabsTrigger>
              </TabsList>

              <TabsContent value="trip" className="space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Request Trip</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Rider</Label>
                      <Select
                        value={selectedRider}
                        onValueChange={setSelectedRider}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select rider" />
                        </SelectTrigger>
                        <SelectContent>
                          {availableRiders.map((rider) => (
                            <SelectItem key={rider.riderId} value={rider.riderId}>
                              {rider.name} ({rider.riderId})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Pickup Location</Label>
                      <Select
                        value={pickupLocation}
                        onValueChange={setPickupLocation}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select pickup" />
                        </SelectTrigger>
                        <SelectContent>
                          {nodes.map((node) => (
                            <SelectItem key={node.nodeId} value={node.nodeId}>
                              {node.nodeId} - {node.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Drop-off Location</Label>
                      <Select
                        value={dropoffLocation}
                        onValueChange={setDropoffLocation}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select drop-off" />
                        </SelectTrigger>
                        <SelectContent>
                          {nodes.map((node) => (
                            <SelectItem key={node.nodeId} value={node.nodeId}>
                              {node.nodeId} - {node.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {tripEstimate && (
                      <div className="p-3 rounded-lg bg-muted/50 space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Distance:</span>
                          <span>{tripEstimate.distance} km</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Est. Duration:</span>
                          <span>{tripEstimate.estimatedDuration} min</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Cost:</span>
                          <span className="font-medium">${tripEstimate.cost}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Cross-Zone:</span>
                          <Badge variant={tripEstimate.isCrossZone ? "secondary" : "outline"}>
                            {tripEstimate.isCrossZone ? "Yes" : "No"}
                          </Badge>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Driver:</span>
                          <span>
                            {tripEstimate.driverAvailable
                              ? `Available (ETA: ${tripEstimate.driverEta} min)`
                              : "None available"}
                          </span>
                        </div>
                      </div>
                    )}

                    <Button
                      className="w-full"
                      onClick={handleRequestTrip}
                      disabled={!selectedRider || !pickupLocation || !dropoffLocation}
                    >
                      Request & Assign Trip
                    </Button>
                  </CardContent>
                </Card>

                <TripPanel
                  trips={trips}
                  onStartTrip={handleStartTrip}
                  onCompleteTrip={handleCompleteTrip}
                  onCancelTrip={handleCancelTrip}
                />
              </TabsContent>

              <TabsContent value="drivers" className="space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Add Driver</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Name</Label>
                      <Input
                        value={newDriverName}
                        onChange={(e) => setNewDriverName(e.target.value)}
                        placeholder="Driver name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Location</Label>
                      <Select
                        value={newDriverLocation}
                        onValueChange={setNewDriverLocation}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select location" />
                        </SelectTrigger>
                        <SelectContent>
                          {nodes.map((node) => (
                            <SelectItem key={node.nodeId} value={node.nodeId}>
                              {node.nodeId} - {node.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <Button
                      className="w-full"
                      onClick={handleCreateDriver}
                      disabled={!newDriverName || !newDriverLocation}
                    >
                      Create Driver
                    </Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Drivers ({drivers.length})</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <ScrollArea className="h-[350px] px-4 pb-4">
                      <div className="space-y-3">
                        {drivers.map((driver) => (
                          <div
                            key={driver.driverId}
                            className="p-3 rounded-lg border bg-card"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">{driver.name}</span>
                              <Badge
                                variant={
                                  driver.status === "available"
                                    ? "default"
                                    : driver.status === "busy"
                                    ? "secondary"
                                    : "outline"
                                }
                              >
                                {driver.status}
                              </Badge>
                            </div>
                            <div className="text-xs text-muted-foreground space-y-1">
                              <div className="flex justify-between">
                                <span>ID:</span>
                                <span className="text-foreground">{driver.driverId}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Location:</span>
                                <span className="text-foreground">{driver.currentLocation}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Zone:</span>
                                <span className="text-foreground">{driver.zone}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Trips:</span>
                                <span className="text-foreground">{driver.totalTrips}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Distance:</span>
                                <span className="text-foreground">{driver.totalDistance} km</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="riders" className="space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Add Rider</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Name</Label>
                      <Input
                        value={newRiderName}
                        onChange={(e) => setNewRiderName(e.target.value)}
                        placeholder="Rider name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Location</Label>
                      <Select
                        value={newRiderLocation}
                        onValueChange={setNewRiderLocation}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select location" />
                        </SelectTrigger>
                        <SelectContent>
                          {nodes.map((node) => (
                            <SelectItem key={node.nodeId} value={node.nodeId}>
                              {node.nodeId} - {node.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <Button
                      className="w-full"
                      onClick={handleCreateRider}
                      disabled={!newRiderName || !newRiderLocation}
                    >
                      Create Rider
                    </Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Riders ({riders.length})</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <ScrollArea className="h-[350px] px-4 pb-4">
                      <div className="space-y-3">
                        {riders.map((rider) => (
                          <div
                            key={rider.riderId}
                            className="p-3 rounded-lg border bg-card"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">{rider.name}</span>
                              <Badge
                                variant={rider.currentTripId ? "secondary" : "outline"}
                              >
                                {rider.currentTripId ? "On Trip" : "Available"}
                              </Badge>
                            </div>
                            <div className="text-xs text-muted-foreground space-y-1">
                              <div className="flex justify-between">
                                <span>ID:</span>
                                <span className="text-foreground">{rider.riderId}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Location:</span>
                                <span className="text-foreground">{rider.currentLocation}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Trips:</span>
                                <span className="text-foreground">{rider.totalTrips}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Total Spent:</span>
                                <span className="text-foreground">${rider.totalSpent}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>

            {/* Operations Panel */}
            <OperationsPanel
              operations={operations}
              operationCount={operationCount}
              canRollback={canRollback}
              onRollbackLast={handleRollbackLast}
              onRollbackK={handleRollbackK}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

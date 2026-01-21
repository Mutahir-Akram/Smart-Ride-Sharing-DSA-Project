"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Trip } from "@/lib/ride-share-system";

interface TripPanelProps {
  trips: Trip[];
  onStartTrip: (tripId: string) => void;
  onCompleteTrip: (tripId: string) => void;
  onCancelTrip: (tripId: string) => void;
}

const STATE_COLORS: Record<string, string> = {
  requested: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  assigned: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  ongoing: "bg-green-500/20 text-green-400 border-green-500/30",
  completed: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  cancelled: "bg-red-500/20 text-red-400 border-red-500/30",
};

export function TripPanel({
  trips,
  onStartTrip,
  onCompleteTrip,
  onCancelTrip,
}: TripPanelProps) {
  const sortedTrips = [...trips].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Trips</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[400px] px-4 pb-4">
          <div className="space-y-3">
            {sortedTrips.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No trips yet. Request a trip to get started.
              </p>
            ) : (
              sortedTrips.map((trip) => (
                <div
                  key={trip.tripId}
                  className="p-3 rounded-lg border bg-card"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{trip.tripId}</span>
                    <Badge
                      variant="outline"
                      className={STATE_COLORS[trip.state]}
                    >
                      {trip.state}
                    </Badge>
                  </div>

                  <div className="text-xs text-muted-foreground space-y-1">
                    <div className="flex justify-between">
                      <span>From:</span>
                      <span className="text-foreground">{trip.pickupLocation}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>To:</span>
                      <span className="text-foreground">{trip.dropoffLocation}</span>
                    </div>
                    {trip.driverId && (
                      <div className="flex justify-between">
                        <span>Driver:</span>
                        <span className="text-foreground">{trip.driverId}</span>
                      </div>
                    )}
                    {trip.distance > 0 && (
                      <div className="flex justify-between">
                        <span>Distance:</span>
                        <span className="text-foreground">{trip.distance} km</span>
                      </div>
                    )}
                    {trip.cost > 0 && (
                      <div className="flex justify-between">
                        <span>Cost:</span>
                        <span className="text-foreground">${trip.cost}</span>
                      </div>
                    )}
                    {trip.isCrossZone && (
                      <Badge variant="secondary" className="text-[10px] mt-1">
                        Cross-Zone
                      </Badge>
                    )}
                  </div>

                  {/* Action buttons based on state */}
                  <div className="flex gap-2 mt-3">
                    {trip.state === "assigned" && (
                      <>
                        <Button
                          size="sm"
                          className="flex-1"
                          onClick={() => onStartTrip(trip.tripId)}
                        >
                          Start Trip
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => onCancelTrip(trip.tripId)}
                        >
                          Cancel
                        </Button>
                      </>
                    )}
                    {trip.state === "ongoing" && (
                      <Button
                        size="sm"
                        className="flex-1"
                        onClick={() => onCompleteTrip(trip.tripId)}
                      >
                        Complete Trip
                      </Button>
                    )}
                    {trip.state === "requested" && (
                      <Button
                        size="sm"
                        variant="destructive"
                        className="flex-1"
                        onClick={() => onCancelTrip(trip.tripId)}
                      >
                        Cancel Request
                      </Button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

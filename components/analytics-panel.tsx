"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Analytics } from "@/lib/ride-share-system";

interface AnalyticsPanelProps {
  analytics: Analytics;
}

export function AnalyticsPanel({ analytics }: AnalyticsPanelProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Trips
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{analytics.totalTrips}</div>
          <p className="text-xs text-muted-foreground mt-1">
            {analytics.completedTrips} completed, {analytics.cancelledTrips} cancelled
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Completion Rate
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {(analytics.completionRate * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {analytics.activeTrips} active trips
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Revenue
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">${analytics.totalRevenue}</div>
          <p className="text-xs text-muted-foreground mt-1">
            Avg distance: {analytics.averageTripDistance} km
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Driver Utilization
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {(analytics.averageDriverUtilization * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {analytics.availableDrivers}/{analytics.totalDrivers} available
          </p>
        </CardContent>
      </Card>

      <Card className="col-span-2">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Cross-Zone Trips
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{analytics.crossZoneTrips}</div>
          <p className="text-xs text-muted-foreground mt-1">
            {(analytics.crossZonePercentage * 100).toFixed(1)}% of completed trips
          </p>
        </CardContent>
      </Card>

      <Card className="col-span-2">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Distance Covered
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{analytics.totalDistanceCovered} km</div>
          <p className="text-xs text-muted-foreground mt-1">
            {analytics.totalRiders} total riders
          </p>
        </CardContent>
      </Card>

      <Card className="col-span-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Zone Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(analytics.zoneStatistics).map(([zone, stats]) => (
              <div key={zone} className="p-3 rounded-lg bg-muted/50">
                <div className="font-medium text-sm">{zone}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  <span className="text-green-500">{stats.available} available</span>
                  {" / "}
                  <span className="text-amber-500">{stats.busy} busy</span>
                  {" / "}
                  <span className="text-muted-foreground">{stats.offline} offline</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

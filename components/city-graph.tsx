"use client";

import React from "react"

import { useEffect, useRef } from "react";
import type { Node, Edge, Driver, Trip } from "@/lib/ride-share-system";

interface CityGraphProps {
  nodes: Node[];
  edges: Edge[];
  drivers?: Driver[];
  activeTrip?: Trip | null;
  selectedPickup?: string | null;
  selectedDropoff?: string | null;
  onNodeClick?: (nodeId: string) => void;
}

const ZONE_COLORS: Record<string, string> = {
  "Zone-A": "#3b82f6", // blue
  "Zone-B": "#22c55e", // green
  "Zone-C": "#f59e0b", // amber
  "Zone-M": "#8b5cf6", // violet
};

export function CityGraph({
  nodes,
  edges,
  drivers = [],
  activeTrip,
  selectedPickup,
  selectedDropoff,
  onNodeClick,
}: CityGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    ctx.scale(2, 2);

    // Clear canvas
    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, rect.width, rect.height);

    // Scale factors
    const padding = 40;
    const scaleX = (rect.width - padding * 2) / 450;
    const scaleY = (rect.height - padding * 2) / 350;

    const transformX = (x: number) => x * scaleX + padding;
    const transformY = (y: number) => y * scaleY + padding;

    // Draw edges
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 2;

    for (const edge of edges) {
      const fromNode = nodes.find((n) => n.nodeId === edge.fromNode);
      const toNode = nodes.find((n) => n.nodeId === edge.toNode);

      if (fromNode && toNode) {
        ctx.beginPath();
        ctx.moveTo(transformX(fromNode.x), transformY(fromNode.y));
        ctx.lineTo(transformX(toNode.x), transformY(toNode.y));
        ctx.stroke();

        // Draw distance label
        const midX = (transformX(fromNode.x) + transformX(toNode.x)) / 2;
        const midY = (transformY(fromNode.y) + transformY(toNode.y)) / 2;
        ctx.fillStyle = "#666";
        ctx.font = "10px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(`${edge.distance}km`, midX, midY - 5);
      }
    }

    // Draw active trip path
    if (activeTrip && activeTrip.path.length > 0) {
      ctx.strokeStyle = "#22c55e";
      ctx.lineWidth = 3;
      ctx.setLineDash([5, 5]);

      ctx.beginPath();
      for (let i = 0; i < activeTrip.path.length; i++) {
        const node = nodes.find((n) => n.nodeId === activeTrip.path[i]);
        if (node) {
          if (i === 0) {
            ctx.moveTo(transformX(node.x), transformY(node.y));
          } else {
            ctx.lineTo(transformX(node.x), transformY(node.y));
          }
        }
      }
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Draw nodes
    for (const node of nodes) {
      const x = transformX(node.x);
      const y = transformY(node.y);

      // Node circle
      let color = ZONE_COLORS[node.zone] || "#666";
      let radius = 12;

      // Highlight selected nodes
      if (node.nodeId === selectedPickup) {
        color = "#22c55e";
        radius = 16;
      } else if (node.nodeId === selectedDropoff) {
        color = "#ef4444";
        radius = 16;
      }

      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Node label
      ctx.fillStyle = "#fff";
      ctx.font = "bold 10px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(node.nodeId, x, y);

      // Node name below
      ctx.fillStyle = "#999";
      ctx.font = "9px sans-serif";
      ctx.fillText(node.name, x, y + 22);
    }

    // Draw drivers
    for (const driver of drivers) {
      const node = nodes.find((n) => n.nodeId === driver.currentLocation);
      if (node) {
        const x = transformX(node.x);
        const y = transformY(node.y) - 25;

        // Driver icon (car)
        ctx.fillStyle = driver.status === "available" ? "#22c55e" : "#f59e0b";
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        ctx.fill();

        // Driver initial
        ctx.fillStyle = "#000";
        ctx.font = "bold 8px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(driver.name[0], x, y);
      }
    }

    // Draw legend
    const legendY = rect.height - 30;
    ctx.font = "11px sans-serif";
    
    let legendX = 20;
    for (const [zone, color] of Object.entries(ZONE_COLORS)) {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(legendX, legendY, 6, 0, Math.PI * 2);
      ctx.fill();
      
      ctx.fillStyle = "#999";
      ctx.textAlign = "left";
      ctx.fillText(zone, legendX + 12, legendY + 3);
      legendX += 80;
    }
  }, [nodes, edges, drivers, activeTrip, selectedPickup, selectedDropoff]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onNodeClick) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const padding = 40;
    const scaleX = (rect.width - padding * 2) / 450;
    const scaleY = (rect.height - padding * 2) / 350;

    for (const node of nodes) {
      const nodeX = node.x * scaleX + padding;
      const nodeY = node.y * scaleY + padding;
      const distance = Math.sqrt((x - nodeX) ** 2 + (y - nodeY) ** 2);

      if (distance < 20) {
        onNodeClick(node.nodeId);
        return;
      }
    }
  };

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full cursor-pointer rounded-lg"
      onClick={handleClick}
    />
  );
}

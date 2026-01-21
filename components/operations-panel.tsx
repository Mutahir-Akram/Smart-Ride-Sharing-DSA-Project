"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import type { Operation } from "@/lib/ride-share-system";

interface OperationsPanelProps {
  operations: Operation[];
  operationCount: number;
  canRollback: boolean;
  onRollbackLast: () => void;
  onRollbackK: (k: number) => void;
}

export function OperationsPanel({
  operations,
  operationCount,
  canRollback,
  onRollbackLast,
  onRollbackK,
}: OperationsPanelProps) {
  const [rollbackCount, setRollbackCount] = useState("2");

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Operations</CardTitle>
          <span className="text-xs text-muted-foreground">
            {operationCount} operations
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={onRollbackLast}
            disabled={!canRollback}
            className="flex-1 bg-transparent"
          >
            Rollback Last
          </Button>
          <div className="flex gap-1">
            <Input
              type="number"
              min="1"
              max={operationCount}
              value={rollbackCount}
              onChange={(e) => setRollbackCount(e.target.value)}
              className="w-16 h-8"
            />
            <Button
              size="sm"
              variant="outline"
              onClick={() => onRollbackK(parseInt(rollbackCount) || 1)}
              disabled={!canRollback}
            >
              Rollback K
            </Button>
          </div>
        </div>

        <ScrollArea className="h-[280px]">
          <div className="space-y-2">
            {operations.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No operations yet
              </p>
            ) : (
              operations.map((op) => (
                <div
                  key={op.operationId}
                  className="p-2 rounded border bg-muted/30 text-xs"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-[10px] text-muted-foreground">
                      {op.operationId}
                    </span>
                    <span className="text-[10px] text-muted-foreground">
                      {new Date(op.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-foreground">{op.description}</p>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

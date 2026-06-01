import { cn } from "@/utils/cn";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Play, CheckSquare } from "lucide-react";
import type { Recommendation } from "@/types/chat";
import type { RiskLevel } from "@/utils/constants";

interface RecommendationCardProps {
  recommendations: Recommendation[];
  onExecuteAll: () => void;
  onExecuteSelected: (ids: string[]) => void;
}

const RISK_STYLES: Record<RiskLevel, string> = {
  low: "bg-green-500/15 text-green-400 border-green-500/30",
  medium: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
};

/** Displays command recommendations as a step-by-step action list */
export function RecommendationCard({ recommendations, onExecuteAll, onExecuteSelected }: RecommendationCardProps) {
  return (
    <Card className="mt-3 border-accent/20">
      <h4 className="mb-3 text-sm font-semibold text-text-primary">Recommended Actions</h4>
      <div className="space-y-2">
        {recommendations.map((rec, index) => (
          <div
            key={rec.id}
            className="flex items-start gap-3 rounded-lg bg-bg-primary/50 p-3"
          >
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent/15 text-xs font-medium text-accent">
              {index + 1}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-text-primary">{rec.title}</span>
                <span
                  className={cn(
                    "inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px] font-medium",
                    RISK_STYLES[rec.risk],
                  )}
                >
                  {rec.risk}
                </span>
              </div>
              <p className="mt-0.5 text-xs text-text-secondary">{rec.description}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex gap-2">
        <Button size="sm" onClick={onExecuteAll} aria-label="Execute all recommendations">
          <Play className="h-3.5 w-3.5" />
          Execute All
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onExecuteSelected(recommendations.map((r) => r.id))}
          aria-label="Select and execute recommendations"
        >
          <CheckSquare className="h-3.5 w-3.5" />
          Select Execute
        </Button>
      </div>
    </Card>
  );
}

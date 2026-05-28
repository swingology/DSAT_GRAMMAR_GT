import { useQuery } from "@tanstack/react-query";
import { fetchStats } from "../api/stats";
import { Badge } from "./ui/badge";
import { useState } from "react";

interface Props {
  userId: string;
}

export function StatsPanel({ userId }: Props) {
  const [showRaw, setShowRaw] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["stats", userId],
    queryFn: () => fetchStats(userId),
    enabled: !!userId,
  });

  if (isLoading) {
    return <div className="text-muted-foreground text-sm animate-pulse">Loading stats…</div>;
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3">
        Could not load stats: {(error as Error).message}
      </div>
    );
  }

  if (!data) return null;

  const accuracy = data.accuracy != null ? Math.round(data.accuracy * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Summary row */}
      <div className="flex gap-8">
        <div className="space-y-1">
          <div className="text-4xl font-bold text-primary">{accuracy}%</div>
          <div className="text-xs text-muted-foreground uppercase tracking-wide">Accuracy</div>
        </div>
        <div className="space-y-1">
          <div className="text-4xl font-bold">{data.total_correct}/{data.total_answered}</div>
          <div className="text-xs text-muted-foreground uppercase tracking-wide">Correct</div>
        </div>
      </div>

      {/* Missed focus keys */}
      {data.top_missed_focus_keys?.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Top Missed Focus Areas</h3>
          <div className="flex flex-wrap gap-2">
            {data.top_missed_focus_keys.map((k) => (
              <Badge key={k} variant="destructive" className="text-xs">{k}</Badge>
            ))}
          </div>
        </div>
      )}

      {/* Missed trap keys */}
      {data.top_missed_trap_keys?.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Top Missed Trap Types</h3>
          <div className="flex flex-wrap gap-2">
            {data.top_missed_trap_keys.map((k) => (
              <Badge key={k} variant="secondary" className="text-xs">{k}</Badge>
            ))}
          </div>
        </div>
      )}

      {data.total_answered === 0 && (
        <p className="text-muted-foreground text-sm">No answers submitted yet. Start a drill to build your stats.</p>
      )}

      {/* Dev accordion */}
      <div className="border rounded-lg overflow-hidden">
        <button
          onClick={() => setShowRaw((v) => !v)}
          className="w-full text-left px-4 py-2 text-xs text-muted-foreground bg-muted hover:bg-muted/80 font-mono"
        >
          {showRaw ? "▼" : "▶"} Raw API response (dev)
        </button>
        {showRaw && (
          <pre className="p-4 text-xs overflow-auto bg-background">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

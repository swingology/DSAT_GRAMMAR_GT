import { cn } from "../lib/utils";

interface Props {
  secondsLeft: number;
}

export function TestTimer({ secondsLeft }: Props) {
  const mins = Math.floor(secondsLeft / 60);
  const secs = secondsLeft % 60;
  const urgent = secondsLeft <= 300;   // < 5 minutes
  const critical = secondsLeft <= 60;  // < 1 minute

  return (
    <div className={cn(
      "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-mono font-semibold border",
      critical ? "bg-red-50 border-red-300 text-red-700 animate-pulse"
               : urgent  ? "bg-orange-50 border-orange-300 text-orange-700"
                        : "bg-muted border-border text-foreground"
    )}>
      <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
      {String(mins).padStart(2, "0")}:{String(secs).padStart(2, "0")}
      {urgent && !critical && <span className="text-xs font-normal ml-1">— time running out</span>}
      {critical && <span className="text-xs font-normal ml-1">— almost done!</span>}
    </div>
  );
}

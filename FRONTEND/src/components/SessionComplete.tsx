import { Button } from "./ui/button";

interface Props {
  answered: number;
  correct: number;
  timeTaken?: number; // seconds, test mode only
  onRestart: () => void;
}

export function SessionComplete({ answered, correct, timeTaken, onRestart }: Props) {
  const accuracy = answered > 0 ? Math.round((correct / answered) * 100) : 0;

  function formatTime(secs: number) {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}m ${String(s).padStart(2, "0")}s`;
  }

  return (
    <div className="text-center space-y-6 max-w-sm mx-auto py-8">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">
          {timeTaken !== undefined ? "Test Complete" : "Session Complete"}
        </h2>
        <p className="text-muted-foreground">Here's how you did</p>
      </div>

      <div className="flex justify-center gap-8">
        <div className="space-y-1">
          <div className="text-4xl font-bold text-primary">{accuracy}%</div>
          <div className="text-xs text-muted-foreground uppercase tracking-wide">Accuracy</div>
        </div>
        <div className="space-y-1">
          <div className="text-4xl font-bold">{correct}/{answered}</div>
          <div className="text-xs text-muted-foreground uppercase tracking-wide">Correct</div>
        </div>
        {timeTaken !== undefined && (
          <div className="space-y-1">
            <div className="text-4xl font-bold">{formatTime(timeTaken)}</div>
            <div className="text-xs text-muted-foreground uppercase tracking-wide">Time used</div>
          </div>
        )}
      </div>

      <Button onClick={onRestart} size="lg">
        {timeTaken !== undefined ? "New Test" : "Start New Session"}
      </Button>
    </div>
  );
}

import { getUserId } from "../lib/auth";
import { StatsPanel } from "../components/StatsPanel";

export function StatsPage() {
  let userId: string;
  try {
    userId = getUserId();
  } catch {
    return (
      <div className="text-muted-foreground text-sm">
        No user ID found — set VITE_TEST_USER_ID in .env or log in.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Your Progress</h1>
      <StatsPanel userId={userId} />
    </div>
  );
}

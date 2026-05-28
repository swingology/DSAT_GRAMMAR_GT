import type { UserStats } from "../types";

const BASE = import.meta.env.VITE_API_BASE_URL as string;
const API_KEY = import.meta.env.VITE_STUDENT_API_KEY as string;

export async function fetchStats(userId: string): Promise<UserStats> {
  const res = await fetch(`${BASE}/api/stats/${userId}`, {
    headers: { "X-API-Key": API_KEY },
  });
  if (!res.ok) throw new Error(`fetchStats failed: ${res.status}`);
  return res.json();
}

import type { Question } from "../types";

const BASE = import.meta.env.VITE_API_BASE_URL as string;
const API_KEY = import.meta.env.VITE_STUDENT_API_KEY as string;

const h = () => ({ "X-API-Key": API_KEY });

export interface FilterInventory {
  hasMixed: boolean;
  hasGrammar: boolean;
  hasReading: boolean;
  mixedTotal: number;
  grammarTotal: number;
  readingTotal: number;
  difficulties: string[];
  diffCounts: Record<string, number>;
}

export async function fetchFilterInventory(userToken: string): Promise<FilterInventory> {
  const url = (extra = "") =>
    `${BASE}/api/questions?limit=${extra ? 1 : 50}&user_token=${userToken}${extra}`;

  const [mixedRes, grammarRes, readingRes, lowRes, highRes] = await Promise.all([
    fetch(url(),                       { headers: h() }),
    fetch(url("&domain=grammar"),      { headers: h() }),
    fetch(url("&domain=reading"),      { headers: h() }),
    fetch(url("&difficulty=low"),      { headers: h() }),
    fetch(url("&difficulty=high"),     { headers: h() }),
  ]);

  const [mixed, grammar, reading, low, high] = await Promise.all([
    mixedRes.json(),
    grammarRes.json(),
    readingRes.json(),
    lowRes.json(),
    highRes.json(),
  ]);

  const mixedTotal   = mixed.inventory?.matching_target_total   ?? 0;
  const grammarTotal = grammar.inventory?.matching_target_total ?? 0;
  const readingTotal = reading.inventory?.matching_target_total ?? 0;
  const lowTotal     = low.inventory?.matching_target_total     ?? 0;
  const highTotal    = high.inventory?.matching_target_total    ?? 0;

  // Derive medium count from the 50-item sample
  const mediumCount = (mixed.items as Question[]).filter(
    (q) => q.difficulty_overall === "medium"
  ).length;

  const difficulties = [
    ...new Set(
      (mixed.items as Question[])
        .map((q) => q.difficulty_overall)
        .filter((d): d is string => !!d)
    ),
  ].sort();

  return {
    hasMixed:   mixedTotal > 0,
    hasGrammar: grammarTotal > 0,
    hasReading: readingTotal > 0,
    mixedTotal,
    grammarTotal,
    readingTotal,
    difficulties,
    diffCounts: {
      low:    lowTotal,
      medium: mediumCount,
      high:   highTotal,
    },
  };
}

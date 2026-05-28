import type { Question } from "../types";

const BASE = import.meta.env.VITE_API_BASE_URL as string;
const API_KEY = import.meta.env.VITE_STUDENT_API_KEY as string;

const h = () => ({ "X-API-Key": API_KEY });

export interface FilterInventory {
  hasMixed: boolean;
  hasGrammar: boolean;
  hasReading: boolean;
  difficulties: string[];
}

export async function fetchFilterInventory(userToken: string): Promise<FilterInventory> {
  const qs = (extra = "") =>
    `${BASE}/api/questions?limit=${extra ? 1 : 50}&user_token=${userToken}${extra}`;

  const [mixedRes, grammarRes, readingRes] = await Promise.all([
    fetch(qs(), { headers: h() }),
    fetch(qs("&domain=grammar"), { headers: h() }),
    fetch(qs("&domain=reading"), { headers: h() }),
  ]);

  const [mixedData, grammarData, readingData] = await Promise.all([
    mixedRes.json(),
    grammarRes.json(),
    readingRes.json(),
  ]);

  const difficulties = [
    ...new Set(
      (mixedData.items as Question[])
        .map((q) => q.difficulty_overall)
        .filter((d): d is string => !!d)
    ),
  ].sort();

  return {
    hasMixed: (mixedData.inventory?.matching_target_total ?? 0) > 0,
    hasGrammar: (grammarData.inventory?.matching_target_total ?? 0) > 0,
    hasReading: (readingData.inventory?.matching_target_total ?? 0) > 0,
    difficulties,
  };
}

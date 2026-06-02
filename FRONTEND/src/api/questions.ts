import type { QuestionsResponse, SubmitResult } from "../types";

const BASE = import.meta.env.VITE_API_BASE_URL as string;
const API_KEY = import.meta.env.VITE_STUDENT_API_KEY as string;

const headers = () => ({ "X-API-Key": API_KEY });

export async function fetchQuestions(params: {
  domain?: "grammar" | "reading";
  difficulty?: string;
  limit?: number;
  userToken: string;
  sourceReleaseYear?: number;
  sourceTestName?: string;
  sourceExamCode?: string;
  sortBySource?: boolean;
}): Promise<QuestionsResponse> {
  const qs = new URLSearchParams();
  if (params.domain) qs.set("domain", params.domain);
  if (params.difficulty && params.difficulty !== "any") qs.set("difficulty", params.difficulty);
  if (params.sourceReleaseYear) qs.set("source_release_year", String(params.sourceReleaseYear));
  if (params.sourceTestName) qs.set("source_test_name", params.sourceTestName);
  if (params.sourceExamCode) qs.set("source_exam_code", params.sourceExamCode);
  if (params.sortBySource) qs.set("sort_by_source", "true");
  qs.set("limit", String(params.limit ?? 20));
  qs.set("user_token", params.userToken);

  const res = await fetch(`${BASE}/api/questions?${qs}`, { headers: headers() });

  if (res.status === 403) throw new Error("INVALID_API_KEY");
  if (!res.ok) throw new Error(`fetchQuestions failed: ${res.status}`);
  return res.json();
}

export async function submitAnswer(body: {
  user_token: string;
  question_id: string;
  selected_option_label: string;
}): Promise<SubmitResult> {
  const res = await fetch(`${BASE}/api/submit`, {
    method: "POST",
    headers: { ...headers(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) throw new Error(`submitAnswer failed: ${res.status}`);
  return res.json();
}

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "./ui/button";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";
import { fetchFilterInventory } from "../api/inventory";
import { getUserToken } from "../lib/auth";

export type Domain = "grammar" | "reading" | "mixed";
export type Difficulty = "any" | "easy" | "medium" | "hard";
export type Mode = "practice" | "test";

export interface SessionParams {
  domain: Domain;
  difficulty: Difficulty;
  mode: Mode;
  count: number;
}

interface Props {
  onStart: (params: SessionParams) => void;
  loading?: boolean;
  error?: string | null;
}

const DIFFICULTY_OPTIONS: { value: Difficulty; label: string }[] = [
  { value: "any",    label: "Any" },
  { value: "easy",   label: "Easy" },
  { value: "medium", label: "Moderate" },
  { value: "hard",   label: "Hard" },
];

const COUNT_OPTIONS = [5, 10, 20];

const DOMAIN_OPTIONS: { value: Domain; label: string; description: string }[] = [
  { value: "mixed",   label: "Mixed",   description: "Grammar + Reading" },
  { value: "grammar", label: "Grammar", description: "Language & conventions" },
  { value: "reading", label: "Reading", description: "Craft & structure" },
];

function countBadge(n: number | undefined) {
  if (n === undefined) return null;
  return (
    <span className={`ml-1 text-xs font-normal ${n === 0 ? "text-destructive" : "text-muted-foreground"}`}>
      ({n})
    </span>
  );
}

export function SessionSetup({ onStart, loading, error }: Props) {
  const [activeTab, setActiveTab] = useState<Mode>("practice");

  // Practice filters
  const [domain, setDomain]   = useState<Domain>("mixed");
  const [difficulty, setDiff] = useState<Difficulty>("any");
  const [count, setCount]     = useState<number>(10);

  const { data: inv } = useQuery({
    queryKey: ["filter-inventory"],
    queryFn: () => fetchFilterInventory(getUserToken()),
    staleTime: 60_000,
    retry: 1,
  });

  const domainOptions = DOMAIN_OPTIONS.map((o) => {
    const total = o.value === "mixed" ? inv?.mixedTotal
                : o.value === "grammar" ? inv?.grammarTotal
                : inv?.readingTotal;
    const countSuffix = total !== undefined ? ` (${total})` : '';
    return {
      ...o,
      total,
      description: o.description + countSuffix,
    };
  });

  function renderError() {
    if (!error) return null;
    let msg = error;
    if (error === "INVALID_API_KEY") msg = "Invalid API key — check VITE_STUDENT_API_KEY in .env";
    else if (error.includes("Not authenticated")) msg = "Auth error — check VITE_TEST_USER_TOKEN in .env";
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3">
        {msg}
      </div>
    );
  }

  return (
    <div className="max-w-lg space-y-6">
      <div>
        <h1 className="text-2xl font-bold">DSAT Verbal Practice</h1>
        <p className="text-muted-foreground text-sm mt-1">Choose a mode to begin.</p>
      </div>

      {/* Mode tabs */}
      <div className="flex rounded-lg border overflow-hidden">
        {(["practice", "test"] as Mode[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setActiveTab(m)}
            className={`flex-1 py-2.5 text-sm font-medium capitalize transition-colors
              ${activeTab === m
                ? "bg-primary text-primary-foreground"
                : "hover:bg-accent text-muted-foreground"}`}
          >
            {m}
          </button>
        ))}
      </div>

      {/* PRACTICE panel */}
      {activeTab === "practice" && (
        <div className="space-y-6">
          {/* Domain */}
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">Domain</h2>
            <RadioGroup
              value={domain}
              onValueChange={(v) => setDomain(v as Domain)}
              className="grid grid-cols-3 gap-3"
            >
              {domainOptions.map((o) => (
                <label
                  key={o.value}
                  htmlFor={`domain-${o.value}`}
                  className={`flex flex-col gap-0.5 rounded-lg border p-3 cursor-pointer hover:bg-accent has-[:checked]:border-primary has-[:checked]:bg-accent ${o.total === 0 ? "opacity-50" : ""}`}
                >
                  <div className="flex items-center gap-2">
                    <RadioGroupItem value={o.value} id={`domain-${o.value}`} />
                    <span className="font-medium text-sm">
                      {o.label}{countBadge(o.total)}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground pl-6">{o.description}</span>
                </label>
              ))}
            </RadioGroup>
          </div>

          {/* Difficulty */}
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">Difficulty</h2>
            <RadioGroup
              value={difficulty}
              onValueChange={(v) => setDiff(v as Difficulty)}
              className="flex flex-wrap gap-3"
            >
              {DIFFICULTY_OPTIONS.map((o) => {
                const n = o.value === "any" ? inv?.mixedTotal : inv?.diffCounts?.[o.value];
                return (
                  <label
                    key={o.value}
                    htmlFor={`diff-${o.value}`}
                    className={`flex items-center gap-2 rounded-lg border px-4 py-2 cursor-pointer hover:bg-accent has-[:checked]:border-primary has-[:checked]:bg-accent ${n === 0 ? "opacity-50" : ""}`}
                  >
                    <RadioGroupItem value={o.value} id={`diff-${o.value}`} />
                    <span className="text-sm">{o.label}{n !== undefined && n !== inv?.mixedTotal && countBadge(n)}</span>
                  </label>
                );
              })}
            </RadioGroup>
          </div>

          {/* Count */}
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">Questions</h2>
            <div className="flex gap-3">
              {COUNT_OPTIONS.map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setCount(n)}
                  className={`w-16 h-10 rounded-lg border text-sm font-medium transition-colors
                    ${count === n ? "border-primary bg-primary text-primary-foreground" : "hover:bg-accent"}`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          {renderError()}

          <Button
            onClick={() => onStart({ domain, difficulty, mode: "practice", count })}
            disabled={loading}
            size="lg"
            className="w-full"
          >
            {loading ? "Loading…" : `Start Practice — ${count} Questions →`}
          </Button>
        </div>
      )}

      {/* TEST panel */}
      {activeTab === "test" && (
        <div className="space-y-6">
          <div className="rounded-lg border bg-muted/30 p-5 space-y-4">
            <div className="space-y-1">
              <h2 className="font-semibold text-base">Official Format</h2>
              <p className="text-sm text-muted-foreground">
                Mirrors the DSAT Reading &amp; Writing module experience.
              </p>
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              {[
                { label: "Questions", value: "33" },
                { label: "Time limit", value: "32 min" },
                { label: "Feedback", value: "None" },
              ].map(({ label, value }) => (
                <div key={label} className="space-y-0.5">
                  <div className="text-xl font-bold">{value}</div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wide">{label}</div>
                </div>
              ))}
            </div>
            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>Questions ordered by type — Craft &amp; Structure → Information &amp; Ideas → Conventions</li>
              <li>No hints or distractor explanations until after submission</li>
              <li>Session ends when time expires or all questions are answered</li>
            </ul>
          </div>

          {renderError()}

          <Button
            onClick={() => onStart({ domain: "mixed", difficulty: "any", mode: "test", count: 33 })}
            disabled={loading || (inv?.mixedTotal !== undefined && inv.mixedTotal < 33)}
            size="lg"
            className="w-full"
          >
            {loading ? "Loading…" : "Start Test →"}
          </Button>

          {inv?.mixedTotal !== undefined && inv.mixedTotal < 33 && (
            <p className="text-xs text-muted-foreground text-center">
              {inv.mixedTotal} questions available — 33 required for a full test
            </p>
          )}
        </div>
      )}
    </div>
  );
}

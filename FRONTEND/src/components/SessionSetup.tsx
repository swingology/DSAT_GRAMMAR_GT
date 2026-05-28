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

const MODE_OPTIONS: { value: Mode; label: string; description: string }[] = [
  { value: "practice", label: "Practice", description: "Feedback after each question" },
  { value: "test",     label: "Test",     description: "No hints — score at the end" },
];

function countLabel(n: number | undefined): string {
  if (n === undefined) return "";
  if (n === 0) return " (0)";
  return ` (${n})`;
}

export function SessionSetup({ onStart, loading, error }: Props) {
  const [domain, setDomain]   = useState<Domain>("mixed");
  const [difficulty, setDiff] = useState<Difficulty>("any");
  const [mode, setMode]       = useState<Mode>("practice");
  const [count, setCount]     = useState<number>(10);

  const { data: inv } = useQuery({
    queryKey: ["filter-inventory"],
    queryFn: () => fetchFilterInventory(getUserToken()),
    staleTime: 60_000,
    retry: 1,
  });

  const domainOptions = [
    { value: "mixed"   as Domain, label: "Mixed",   description: "Grammar + Reading", count: inv?.mixedTotal },
    { value: "grammar" as Domain, label: "Grammar",  description: "Language & conventions", count: inv?.grammarTotal },
    { value: "reading" as Domain, label: "Reading",  description: "Craft & structure", count: inv?.readingTotal },
  ];

  // Human-readable error: show the actual message rather than a generic override
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
    <div className="space-y-8 max-w-lg">
      <div>
        <h1 className="text-2xl font-bold">DSAT Verbal Practice</h1>
        <p className="text-muted-foreground text-sm mt-1">Configure your session and start drilling.</p>
      </div>

      {/* Mode */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">Mode</h2>
        <RadioGroup
          value={mode}
          onValueChange={(v) => setMode(v as Mode)}
          className="grid grid-cols-2 gap-3"
        >
          {MODE_OPTIONS.map((o) => (
            <label
              key={o.value}
              htmlFor={`mode-${o.value}`}
              className="flex flex-col gap-0.5 rounded-lg border p-3 cursor-pointer hover:bg-accent has-[:checked]:border-primary has-[:checked]:bg-accent"
            >
              <div className="flex items-center gap-2">
                <RadioGroupItem value={o.value} id={`mode-${o.value}`} />
                <span className="font-medium text-sm">{o.label}</span>
              </div>
              <span className="text-xs text-muted-foreground pl-6">{o.description}</span>
            </label>
          ))}
        </RadioGroup>
      </div>

      {/* Domain */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">Domain</h2>
        <RadioGroup
          value={domain}
          onValueChange={(v) => setDomain(v as Domain)}
          className="grid grid-cols-3 gap-3"
        >
          {domainOptions.map((o) => {
            const empty = o.count === 0;
            return (
              <label
                key={o.value}
                htmlFor={`domain-${o.value}`}
                className={`flex flex-col gap-0.5 rounded-lg border p-3 cursor-pointer hover:bg-accent has-[:checked]:border-primary has-[:checked]:bg-accent ${empty ? "opacity-50" : ""}`}
              >
                <div className="flex items-center gap-2">
                  <RadioGroupItem value={o.value} id={`domain-${o.value}`} />
                  <span className="font-medium text-sm">
                    {o.label}
                    <span className="text-xs text-muted-foreground font-normal">{countLabel(o.count)}</span>
                  </span>
                </div>
                <span className="text-xs text-muted-foreground pl-6">{o.description}</span>
              </label>
            );
          })}
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
            const diffCount = o.value === "any" ? inv?.mixedTotal : inv?.diffCounts?.[o.value];
            const empty = diffCount === 0;
            return (
              <label
                key={o.value}
                htmlFor={`diff-${o.value}`}
                className={`flex items-center gap-2 rounded-lg border px-4 py-2 cursor-pointer hover:bg-accent has-[:checked]:border-primary has-[:checked]:bg-accent ${empty ? "opacity-50" : ""}`}
              >
                <RadioGroupItem value={o.value} id={`diff-${o.value}`} />
                <span className="text-sm">
                  {o.label}
                  {diffCount !== undefined && <span className="text-xs text-muted-foreground ml-1">{countLabel(diffCount)}</span>}
                </span>
              </label>
            );
          })}
        </RadioGroup>
      </div>

      {/* Question count */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">Questions</h2>
        <div className="flex gap-3">
          {COUNT_OPTIONS.map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => setCount(n)}
              className={`w-16 h-10 rounded-lg border text-sm font-medium transition-colors
                ${count === n
                  ? "border-primary bg-primary text-primary-foreground"
                  : "hover:bg-accent"}`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      {renderError()}

      <Button
        onClick={() => onStart({ domain, difficulty, mode, count })}
        disabled={loading}
        size="lg"
        className="w-full"
      >
        {loading
          ? "Loading questions…"
          : mode === "test"
          ? `Start Test — ${count} Questions →`
          : `Start Practice — ${count} Questions →`}
      </Button>
    </div>
  );
}

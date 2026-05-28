import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "./ui/button";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";
import { fetchFilterInventory } from "../api/inventory";
import { getUserToken } from "../lib/auth";

export type Domain = "grammar" | "reading" | "mixed";
export type Difficulty = "any" | string;

interface Props {
  onStart: (domain: Domain, difficulty: Difficulty) => void;
  loading?: boolean;
  error?: string | null;
}

export function SessionSetup({ onStart, loading, error }: Props) {
  const [domain, setDomain] = useState<Domain>("mixed");
  const [difficulty, setDifficulty] = useState<Difficulty>("any");

  const { data: inv, isLoading: invLoading } = useQuery({
    queryKey: ["filter-inventory"],
    queryFn: () => fetchFilterInventory(getUserToken()),
    staleTime: 60_000,
    retry: 1,
  });

  // Reset domain if current selection has no inventory
  useEffect(() => {
    if (!inv) return;
    if (domain === "grammar" && !inv.hasGrammar) setDomain("mixed");
    if (domain === "reading" && !inv.hasReading) setDomain("mixed");
  }, [inv, domain]);

  // Reset difficulty if no longer in available list
  useEffect(() => {
    if (!inv || difficulty === "any") return;
    if (!inv.difficulties.includes(difficulty)) setDifficulty("any");
  }, [inv, difficulty]);

  const domainOptions: { value: Domain; label: string; available: boolean }[] = [
    { value: "mixed", label: "Mixed", available: inv?.hasMixed ?? true },
    { value: "grammar", label: "Grammar", available: inv?.hasGrammar ?? true },
    { value: "reading", label: "Reading", available: inv?.hasReading ?? true },
  ];

  const difficultyOptions: { value: Difficulty; label: string }[] = [
    { value: "any", label: "Any" },
    ...(inv?.difficulties ?? ["easy", "medium", "hard"]).map((d) => ({
      value: d,
      label: d.charAt(0).toUpperCase() + d.slice(1),
    })),
  ];

  const errorMessage = error
    ? error === "INVALID_API_KEY"
      ? "Invalid API key — check VITE_STUDENT_API_KEY in .env"
      : error.includes("No active questions")
      ? "No active questions for these filters. Try a different selection."
      : `Error: ${error}`
    : null;

  return (
    <div className="space-y-8 max-w-lg">
      <div>
        <h2 className="text-lg font-semibold mb-3">Domain</h2>
        {invLoading ? (
          <div className="flex gap-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 w-24 rounded-lg bg-muted animate-pulse" />
            ))}
          </div>
        ) : (
          <RadioGroup
            value={domain}
            onValueChange={(v) => setDomain(v as Domain)}
            className="flex flex-wrap gap-3"
          >
            {domainOptions
              .filter((o) => o.available)
              .map((o) => (
                <label
                  key={o.value}
                  htmlFor={`domain-${o.value}`}
                  className="flex items-center gap-2 rounded-lg border px-4 py-2 cursor-pointer hover:bg-accent has-[:checked]:border-primary has-[:checked]:bg-accent"
                >
                  <RadioGroupItem value={o.value} id={`domain-${o.value}`} />
                  {o.label}
                </label>
              ))}
          </RadioGroup>
        )}
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-3">Difficulty</h2>
        {invLoading ? (
          <div className="flex gap-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 w-20 rounded-lg bg-muted animate-pulse" />
            ))}
          </div>
        ) : (
          <RadioGroup
            value={difficulty}
            onValueChange={setDifficulty}
            className="flex flex-wrap gap-3"
          >
            {difficultyOptions.map((o) => (
              <label
                key={o.value}
                htmlFor={`diff-${o.value}`}
                className="flex items-center gap-2 rounded-lg border px-4 py-2 cursor-pointer hover:bg-accent has-[:checked]:border-primary has-[:checked]:bg-accent"
              >
                <RadioGroupItem value={o.value} id={`diff-${o.value}`} />
                {o.label}
              </label>
            ))}
          </RadioGroup>
        )}
      </div>

      {errorMessage && (
        <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3">
          {errorMessage}
        </div>
      )}

      <Button
        onClick={() => onStart(domain, difficulty)}
        disabled={loading || invLoading}
        size="lg"
      >
        {loading ? "Loading questions…" : "Start Drill →"}
      </Button>
    </div>
  );
}

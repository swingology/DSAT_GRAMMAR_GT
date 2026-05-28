import { useState } from "react";
import { Button } from "./ui/button";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";

type Domain = "grammar" | "reading" | "mixed";
type Difficulty = "easy" | "medium" | "hard" | "any";

interface Props {
  onStart: (domain: Domain, difficulty: Difficulty) => void;
  loading?: boolean;
  error?: string | null;
}

export function SessionSetup({ onStart, loading, error }: Props) {
  const [domain, setDomain] = useState<Domain>("mixed");
  const [difficulty, setDifficulty] = useState<Difficulty>("any");

  return (
    <div className="space-y-8 max-w-lg">
      <div>
        <h2 className="text-lg font-semibold mb-3">Domain</h2>
        <RadioGroup
          value={domain}
          onValueChange={(v) => setDomain(v as Domain)}
          className="flex flex-wrap gap-3"
        >
          {(["mixed", "grammar", "reading"] as Domain[]).map((d) => (
            <label
              key={d}
              htmlFor={`domain-${d}`}
              className="flex items-center gap-2 rounded-lg border px-4 py-2 cursor-pointer capitalize hover:bg-accent has-[:checked]:border-primary has-[:checked]:bg-accent"
            >
              <RadioGroupItem value={d} id={`domain-${d}`} />
              {d}
            </label>
          ))}
        </RadioGroup>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-3">Difficulty</h2>
        <RadioGroup
          value={difficulty}
          onValueChange={(v) => setDifficulty(v as Difficulty)}
          className="flex flex-wrap gap-3"
        >
          {(["any", "easy", "medium", "hard"] as Difficulty[]).map((d) => (
            <label
              key={d}
              htmlFor={`diff-${d}`}
              className="flex items-center gap-2 rounded-lg border px-4 py-2 cursor-pointer capitalize hover:bg-accent has-[:checked]:border-primary has-[:checked]:bg-accent"
            >
              <RadioGroupItem value={d} id={`diff-${d}`} />
              {d}
            </label>
          ))}
        </RadioGroup>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3">
          {error === "INVALID_API_KEY"
            ? "Invalid API key — check VITE_STUDENT_API_KEY in .env"
            : error.includes("No active questions") || error.includes("0")
            ? "No active questions found for these filters. Try a different domain or difficulty."
            : `Error: ${error}`}
        </div>
      )}

      <Button onClick={() => onStart(domain, difficulty)} disabled={loading} size="lg">
        {loading ? "Loading questions…" : "Start Drill →"}
      </Button>
    </div>
  );
}

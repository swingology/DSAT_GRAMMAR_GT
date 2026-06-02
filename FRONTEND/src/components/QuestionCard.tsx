import { useState } from "react";
import type { Question, SubmitResult } from "../types";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { cn } from "../lib/utils";

// ── Colour palette — assigned deterministically by key name hash ──────────────
const KEY_PALETTE = [
  { bg: "#eff6ff", border: "#3b82f6", text: "#1d4ed8" },
  { bg: "#f0fdf4", border: "#22c55e", text: "#15803d" },
  { bg: "#fdf4ff", border: "#a855f7", text: "#7e22ce" },
  { bg: "#fff7ed", border: "#f97316", text: "#c2410c" },
  { bg: "#ecfeff", border: "#06b6d4", text: "#0e7490" },
  { bg: "#fefce8", border: "#eab308", text: "#a16207" },
  { bg: "#f5f3ff", border: "#8b5cf6", text: "#6d28d9" },
  { bg: "#fff1f2", border: "#f43f5e", text: "#be123c" },
  { bg: "#f0fdfa", border: "#14b8a6", text: "#0f766e" },
  { bg: "#fef9c3", border: "#ca8a04", text: "#854d0e" },
] as const;

function keyColor(key: string) {
  let h = 0;
  for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) & 0x7fffffff;
  return KEY_PALETTE[h % KEY_PALETTE.length];
}

function formatKey(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// ── Token-based passage ───────────────────────────────────────────────────────
interface PassageTextProps {
  question: Question;
  activeKeys: Set<string>;
  filledText?: string;
  isCorrect?: boolean;
}

function PassageText({ question, activeKeys, filledText, isCorrect }: PassageTextProps) {
  const tokens = question.passage_tokens;
  const base = "border-l-4 border-primary/30 bg-muted/50 rounded-r-lg p-4 text-sm leading-relaxed";

  if (!tokens || tokens.length === 0) {
    return (
      <blockquote className={cn(base, "whitespace-pre-wrap")}>
        {question.current_passage_text}
      </blockquote>
    );
  }

  return (
    <blockquote className={base}>
      {tokens.map((token, i) => {
        const word = (token.word ?? token.text ?? "") as string;
        const tags = (token.tags ?? []) as string[];
        const isBlank = Boolean(token.is_blank ?? token.isBlank);
        const matchingKey = tags.find((t) => activeKeys.has(t));
        const c = matchingKey ? keyColor(matchingKey) : null;
        const blankHighlightStyle = c
          ? {
              boxShadow: `0 0 0 3px ${c.bg}`,
              borderColor: c.border,
            }
          : undefined;

        if (isBlank) {
          if (filledText === undefined) {
            return (
              <span
                key={i}
                className="inline-block px-3 py-0.5 mx-0.5 rounded border-2 border-dashed border-muted-foreground/40 text-muted-foreground font-semibold bg-muted/40"
                style={blankHighlightStyle}
              >
                ________
              </span>
            );
          }
          return (
            <span
              key={i}
              className={cn(
                "inline-block px-2 py-0.5 mx-0.5 rounded border-2 font-semibold",
                isCorrect
                  ? "border-green-500 bg-green-50 text-green-800"
                  : "border-red-400 bg-red-50 text-red-800"
              )}
              style={blankHighlightStyle}
            >
              {filledText}
            </span>
          );
        }

        return (
          <span
            key={i}
            style={
              c
                ? {
                    backgroundColor: c.bg,
                    borderBottom: `2.5px solid ${c.border}`,
                    padding: "1px 3px",
                    borderRadius: "2px",
                  }
                : undefined
            }
          >
            {word}
          </span>
        );
      })}
    </blockquote>
  );
}

// ── Grammar key interactive panel ─────────────────────────────────────────────
interface GrammarKeyPanelProps {
  question: Question;
  activeKeys: Set<string>;
  onToggle: (key: string) => void;
  onFindTraps: () => void;
  onClear: () => void;
}

function GrammarKeyPanel({ question, activeKeys, onToggle, onFindTraps, onClear }: GrammarKeyPanelProps) {
  const tokens = question.passage_tokens;
  if (!tokens || tokens.length === 0) return null;

  // Collect all unique tags from passage tokens
  const allTags = new Set<string>();
  tokens.forEach((t) => ((t.tags ?? []) as string[]).forEach((tag) => allTags.add(tag)));
  if (allTags.size === 0) return null;

  const focusTags = [question.grammar_focus_key, question.grammar_role_key]
    .filter((k): k is string => !!k && allTags.has(k));
  const anatomyTags = [...allTags].filter((t) => !focusTags.includes(t));

  return (
    <div className="rounded-lg border bg-muted/20 p-4 space-y-3 text-sm">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Passage Grammar Analysis
        </span>
        <div className="flex gap-2">
          {focusTags.length > 0 && (
            <button
              onClick={onFindTraps}
              className="text-xs px-3 py-1 rounded-full bg-primary text-primary-foreground font-semibold hover:opacity-80 transition-opacity"
            >
              Find traps
            </button>
          )}
          {activeKeys.size > 0 && (
            <button
              onClick={onClear}
              className="text-xs px-3 py-1 rounded-full border border-border text-muted-foreground hover:text-foreground transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Question focus keys */}
      {focusTags.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-xs uppercase tracking-wide font-semibold text-muted-foreground">
            Question Focus
          </div>
          <div className="flex flex-wrap gap-2">
            {focusTags.map((key) => {
              const c = keyColor(key);
              const active = activeKeys.has(key);
              return (
                <button
                  key={key}
                  onClick={() => onToggle(key)}
                  className="text-xs px-3 py-1.5 rounded-full border-2 font-semibold transition-all hover:-translate-y-px"
                  style={{
                    borderColor: c.border,
                    backgroundColor: active ? c.border : c.bg,
                    color: active ? "#fff" : c.text,
                  }}
                >
                  {formatKey(key)}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Sentence anatomy tags */}
      {anatomyTags.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-xs uppercase tracking-wide font-semibold text-muted-foreground">
            Sentence Elements
          </div>
          <div className="flex flex-wrap gap-2">
            {anatomyTags.map((key) => {
              const c = keyColor(key);
              const active = activeKeys.has(key);
              return (
                <button
                  key={key}
                  onClick={() => onToggle(key)}
                  className="text-xs px-3 py-1.5 rounded-full border font-medium transition-all hover:-translate-y-px"
                  style={{
                    borderColor: active ? c.border : "#d1d5db",
                    backgroundColor: active ? c.bg : "#fff",
                    color: active ? c.text : "#6b7280",
                  }}
                >
                  {formatKey(key)}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main QuestionCard ─────────────────────────────────────────────────────────
interface Props {
  question: Question;
  questionNumber: number;
  total: number;
  mode?: "practice" | "test";
  onSubmitAnswer: (label: string) => Promise<SubmitResult>;
  onNext: () => void;
}

export function QuestionCard({ question, questionNumber, total, mode = "practice", onSubmitAnswer, onNext }: Props) {
  const isPractice = mode === "practice";
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeKeys, setActiveKeys] = useState<Set<string>>(new Set());

  function toggleKey(key: string) {
    setActiveKeys((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  function findTraps() {
    const traps = [
      question.grammar_focus_key,
      question.grammar_role_key,
      question.syntactic_trap_key,
    ].filter(Boolean) as string[];
    setActiveKeys(new Set(traps));
  }

  async function handleSubmit() {
    if (!selected) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await onSubmitAnswer(selected);
      setResult(res);
      // Auto-highlight the question's grammar keys on submit
      const traps = [
        question.grammar_focus_key,
        question.grammar_role_key,
        question.syntactic_trap_key,
      ].filter(Boolean) as string[];
      if (traps.length > 0) setActiveKeys(new Set(traps));
    } catch {
      setError("Submission failed — please try again");
    } finally {
      setSubmitting(false);
    }
  }

  function handleNext() {
    setSelected(null);
    setResult(null);
    setError(null);
    setActiveKeys(new Set());
    onNext();
  }

  // Resolve filled blank text for token rendering
  const selectedOption = question.options.find((o) => o.label === selected);
  const filledText = result ? (selectedOption?.text ?? selected ?? undefined) : undefined;

  return (
    <div className="space-y-6">
      {/* Progress */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>Question {questionNumber} of {total}</span>
        <span className="text-xs uppercase tracking-wide font-mono">
          {question.grammar_focus_key ?? question.reading_focus_key ?? question.content_origin}
        </span>
      </div>

      {/* Passage */}
      {question.current_passage_text && (
        <PassageText
          question={question}
          activeKeys={activeKeys}
          filledText={filledText}
          isCorrect={result?.is_correct}
        />
      )}

      {/* Grammar key panel */}
      {isPractice && question.passage_tokens?.length ? (
        <GrammarKeyPanel
          question={question}
          activeKeys={activeKeys}
          onToggle={toggleKey}
          onFindTraps={findTraps}
          onClear={() => setActiveKeys(new Set())}
        />
      ) : null}

      {/* Question stem */}
      <p className="text-base font-medium leading-relaxed">{question.current_question_text}</p>

      {/* Options */}
      <RadioGroup
        value={selected ?? ""}
        onValueChange={setSelected}
        disabled={!!result || submitting}
        className="space-y-2"
      >
        {question.options.map((opt) => {
          const isSelected = selected === opt.label;
          const showCorrect = result?.is_correct && isSelected;
          const showWrong = result && !result.is_correct && isSelected;

          return (
            <div key={opt.label} className="space-y-1">
              <label
                htmlFor={`opt-${opt.label}`}
                className={cn(
                  "flex items-start gap-3 rounded-lg border p-3 cursor-pointer transition-colors",
                  !result && "hover:bg-accent",
                  isSelected && !result && "border-primary bg-accent",
                  showCorrect && "border-green-500 bg-green-50 text-green-900",
                  showWrong && "border-destructive bg-red-50 text-red-900",
                  result && !isSelected && "opacity-50 cursor-default"
                )}
              >
                <RadioGroupItem value={opt.label} id={`opt-${opt.label}`} className="mt-0.5 shrink-0" />
                <span className="text-sm">
                  <span className="font-semibold mr-1">{opt.label}.</span>
                  {opt.text}
                </span>
              </label>

              {/* Per-option distractor analysis */}
              {isPractice && result && showWrong && opt.distractor_type_key && (
                <div className="ml-10 rounded-md bg-orange-50 border border-orange-200 px-3 py-2 text-xs space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-orange-800">Trap:</span>
                    <Badge variant="outline" className="text-orange-700 border-orange-300 text-xs">
                      {formatKey(opt.distractor_type_key)}
                    </Badge>
                  </div>
                  {opt.why_plausible && (
                    <p className="text-orange-700"><span className="font-medium">Why tempting: </span>{opt.why_plausible}</p>
                  )}
                  {opt.why_wrong && (
                    <p className="text-orange-800"><span className="font-medium">Why wrong: </span>{opt.why_wrong}</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </RadioGroup>

      {/* Submission feedback */}
      {isPractice && result && (
        <div
          className={cn(
            "rounded-lg px-4 py-3 text-sm font-medium",
            result.is_correct
              ? "bg-green-100 text-green-800 border border-green-200"
              : "bg-red-100 text-red-800 border border-red-200"
          )}
        >
          {result.is_correct ? "Correct ✓" : "Incorrect ✗"}
        </div>
      )}

      {/* Post-answer review panel */}
      {isPractice && result && (
        <div className="rounded-lg border bg-muted/30 p-4 space-y-3 text-sm">
          <div className="flex flex-wrap gap-2">
            {question.grammar_focus_key && (
              <Badge variant="secondary">{formatKey(question.grammar_focus_key)}</Badge>
            )}
            {question.grammar_role_key && (
              <Badge variant="secondary">{formatKey(question.grammar_role_key)}</Badge>
            )}
            {question.reading_focus_key && (
              <Badge variant="secondary">{formatKey(question.reading_focus_key)}</Badge>
            )}
            {question.difficulty_overall && (
              <Badge variant="outline" className="capitalize">{question.difficulty_overall}</Badge>
            )}
            {question.reasoning_trap_key && (
              <Badge variant="destructive" className="text-xs">
                Trap: {formatKey(question.reasoning_trap_key)}
              </Badge>
            )}
          </div>

          {question.explanation_short && (
            <p className="text-muted-foreground leading-relaxed">{question.explanation_short}</p>
          )}

          {question.solver_pattern_key && (
            <p className="text-xs text-muted-foreground">
              <span className="font-semibold">Strategy: </span>
              {formatKey(question.solver_pattern_key)}
            </p>
          )}
        </div>
      )}

      {/* Error */}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {/* Actions */}
      <div className="flex justify-end gap-3">
        {!result ? (
          <Button onClick={handleSubmit} disabled={!selected || submitting}>
            {submitting ? "Submitting…" : "Submit Answer"}
          </Button>
        ) : (
          <Button onClick={handleNext}>Next Question →</Button>
        )}
      </div>
    </div>
  );
}

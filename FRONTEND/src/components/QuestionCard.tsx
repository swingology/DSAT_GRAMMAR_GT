import { useState } from "react";
import type { Question, SubmitResult } from "../types";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { cn } from "../lib/utils";

interface Props {
  question: Question;
  questionNumber: number;
  total: number;
  onSubmitAnswer: (label: string) => Promise<SubmitResult>;
  onNext: () => void;
}

function formatKey(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function QuestionCard({ question, questionNumber, total, onSubmitAnswer, onNext }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!selected) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await onSubmitAnswer(selected);
      setResult(res);
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
    onNext();
  }

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
        <blockquote className="border-l-4 border-primary/30 bg-muted/50 rounded-r-lg p-4 text-sm leading-relaxed whitespace-pre-wrap">
          {question.current_passage_text}
        </blockquote>
      )}

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

              {/* Per-option distractor analysis — shown after submission for selected wrong answer */}
              {result && showWrong && opt.distractor_type_key && (
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
      {result && (
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
      {result && (
        <div className="rounded-lg border bg-muted/30 p-4 space-y-3 text-sm">
          {/* Metadata badges */}
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

          {/* Explanation */}
          {question.explanation_short && (
            <p className="text-muted-foreground leading-relaxed">{question.explanation_short}</p>
          )}

          {/* Solver strategy */}
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

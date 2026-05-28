import { useState } from "react";
import type { Question, SubmitResult } from "../types";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";
import { Button } from "./ui/button";
import { cn } from "../lib/utils";

interface Props {
  question: Question;
  questionNumber: number;
  total: number;
  onSubmitAnswer: (label: string) => Promise<SubmitResult>;
  onNext: () => void;
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
        <span className="text-xs uppercase tracking-wide">
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
        className="space-y-3"
      >
        {question.options.map((opt) => {
          const isSelected = selected === opt.label;
          const showCorrect = result && result.is_correct && isSelected;
          const showWrong = result && !result.is_correct && isSelected;

          return (
            <label
              key={opt.label}
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
          );
        })}
      </RadioGroup>

      {/* Feedback */}
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

      {/* Error */}
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

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

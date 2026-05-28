import { useState, useEffect, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { fetchQuestions, submitAnswer } from "../api/questions";
import { getUserToken } from "../lib/auth";
import { queryClient } from "../lib/query";
import { SessionSetup, type SessionParams } from "../components/SessionSetup";
import { QuestionCard } from "../components/QuestionCard";
import { SessionComplete } from "../components/SessionComplete";
import { TestTimer } from "../components/TestTimer";
import type { Question, SubmitResult } from "../types";

type Phase = "setup" | "drilling" | "complete";

// DSAT question family ordering: Craft & Structure → Information & Ideas → Expression → Conventions
const FAMILY_ORDER: Record<string, number> = {
  craft_and_structure:   1,
  information_and_ideas: 2,
  expression_of_ideas:   3,
  conventions_grammar:   4,
};

function sortDSAT(questions: Question[]): Question[] {
  return [...questions].sort((a, b) => {
    const fa = FAMILY_ORDER[a.question_family_key ?? ""] ?? 5;
    const fb = FAMILY_ORDER[b.question_family_key ?? ""] ?? 5;
    if (fa !== fb) return fa - fb;
    return (a.source_question_number ?? 99) - (b.source_question_number ?? 99);
  });
}

const TEST_DURATION = 32 * 60; // 32 minutes in seconds

export function PracticePage() {
  const [phase, setPhase]           = useState<Phase>("setup");
  const [questions, setQuestions]   = useState<Question[]>([]);
  const [index, setIndex]           = useState(0);
  const [correct, setCorrect]       = useState(0);
  const [mode, setMode]             = useState<"practice" | "test">("practice");
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [fetchLoading, setFetchLoading] = useState(false);
  const [timeLeft, setTimeLeft]     = useState(TEST_DURATION);
  const [timeTaken, setTimeTaken]   = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Countdown timer — only active during test drilling
  useEffect(() => {
    if (phase !== "drilling" || mode !== "test") return;

    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current!);
          setTimeTaken(TEST_DURATION);
          setPhase("complete");
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [phase, mode]);

  const submitMutation = useMutation({
    mutationFn: submitAnswer,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["stats"] }),
  });

  async function handleStart({ domain, difficulty, mode: selectedMode, count }: SessionParams) {
    setFetchLoading(true);
    setFetchError(null);
    try {
      const token = getUserToken();
      const data = await fetchQuestions({
        domain: domain === "mixed" ? undefined : domain,
        difficulty: difficulty === "any" ? undefined : difficulty,
        limit: count,
        userToken: token,
      });

      if (!data.items || data.items.length === 0) {
        setFetchError("No questions available for these filters. Try a different selection.");
        return;
      }

      const ordered = selectedMode === "test" ? sortDSAT(data.items) : data.items;

      setQuestions(ordered);
      setIndex(0);
      setCorrect(0);
      setMode(selectedMode);
      setTimeLeft(TEST_DURATION);
      setTimeTaken(0);
      setPhase("drilling");
    } catch (e) {
      setFetchError((e as Error).message);
    } finally {
      setFetchLoading(false);
    }
  }

  async function handleSubmitAnswer(label: string): Promise<SubmitResult> {
    const token = getUserToken();
    const question = questions[index];
    const result = await submitMutation.mutateAsync({
      user_token: token,
      question_id: question.id,
      selected_option_label: label,
    });
    if (result.is_correct) setCorrect((c) => c + 1);
    return result;
  }

  function handleNext() {
    if (index + 1 >= questions.length) {
      if (timerRef.current) clearInterval(timerRef.current);
      setTimeTaken(TEST_DURATION - timeLeft);
      setPhase("complete");
    } else {
      setIndex((i) => i + 1);
    }
  }

  function handleRestart() {
    if (timerRef.current) clearInterval(timerRef.current);
    setPhase("setup");
    setQuestions([]);
    setIndex(0);
    setCorrect(0);
    setTimeLeft(TEST_DURATION);
    setTimeTaken(0);
  }

  if (phase === "setup") {
    return <SessionSetup onStart={handleStart} loading={fetchLoading} error={fetchError} />;
  }

  if (phase === "complete") {
    return (
      <SessionComplete
        answered={questions.length}
        correct={correct}
        timeTaken={mode === "test" ? timeTaken : undefined}
        onRestart={handleRestart}
      />
    );
  }

  const question = questions[index];
  if (!question) return null;

  return (
    <div className="space-y-4">
      {mode === "test" && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            Question {index + 1} of {questions.length}
          </span>
          <TestTimer secondsLeft={timeLeft} />
        </div>
      )}
      <QuestionCard
        question={question}
        questionNumber={index + 1}
        total={questions.length}
        mode={mode}
        onSubmitAnswer={handleSubmitAnswer}
        onNext={handleNext}
      />
    </div>
  );
}

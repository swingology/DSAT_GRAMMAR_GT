import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { fetchQuestions, submitAnswer } from "../api/questions";
import { getUserToken } from "../lib/auth";
import { queryClient } from "../lib/query";
import { SessionSetup } from "../components/SessionSetup";
import { QuestionCard } from "../components/QuestionCard";
import { SessionComplete } from "../components/SessionComplete";
import type { Question, SubmitResult } from "../types";

type Phase = "setup" | "drilling" | "complete";
type Domain = "grammar" | "reading" | "mixed";
type Difficulty = "easy" | "medium" | "hard" | "any";

export function PracticePage() {
  const [phase, setPhase] = useState<Phase>("setup");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [index, setIndex] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [fetchLoading, setFetchLoading] = useState(false);

  const submitMutation = useMutation({
    mutationFn: submitAnswer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });

  async function handleStart(domain: Domain, difficulty: Difficulty) {
    setFetchLoading(true);
    setFetchError(null);
    try {
      const token = getUserToken();
      const data = await fetchQuestions({
        domain: domain === "mixed" ? undefined : domain,
        difficulty: difficulty === "any" ? undefined : difficulty,
        limit: 20,
        userToken: token,
      });

      if (!data.items || data.items.length === 0) {
        setFetchError("No active questions found for these filters. Try a different domain or difficulty.");
        return;
      }

      setQuestions(data.items);
      setIndex(0);
      setCorrect(0);
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
      setPhase("complete");
    } else {
      setIndex((i) => i + 1);
    }
  }

  function handleRestart() {
    setPhase("setup");
    setQuestions([]);
    setIndex(0);
    setCorrect(0);
  }

  if (phase === "setup") {
    return (
      <SessionSetup
        onStart={handleStart}
        loading={fetchLoading}
        error={fetchError}
      />
    );
  }

  if (phase === "complete") {
    return (
      <SessionComplete
        answered={questions.length}
        correct={correct}
        onRestart={handleRestart}
      />
    );
  }

  const question = questions[index];
  if (!question) return null;

  return (
    <QuestionCard
      question={question}
      questionNumber={index + 1}
      total={questions.length}
      onSubmitAnswer={handleSubmitAnswer}
      onNext={handleNext}
    />
  );
}

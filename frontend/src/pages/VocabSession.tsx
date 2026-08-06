import React, { useState, useRef } from "react";
import { useInfiniteQuery, useMutation } from "@tanstack/react-query";

import type { WordPair, WordResults, VocabResults } from "../types";
import { fetchSession, fetchWords, sendVocabResults } from "../api";
import { calcIncorrectInput } from "../utils";

function VocabControl({ onStart }: { onStart: () => void }) {
  return (
    <div className="flex justify-center bg-[#dddddd] w-120 mx-auto px-10 py-5">
      <div className="flex flex-col text-[14px] w-90">
        <h1 className="text-[28px] font-bold">Vocab Session</h1>
        <p className="mb-4">Optimal words to review.</p>
        <button
          onClick={() => onStart()}
          className="border px-6 py-1 mt-4 rounded cursor-pointer bg-gray-100 hover:bg-[#dddddd] active:bg-gray-200"
        >
          Start Session
        </button>
      </div>
    </div>
  );
}

function WordCard({
  wordPair,
  inputText,
  onKeyDown,
  onInputChange,
}: {
  wordPair: WordPair;
  inputText: string;
  onKeyDown: (e: React.KeyboardEvent) => void;
  onInputChange: (value: string) => void;
}) {
  const targetWord = wordPair.target;
  const sourceWord = wordPair.source;

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-8 pb-48">
      <div className="text-center">
        <h1 className="text-4xl font-medium tracking-wide">{targetWord}</h1>
        <p>{sourceWord}</p>
      </div>
      {/* Full event object needed onKeyDown to disable default Tab behaviour*/}
      <input
        type="text"
        value={inputText}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={onKeyDown} // For non-value keys (esc, tab) and keystroke history recording
        className="bg-transparent border-t border-b text-center border-gray-500 outline-none w-64 text-xl"
      />
    </div>
  );
}

export default function VocabSession() {
  const [inputText, setInputText] = useState<string>("");
  const [wordIndex, setWordIndex] = useState(0);

  const sessionPosition = useRef<number>(1);
  const keystrokes = useRef<string>("");
  const wordShownTime = useRef<number>(Date.now());

  const { mutate: sessionMutate, data: sessionId } = useMutation({
    mutationFn: () => fetchSession({ bound_type: "time", bound_value: 120 }),
  });

  const { data: wordsData, fetchNextPage } = useInfiniteQuery({
    queryKey: ["words"],
    queryFn: () => fetchWords(),
    initialPageParam: 0,
    getNextPageParam: (_, __, lastPageParam) => lastPageParam + 1,
    staleTime: Infinity, // Prevent background refetch mid-session (e.g window refocus)
  });

  const words = wordsData?.pages.flat() ?? [];

  const currentWord: WordPair | undefined = words[wordIndex];

  function startSession() {
    sessionMutate();
    sessionPosition.current = 1;
  }

  async function advanceWord() {
    setInputText("");
    keystrokes.current = "";
    sessionPosition.current++;

    // New time needed to calculate how long they took to answer
    wordShownTime.current = Date.now();

    // Increment the word index to advance the word
    const nextWordIndex = wordIndex + 1;
    setWordIndex(nextWordIndex);

    // Append new batch if falls below threshold
    if (words.length - nextWordIndex <= 3) {
      fetchNextPage();
    }
  }

  function buildVocabResults(
    currentWord: WordPair,
    session: number,
    skipped: boolean = false,
  ): VocabResults {
    const word_id = currentWord.id;
    const response_time_ms = Date.now() - wordShownTime.current;
    const answered_at = new Date().toISOString();
    const raw_keystrokes = calcIncorrectInput(
      currentWord.source,
      keystrokes.current,
    );
    const session_position = sessionPosition.current;

    let status: string;
    if (skipped) {
      status = "skipped";
    } else {
      status = raw_keystrokes === null ? "correct_first_try" : "corrected";
    }

    // Pack results for the words into one type
    const wordResults: WordResults = {
      word_id,
      response_time_ms,
      answered_at,
      raw_keystrokes,
      status,
      session_position,
    };

    // Pack multiple results for the words into one type to send over api
    const vocabResults: VocabResults = {
      session_id: session,
      word_results: [wordResults],
    };

    return vocabResults;
  }

  async function handleInputChange(input: string) {
    if (!currentWord || !sessionId) return; // Defensive

    setInputText(input);

    // Check whether input matches the answer
    if (input === currentWord.source) {
      const vocabResults = buildVocabResults(currentWord, sessionId);
      await advanceWord(); // Timer is reset in advanceWord - therefore placed before sendVocabResults (so its not waiting) and after vocabResults is built (else time sent immediately after started)
      await sendVocabResults(vocabResults);
    }
  }

  async function handleKeyDown(e: React.KeyboardEvent) {
    if (!currentWord || !sessionId) return;

    const key = e.key;
    if (key === "Escape" || key === "Tab") {
      e.preventDefault();

      // Build results before advancing to capture response time accurately since time updates on advanceWord
      const skipped = true;
      const vocabResults = buildVocabResults(currentWord, sessionId, skipped);
      await advanceWord(); // advanceWord before network request to priorise UI speed
      await sendVocabResults(vocabResults);
    }

    // Filter out meaningless keys, replace Backspace with a clean and distinct symbol
    if (key.length !== 1 && key !== "Backspace") return;
    const recorded = key === "Backspace" ? "⌫" : key;

    // Update the ref
    keystrokes.current = keystrokes.current + recorded;
  }

  // There will only be a session ID after the user has clicked the start button. Having a separate state for the started would cause a race condition
  if (!sessionId) {
    return <VocabControl onStart={() => startSession()} />;
  }

  // Loading check is after the conditional checking for session - loading will happen in the background before the user presses start button
  if (!currentWord) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <WordCard
        wordPair={currentWord}
        inputText={inputText}
        onKeyDown={handleKeyDown}
        onInputChange={handleInputChange}
      />
    </div>
  );
}

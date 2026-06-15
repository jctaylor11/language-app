import React, { useState, useRef } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";

import type { WordPair, WordResults, VocabResults } from "../types";
import { fetchWords, getOrCreateSession, sendVocabResults } from "../api";
import { calcIncorrectInput } from "../utils";
import { DEV_USER_ID } from "../config";

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

  const keystrokes = useRef<string>("");
  const wordShownTime = useRef<number>(Date.now());

  const { data: session } = useQuery({
    queryKey: ["session"],
    queryFn: () => getOrCreateSession(DEV_USER_ID),
  });

  const { data: wordsData, fetchNextPage } = useInfiniteQuery({
    queryKey: ["words"],
    queryFn: () => fetchWords(DEV_USER_ID),
    initialPageParam: 0,
    getNextPageParam: (_, __, lastPageParam) => lastPageParam + 1,
    staleTime: Infinity, // Prevent background refetch mid-session (e.g window refocus)
  });

  const words = wordsData?.pages.flat() ?? [];

  const currentWord: WordPair | undefined = words[wordIndex];

  function getSessionPosition(): number {
    const stored = sessionStorage.getItem("sessionPosition");
    return stored ? Number(stored) : 1;
  }

  function advanceSessionPosition() {
    const newSessionPosition = getSessionPosition() + 1;
    sessionStorage.setItem("sessionPosition", String(newSessionPosition));
  }

  async function advanceWord() {
    setInputText("");
    keystrokes.current = "";
    advanceSessionPosition();

    // New time needed to calculate how long they took to answer
    wordShownTime.current = Date.now();

    // Advance the counter
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
    const session_position = getSessionPosition();

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
    if (!currentWord || !session) return; // Defensive

    setInputText(input);

    // Check whether input matches the answer
    if (input === currentWord.source) {
      const vocabResults = buildVocabResults(currentWord, session);
      await advanceWord(); // Timer is reset in advanceWord - therefore placed before sendVocabResults (so its not waiting) and after vocabResults is built (else time sent immediately after started)
      await sendVocabResults(DEV_USER_ID, vocabResults);
    }
  }

  async function handleKeyDown(e: React.KeyboardEvent) {
    if (!currentWord || !session) return;

    const key = e.key;
    if (key === "Escape" || key === "Tab") {
      e.preventDefault();

      // Build results before advancing to capture response time accurately since time updates on advanceWord
      const skipped = true;
      const vocabResults = buildVocabResults(currentWord, session, skipped);
      await advanceWord(); // advanceWord before network request to priorise UI speed
      await sendVocabResults(DEV_USER_ID, vocabResults);
    }

    // Filter out meaningless keys, replace Backspace with a clean and distinct symbol
    if (key.length !== 1 && key !== "Backspace") return;
    const recorded = key === "Backspace" ? "⌫" : key;

    // Update the ref
    keystrokes.current = keystrokes.current + recorded;
  }

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

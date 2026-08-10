import React, { useState, useRef, useEffect } from "react";
import {
  useQuery,
  useInfiniteQuery,
  useMutation,
  useIsMutating,
} from "@tanstack/react-query";

import type { WordPair, WordResults, VocabResults } from "../types";
import {
  fetchSession,
  fetchWords,
  sendVocabResults,
  getVocabSummary,
} from "../api";
import { calcIncorrectInput } from "../utils";

const SESSION_DURATION_S = 10;

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

function Timer({
  timerDurationS,
  sessionStartTime,
  onFinish,
}: {
  timerDurationS: number;
  sessionStartTime: number;
  onFinish: () => void;
}) {
  const [timeRemaining, setTimeRemaining] = useState(timerDurationS);

  useEffect(() => {
    const timerInterval = setInterval(() => {
      const currentTime = Date.now();
      const timeElapsedMs = currentTime - sessionStartTime;
      const secondsLeft = Math.ceil(timerDurationS - timeElapsedMs / 1000); // As a variable since the closed over state is the original timeRemaining, and remaining time is needed for <= 0 conditional
      setTimeRemaining(secondsLeft);

      if (secondsLeft <= 0) {
        clearInterval(timerInterval);
        onFinish(); // Updates state in parent component to render the summary component in place of everything currently being rendered for the session
      }
    }, 1000);

    return () => clearInterval(timerInterval); // Would be called on unmount, but also when the sessionStartTime changes (e.g. if the user restarts the session) - so the old interval is cleared and a new one is created with the new start time
  }, [sessionStartTime]);

  return <div>{timeRemaining}</div>;
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

function SessionSummary({
  handleNewSession,
  sessionId,
}: {
  handleNewSession: () => void;
  sessionId: number;
}) {
  const flushesInFlight = useIsMutating({ mutationKey: ["vocabResults"] });

  const sessionSummary = useQuery({
    queryKey: ["vocabSummary", sessionId],
    queryFn: () => getVocabSummary(sessionId),
    enabled: flushesInFlight === 0, // Otherwise last result may still be in flight which would undercount results
  });

  if (sessionSummary.isPending) {
    return <p>Loading...</p>;
  }

  if (sessionSummary.isError) {
    return <p>Error: {sessionSummary.error.message}</p>;
  }

  const newWords = sessionSummary.data.new_words;
  const totalReviewed = sessionSummary.data.total_reviewed;

  return (
    <div className="flex flex-col items-center gap-6 bg-[#dddddd] w-120 mx-auto px-10 py-5 m-20">
      <div id="summary-metrics" className="flex gap-16 mt-5">
        <div className="text-center">
          <div className="text-xs text-neutral-500 uppercase">New Words</div>
          <div className="text-xl text-gray-500 font-mono mt-2">{newWords}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-neutral-500 uppercase">
            Total Reviewed
          </div>
          <div className="text-xl text-gray-500 font-mono mt-2">
            {totalReviewed}
          </div>
        </div>
      </div>
      <button
        onClick={() => handleNewSession()}
        className="border px-6 py-1 mt-1 rounded cursor-pointer bg-gray-100 hover:bg-[#dddddd] active:bg-gray-200"
      >
        New Session
      </button>
    </div>
  );
}

export default function VocabSession() {
  const [inputText, setInputText] = useState<string>("");
  const [wordIndex, setWordIndex] = useState(0);
  const [sessionStartTime, setSessionStartTime] = useState(0);
  const [sessionFinished, setSessionFinished] = useState(false);

  const sessionPosition = useRef<number>(1);
  const keystrokes = useRef<string>("");
  const wordShownTime = useRef<number>(0);

  const {
    mutate: sessionMutate,
    data: sessionId,
    isPending: sessionPending,
  } = useMutation({
    mutationFn: () =>
      fetchSession({ bound_type: "time", bound_value: SESSION_DURATION_S }),
    onSuccess: () => {
      const sessionStart = Date.now();
      sessionPosition.current = 1;
      wordShownTime.current = sessionStart;
      setSessionStartTime(sessionStart);
      setInputText("");
      keystrokes.current = "";
      setSessionFinished(false);
    },
  });

  const { mutate: resultsMutate } = useMutation({
    mutationKey: ["vocabResults"],
    mutationFn: sendVocabResults,
  });

  const { data: wordsData, fetchNextPage } = useInfiniteQuery({
    queryKey: ["words"],
    queryFn: () => fetchWords(),
    initialPageParam: 0,
    getNextPageParam: (_, __, lastPageParam) => lastPageParam + 1,
    staleTime: Infinity, // Prevent background refetch mid-session (e.g window refocus)
  });

  const words = wordsData?.pages.flat() ?? [];

  // Append new batch if falls below threshold, checked every time words list or word index changes (after every commit)
  useEffect(() => {
    if (words.length - wordIndex <= 3) {
      fetchNextPage();
    }
  }, [words.length, wordIndex, fetchNextPage]);

  const currentWord: WordPair | undefined = words[wordIndex];

  function advanceWord() {
    setInputText("");
    keystrokes.current = "";
    sessionPosition.current++;

    // New time needed to calculate how long they took to answer
    wordShownTime.current = Date.now();

    // Increment the word index to advance the word
    const nextWordIndex = wordIndex + 1;
    setWordIndex(nextWordIndex);
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

  function handleInputChange(input: string) {
    if (!currentWord || !sessionId) return; // Defensive

    setInputText(input);

    // Check whether input matches the answer
    if (input === currentWord.source) {
      const vocabResults = buildVocabResults(currentWord, sessionId);
      advanceWord(); // wordShownTime is reset in advanceWord - therefore placed after building the results
      resultsMutate(vocabResults);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!currentWord || !sessionId) return;

    const key = e.key;
    if (key === "Escape" || key === "Tab") {
      e.preventDefault();

      // Build results before advancing to capture response time accurately since time updates on advanceWord
      const skipped = true;
      const vocabResults = buildVocabResults(currentWord, sessionId, skipped);
      advanceWord(); // wordShownTime is reset in advanceWord - therefore placed after building results
      resultsMutate(vocabResults);
    }

    // Filter out meaningless keys, replace Backspace with a clean and distinct symbol
    if (key.length !== 1 && key !== "Backspace") return;
    const recorded = key === "Backspace" ? "⌫" : key;

    // Update the ref
    keystrokes.current = keystrokes.current + recorded;
  }

  // Start button will flash without this, which if clicked would create an orphan session
  if (sessionPending) {
    return <div>Loading...</div>;
  }

  // There will only be a session ID after the user has clicked the start button. Having a separate state for the started would cause a race condition
  if (!sessionId) {
    return <VocabControl onStart={() => sessionMutate()} />;
  }

  if (sessionFinished) {
    return (
      <SessionSummary handleNewSession={sessionMutate} sessionId={sessionId} />
    );
  }

  if (!currentWord) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Timer
        timerDurationS={SESSION_DURATION_S}
        sessionStartTime={sessionStartTime}
        onFinish={() => {
          setSessionFinished(true);
          setWordIndex((index) => index + 1); // Skips the last (not done) word seen as the timer expired
        }}
      />
      <WordCard
        wordPair={currentWord}
        inputText={inputText}
        onKeyDown={handleKeyDown}
        onInputChange={handleInputChange}
      />
    </div>
  );
}

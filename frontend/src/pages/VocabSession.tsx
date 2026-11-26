import React, { useState, useRef, useEffect } from "react";
import { useOutletContext } from "react-router";
import {
  useQuery,
  useInfiniteQuery,
  useMutation,
  useIsMutating,
} from "@tanstack/react-query";

import type {
  RootLayoutContext,
  WordPair,
  WordResults,
  VocabResults,
  VocabResultStatus,
} from "../types";
import {
  fetchSession,
  completeSession,
  fetchWords,
  sendVocabResults,
  getVocabSummary,
} from "../api";
import {
  calcIncorrectInput,
  getAcceptedGlosses,
  isAcceptedAnswer,
} from "../utils";

const SESSION_DURATION_S = 120;

function formatTime(totalSeconds: number): string {
  const secondsLeft = Math.max(0, totalSeconds); // The timer can tick just past zero before the session finishes
  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function SessionHeader({ children }: { children: React.ReactNode }) {
  return (
    <header className="flex justify-end items-center gap-6 p-8 border-b-2 border-accent">
      {children}
    </header>
  );
}

function TimerDisplay({ seconds }: { seconds: number }) {
  return (
    <div
      role="timer"
      aria-label="Time remaining"
      className="font-mono text-timer tabular-nums text-ink"
    >
      {formatTime(seconds)}
    </div>
  );
}

function KeyHint() {
  return (
    <p className="flex gap-6 text-small text-ink-muted">
      <span>
        <span className="font-mono text-ink">Tab</span> to skip
      </span>
      <span>
        Hold <span className="font-mono text-ink">Esc</span> to reveal the
        answer
      </span>
    </p>
  );
}

function VocabStart({ onStart }: { onStart: () => void }) {
  const started = useRef(false);

  function startSession() {
    if (started.current) return; // A second key press before the session mutation is pending would create an orphan session
    started.current = true;
    onStart();
  }

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.repeat) return; // A held key would otherwise count as another press
      if (e.metaKey || e.ctrlKey || e.altKey || e.key === "Shift") return; // Shortcuts like Cmd+R shouldn't start a session
      startSession();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="h-full flex flex-col">
      <main className="flex-1 flex flex-col items-center justify-center px-8 pb-24">
        <div className="w-full max-w-session flex flex-col items-center gap-12">
          <div className="h-15 flex items-center justify-center">
            <p className="text-heading text-ink text-center">
              Type the English meaning of each Korean word.
            </p>
          </div>
          <button
            type="button"
            onClick={startSession}
            className="w-full h-16 px-4 rounded-lg border-2 border-accent bg-canvas text-answer text-ink-muted text-center cursor-pointer"
          >
            Press any key to start
          </button>
          <KeyHint />
        </div>
      </main>
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

  return <TimerDisplay seconds={timeRemaining} />;
}

function WordCard({
  wordPair,
  inputText,
  answerRevealed,
  inputElementRef,
  onKeyDown,
  onKeyUp,
  onBlur,
  onInputChange,
}: {
  wordPair: WordPair;
  inputText: string;
  answerRevealed: boolean;
  inputElementRef: React.RefObject<HTMLInputElement | null>;
  onKeyDown: (e: React.KeyboardEvent) => void;
  onKeyUp: (e: React.KeyboardEvent) => void;
  onBlur: () => void;
  onInputChange: (value: string) => void;
}) {
  const targetWord = wordPair.target;
  const sourceWord = wordPair.primary_glosses.join(" / ");
  const inputValue = answerRevealed ? sourceWord : inputText; // The answer replaces the typed text while Esc is held, which returns on release
  const inputFill = answerRevealed ? "bg-surface-muted" : "bg-canvas";

  return (
    <main className="flex-1 flex flex-col items-center justify-center px-8 pb-24">
      <div className="w-full max-w-session flex flex-col items-center gap-12">
        <h1 lang="ko" className="text-prompt-word font-ko text-ink text-center">
          {targetWord}
        </h1>
        {/* Full event object needed onKeyDown and onKeyUp to disable default Tab/Esc behaviour - e.g changing selection*/}
        <input
          type="text"
          ref={inputElementRef}
          autoFocus
          value={inputValue}
          readOnly={answerRevealed} // Otherwise typing while revealed would append to the displayed answer
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={onKeyDown} // For non-value keys (esc, tab) and keystroke history recording
          onKeyUp={onKeyUp}
          onBlur={onBlur}
          className={`w-full h-16 px-4 rounded-lg border-2 border-accent text-center text-answer text-ink outline-none ${inputFill}`}
        />
        <KeyHint />
      </div>
      <p className="absolute bottom-5 left-5 text-gray-500">{sourceWord}</p>
    </main>
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
  const [score, setScore] = useState(0);
  const [answerRevealed, setAnswerRevealed] = useState(false);

  const sessionPosition = useRef<number>(1);
  const keystrokes = useRef<string>("");
  const wordShownTime = useRef<number>(0);
  const peeked = useRef<boolean>(false);
  const inputElementRef = useRef<HTMLInputElement>(null);

  const {
    mutate: sessionMutate,
    data: sessionId,
    isPending: sessionPending,
  } = useMutation({
    mutationFn: () =>
      fetchSession({
        bound_type: "time",
        bound_value: SESSION_DURATION_S,
        session_type: "vocab",
      }),
    onSuccess: () => {
      const sessionStart = Date.now();
      sessionPosition.current = 1;
      wordShownTime.current = sessionStart;
      setSessionStartTime(sessionStart);
      setInputText("");
      setScore(0);
      keystrokes.current = "";
      setSessionFinished(false);
    },
  });

  // Sent as a mutation instead of an async function for pending state, which provides useIsMutating to check for in flight requests before showing summary
  const { mutate: resultsMutate } = useMutation({
    mutationKey: ["vocabResults"],
    mutationFn: sendVocabResults,
  });

  const { mutate: completeSessionMutate } = useMutation({
    mutationFn: completeSession,
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

  const { setFocusMode } = useOutletContext<RootLayoutContext>();
  const sessionRunning = sessionId !== undefined && !sessionFinished;

  useEffect(() => {
    setFocusMode(sessionRunning);
    return () => setFocusMode(false); // Otherwise navigating away mid-session would leave the nav hidden
  }, [sessionRunning, setFocusMode]);

  function advanceWord() {
    setInputText("");
    keystrokes.current = "";
    sessionPosition.current++;
    setAnswerRevealed(false);
    peeked.current = false;

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
    const acceptedGlosses = getAcceptedGlosses(currentWord);
    const raw_keystrokes = calcIncorrectInput(
      acceptedGlosses,
      keystrokes.current,
    );
    const session_position = sessionPosition.current;

    let status: VocabResultStatus;
    // Skipping takes priority over peeking, as it's a conscious decision they don't want to do that word
    if (skipped) {
      status = "skipped";
    } else if (peeked.current) {
      status = "peeked";
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
    if (isAcceptedAnswer(input, currentWord)) {
      if (!peeked.current) {
        // A correct input only counts if it wasn't peeked
        setScore((prev) => prev + 1);
      }

      const vocabResults = buildVocabResults(currentWord, sessionId);
      advanceWord(); // wordShownTime is reset in advanceWord - therefore placed after building the results
      resultsMutate(vocabResults);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!currentWord || !sessionId) return;

    const key = e.key;

    if (key === "Escape") {
      e.preventDefault();
      if (e.repeat) return; // Only the first press down is relevant

      setAnswerRevealed(true);
      peeked.current = true; // Only in keydown, not key up - otherwise holding the keydown while typing correct answer will result in a false positive on the next word
    }

    if (key === "Tab") {
      e.preventDefault();

      if (e.repeat) return; // Otherwise someone holding down the key will go through as pressing tab many times and burn through the queue

      // Build results before advancing to capture response time accurately since time updates on advanceWord
      const skipped = true;
      const vocabResults = buildVocabResults(currentWord, sessionId, skipped);
      advanceWord(); // wordShownTime is reset in advanceWord - therefore placed after building results
      resultsMutate(vocabResults);
    }

    // Filter out meaningless keys
    if (key.length !== 1 && key !== "Backspace") return;

    // Spaces at the beginning would be accidental space from end of last word, and double space would be accidental too
    if (key === " " && (inputText === "" || inputText.slice(-1) === " ")) {
      e.preventDefault();
      return;
    }

    const recorded = key === "Backspace" ? "⌫" : key; // A clean and distinct symbol for keystroke record to be analysed as an additional confidence signal in backend
    keystrokes.current = keystrokes.current + recorded;
  }

  function handleKeyUp(e: React.KeyboardEvent) {
    const key = e.key;

    if (key === "Escape") {
      setAnswerRevealed(false);
    }
  }

  function handleBlur() {
    setAnswerRevealed(false); // Otherwise answer stays revealed if focus is lost mid reveal
    inputElementRef.current?.focus(); // Refocuses on inputbox since typing shouldn't be lost mid-session
  }

  // Start button will flash without this, which if clicked would create an orphan session
  if (sessionPending) {
    return <div>Loading...</div>;
  }

  // There will only be a session ID after the user has clicked the start button. Having a separate state for the started would cause a race condition
  if (!sessionId) {
    return <VocabStart onStart={() => sessionMutate()} />;
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
    <div className="h-full flex flex-col">
      <SessionHeader>
        <Timer
          timerDurationS={SESSION_DURATION_S}
          sessionStartTime={sessionStartTime}
          onFinish={() => {
            completeSessionMutate(sessionId); // Only reached when the timer runs out, so a session left early stays uncompleted
            setSessionFinished(true);
            setWordIndex((index) => index + 1); // Skips the last (not done) word seen as the timer expired
          }}
        />
        <div className="font-mono text-timer tabular-nums text-ink-muted">
          {score}
        </div>
      </SessionHeader>
      <WordCard
        wordPair={currentWord}
        inputText={inputText}
        answerRevealed={answerRevealed}
        inputElementRef={inputElementRef}
        onKeyDown={handleKeyDown}
        onKeyUp={handleKeyUp}
        onBlur={handleBlur}
        onInputChange={handleInputChange}
      />
    </div>
  );
}

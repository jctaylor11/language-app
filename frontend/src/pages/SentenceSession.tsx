import { useRef, useState } from "react";
import {
  useQuery,
  useInfiniteQuery,
  useMutation,
  useIsMutating,
} from "@tanstack/react-query";

import {
  fetchSession,
  fetchSentencePairs,
  sendSentenceResult,
  getSentencesSummary,
  completeSession,
} from "../api";
import type { SentencePair, SentenceResults } from "../types";

const SENTENCES_PER_SESSION = 5;

function SentenceStart({ onStart }: { onStart: () => void }) {
  return (
    <div className="flex flex-col bg-[#dddddd] w-120 mx-auto px-15 py-5 text-[14px]">
      <h1 className="text-[28px] font-bold">Sentences</h1>
      <p className="mb-1">
        Sentences will be selected based on the words that you already know.
      </p>
      <p className="mb-2">
        Min 80% known words, prioritising those due for review
      </p>
      <p className="text-gray-500 pl-4">ESC to cheat</p>
      <p className="text-gray-500 pl-4">TAB to skip</p>

      {/* Intentionally leaving 'session' in to signal how the app functions in terms of session - this is the root of the data, the session log, etc */}
      <button
        onClick={() => onStart()}
        className="border px-6 py-1 mt-4 rounded cursor-pointer bg-gray-100 hover:bg-[#dddddd] active:bg-gray-200"
      >
        Start session
      </button>
    </div>
  );
}

function SentenceCard({
  sentencePair,
  inputText,
  answerRevealed,
  inputElementRef,
  onInputChange,
  onKeyDown,
  onKeyUp,
  onBlur,
}: {
  sentencePair: SentencePair;
  inputText: string;
  answerRevealed: boolean;
  inputElementRef: React.RefObject<HTMLInputElement | null>;
  onInputChange: (input: string) => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  onKeyUp: (e: React.KeyboardEvent) => void;
  onBlur: () => void;
}) {
  const targetSentence = sentencePair.target;
  const sourceSentence = sentencePair.source;

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-8 pb-48">
      <p
        className={`text-center text-xl font-medium tracking-wide text-gray-500 ${answerRevealed ? "" : "invisible"}`}
      >
        {sourceSentence}
      </p>
      <h1 className="text-center text-3xl font-medium tracking-wide">
        {targetSentence}
      </h1>
      {/* Full event object needed onKeyDown and onKeyUp to disable default Tab/Esc behaviour - e.g changing selection*/}
      <input
        type="text"
        ref={inputElementRef}
        autoFocus
        className="bg-transparent border-t border-b text-center border-gray-500 outline-none w-64 text-xl"
        value={inputText}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={onKeyDown}
        onKeyUp={onKeyUp}
        onBlur={onBlur}
      />
      <p className="absolute bottom-5 left-5 text-gray-500">{sourceSentence}</p>
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
  const flushesInFlight = useIsMutating({ mutationKey: ["sentenceResults"] });

  const sessionSummary = useQuery({
    queryKey: ["sentencesSummary", sessionId],
    queryFn: () => getSentencesSummary(sessionId),
    enabled: flushesInFlight === 0, // Ensure the final sentence has been inserted into the database before summary is fetched
  });

  if (sessionSummary.isPending) {
    return <p>Loading...</p>;
  }

  if (sessionSummary.isError) {
    return <p>Error: {sessionSummary.error.message}</p>;
  }

  const totalReviewed = sessionSummary.data.total_reviewed;

  return (
    <div className="flex flex-col items-center gap-6 bg-[#dddddd] w-120 mx-auto px-10 py-5 m-20">
      <div id="summary-metrics" className="flex gap-16 mt-5">
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

export default function SentenceSession() {
  const [inputText, setInputText] = useState("");
  const [sentencePairIndex, setSentencePairIndex] = useState(0);
  const [completedSentencesCount, setCompletedSentencesCount] = useState(0);
  const [answerRevealed, setAnswerRevealed] = useState(false);

  const cheated = useRef<boolean>(false);
  const inputElementRef = useRef<HTMLInputElement>(null);
  const queuedSentenceIdsRef = useRef<number[]>([]); // queryFn needs the latest sentencePairs, but referencing it directly creates a TS type cycle (its type depends on this hook's own return)

  const {
    mutate: sessionMutate,
    data: sessionId,
    isPending: sessionPending,
  } = useMutation({
    mutationFn: () =>
      fetchSession({
        bound_type: "count",
        bound_value: SENTENCES_PER_SESSION,
        session_type: "sentence",
      }),
    onSuccess: () => {
      setCompletedSentencesCount(0);
    },
  });

  const { mutate: resultsMutate } = useMutation({
    mutationKey: ["sentenceResults"],
    mutationFn: sendSentenceResult,
  });

  const { mutate: completeSessionMutate } = useMutation({
    mutationFn: completeSession,
  });

  const { data: sentencePairsData, fetchNextPage } = useInfiniteQuery({
    // useInfiniteQuery appends batches instead of replace on refetch
    queryKey: ["sentencePairs"],
    queryFn: () =>
      fetchSentencePairs(queuedSentenceIdsRef.current.slice(sentencePairIndex)),
    initialPageParam: 0,
    getNextPageParam: (_, __, lastPageParam) => lastPageParam + 1,
    staleTime: Infinity, // Prevent background refetching mid-session
  }); // Fetches on mount rather than waiting on the session, so the first batch is ready by the time the user starts

  const sentencePairs = sentencePairsData?.pages.flat() ?? []; // Pages only needed so refetch doesn't replace data
  queuedSentenceIdsRef.current = sentencePairs.map((pair) => pair.id);

  function buildSentenceResults(
    currentSentencePair: SentencePair,
    session: number,
    skipped: boolean = false,
  ): SentenceResults {
    const sentence_id = currentSentencePair.id;
    const session_id = session;

    let status: string;
    // Skipping takes priority over cheating, as it's a conscious decision they don't want to do that sentence
    if (skipped) {
      status = "skipped";
    } else if (cheated.current) {
      status = "cheated";
    } else {
      status = "correct";
    }

    const sentenceResults: SentenceResults = {
      sentence_id,
      session_id,
      status,
    };

    return sentenceResults;
  }

  function advanceSentencePair() {
    const nextIndex = sentencePairIndex + 1;

    setInputText("");
    setAnswerRevealed(false);
    cheated.current = false;
    setSentencePairIndex(nextIndex);

    if (sentencePairs.length - nextIndex <= 3) {
      fetchNextPage();
    }
  }

  function handleInputChange(input: string) {
    if (!sentencePairs[sentencePairIndex] || !sessionId) return; // Defensive

    setInputText(input);

    const cleanedSourceSentence = sentencePairs[sentencePairIndex].source
      .toLowerCase()
      .replace(/[^\w\s]/g, "");
    const cleanedInput = input.toLowerCase().replace(/[^\w\s]/g, "");

    if (cleanedInput === cleanedSourceSentence) {
      const sentenceResults = buildSentenceResults(
        sentencePairs[sentencePairIndex],
        sessionId,
      );
      const nextCompletedCount = completedSentencesCount + 1;

      if (nextCompletedCount >= SENTENCES_PER_SESSION) {
        completeSessionMutate(sessionId); // The count bound is the session's end, so a session left early stays uncompleted
      }

      setCompletedSentencesCount(nextCompletedCount);
      advanceSentencePair();
      resultsMutate(sentenceResults);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!sentencePairs[sentencePairIndex] || !sessionId) return; // Defensive

    const key = e.key;

    if (key === "Escape") {
      e.preventDefault();
      if (e.repeat) return; // Only the first press down is relevant

      setAnswerRevealed(true);
      cheated.current = true; // Only in keydown, not key up - otherwise holding the keydown while typing correct answer will result in a false positive on the next sentence
    }

    if (key === "Tab") {
      e.preventDefault();

      if (e.repeat) return; // Guards against someone holding down the skip key - burns through queue and costs on LLM tokens

      const sentenceResults = buildSentenceResults(
        sentencePairs[sentencePairIndex],
        sessionId,
        true,
      );
      advanceSentencePair();
      resultsMutate(sentenceResults);
    }
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

  // Intentionally above check for existence of sessionId, since session pending implies no session ID exists yet
  if (sessionPending) {
    return <div>Loading...</div>;
  }

  if (!sessionId) {
    return <SentenceStart onStart={() => sessionMutate()} />;
  }

  if (completedSentencesCount >= SENTENCES_PER_SESSION) {
    return (
      <SessionSummary handleNewSession={sessionMutate} sessionId={sessionId} />
    );
  }

  // Intentionally last guard since run before !sessionId would also show no sentence pairs
  if (!sentencePairs[sentencePairIndex]) {
    return <div>Loading...</div>;
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-end">{completedSentencesCount}</div>
      <SentenceCard
        sentencePair={sentencePairs[sentencePairIndex]}
        inputText={inputText}
        answerRevealed={answerRevealed}
        inputElementRef={inputElementRef}
        onInputChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onKeyUp={handleKeyUp}
        onBlur={handleBlur}
      />
    </div>
  );
}

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
} from "../api";
import type { SentencePair, SentenceResults } from "../types";

const SENTENCES_PER_SESSION = 5;

function SentenceStart({ onStart }: { onStart: () => void }) {
  return (
    <div className="flex justify-center bg-[#dddddd] w-120 mx-auto px-10 py-5">
      <div className="flex flex-col text-[14px] w-90">
        <h1 className="text-[28px] font-bold">Sentence Generation</h1>
        <p className="mb-4">Based on the words you know.</p>
        <button
          onClick={() => onStart()}
          className="border px-6 py-1 mt-4 rounded cursor-pointer bg-gray-100 hover:bg-[#dddddd] active:bg-gray-200"
        >
          Generate Sentences
        </button>
      </div>
    </div>
  );
}

function SentenceCard({
  sentencePair,
  inputText,
  onInputChange,
  onKeyDown,
}: {
  sentencePair: SentencePair;
  inputText: string;
  onInputChange: (input: string) => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
}) {
  const targetSentence = sentencePair.target;
  const sourceSentence = sentencePair.source;

  return (
    <div className="flex flex-col items-center justify-center pt-60">
      <h1 className="text-2xl font-medium tracking-wide">{targetSentence}</h1>
      <p>{sourceSentence}</p>
      <input
        type="text"
        className="bg-transparent border-t border-b text-center border-gray-500 outline-none w-64 text-xl"
        value={inputText}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={onKeyDown}
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
    if (skipped) {
      status = "skipped";
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
      setCompletedSentencesCount((prev) => prev + 1);
      advanceSentencePair();
      resultsMutate(sentenceResults);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!sentencePairs[sentencePairIndex] || !sessionId) return; // Defensive

    const key = e.key;
    if (key === "Escape" || key === "Tab") {
      e.preventDefault();

      const sentenceResults = buildSentenceResults(
        sentencePairs[sentencePairIndex],
        sessionId,
        true,
      );
      advanceSentencePair();
      resultsMutate(sentenceResults);
    }
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
    <>
      <div className="flex justify-end">{completedSentencesCount}</div>
      <SentenceCard
        sentencePair={sentencePairs[sentencePairIndex]}
        inputText={inputText}
        onInputChange={handleInputChange}
        onKeyDown={handleKeyDown}
      />
    </>
  );
}

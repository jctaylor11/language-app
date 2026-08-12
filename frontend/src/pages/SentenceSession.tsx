import { useRef, useState } from "react";
import { useInfiniteQuery, useMutation } from "@tanstack/react-query";

import { fetchSession, fetchSentencePairs, sendSentenceResult } from "../api";
import type { SentencePair, SentenceResults } from "../types";

const BAND_HALF_WIDTH_PERCENT = 10; // Mirrors PROPORTION_BAND_PERCENT in backend/routers/sentence.py
const SESSION_COUNT = 5;

function formatKnownBand(percentValue: number): string {
  const lowerPercent = percentValue - BAND_HALF_WIDTH_PERCENT;
  const upperPercent = percentValue + BAND_HALF_WIDTH_PERCENT;

  return `${lowerPercent}-${upperPercent}%`;
}

function SentenceControl({
  percentValue,
  onPercentChange,
  onStart,
}: {
  percentValue: number;
  onPercentChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onStart: () => void;
}) {
  return (
    <div className="flex justify-center bg-[#dddddd] w-120 mx-auto px-10 py-5">
      <div className="flex flex-col text-[14px] w-90">
        <h1 className="text-[28px] font-bold">Sentence Generation</h1>
        <p className="mb-4">Based on the words you know.</p>
        <div>
          <label className="block mb-2">
            Known words in each sentence: {formatKnownBand(percentValue)}
          </label>
          {/* Stops are band centres (10-90%) and the thumb matches the backend's applicable 20% range. Thumb is w-18, which is 20% of the w-90 track to match 20% band, so it stretches the width of the band instead of a single point */}
          <input
            className="w-full h-6 appearance-none rounded-sm bg-gray-400
              [&::-webkit-slider-thumb]:h-6 [&::-webkit-slider-thumb]:w-18 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:rounded-sm [&::-webkit-slider-thumb]:bg-gray-700
              [&::-moz-range-thumb]:h-6 [&::-moz-range-thumb]:w-18 [&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:rounded-sm [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:bg-gray-700"
            type="range"
            min="10"
            max="90"
            step="10"
            value={percentValue}
            onChange={(e) => onPercentChange(e)}
          />
        </div>
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

export default function SentenceSession() {
  const [knownPercent, setKnownPercent] = useState(90); // 80-100% band - the closest bucket to the ~80% comprehensible input target
  const [inputText, setInputText] = useState("");
  const [sentencePairIndex, setSentencePairIndex] = useState(0);

  const queuedSentenceIdsRef = useRef<number[]>([]); // queryFn needs the latest sentencePairs, but referencing it directly creates a TS type cycle (its type depends on this hook's own return)

  const {
    mutate: sessionMutate,
    data: sessionId,
    isPending: sessionPending,
  } = useMutation({
    mutationFn: () =>
      fetchSession({
        bound_type: "count",
        bound_value: SESSION_COUNT,
      }),
  });

  const { mutate: resultsMutate } = useMutation({
    mutationKey: ["sentenceResults"],
    mutationFn: sendSentenceResult,
  });

  const { data: sentencePairsData, fetchNextPage } = useInfiniteQuery({
    // useInfiniteQuery appends batches instead of replace on refetch
    queryKey: ["sentencePairs", knownPercent],
    queryFn: () =>
      fetchSentencePairs(
        knownPercent,
        queuedSentenceIdsRef.current.slice(sentencePairIndex),
      ),
    initialPageParam: 0,
    getNextPageParam: (_, __, lastPageParam) => lastPageParam + 1,
    staleTime: Infinity, // Prevent background refetching mid-session
    enabled: !!sessionId, // Since the user needs to submit preferences - Otherwise it will default to true on mount and fetch before user's preference. Double inversion resolves the 'false' being undefined
  });

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

  if (sessionPending) {
    return <div>Loading...</div>;
  }

  if (!sessionId) {
    return (
      <SentenceControl
        percentValue={knownPercent}
        onPercentChange={(e) => setKnownPercent(Number(e.target.value))}
        onStart={() => sessionMutate()}
      />
    );
  }

  // Intentionally last guard since run before !sessionId would also show no sentence pairs
  if (!sentencePairs[sentencePairIndex]) {
    return <div>Loading...</div>;
  }

  return (
    <SentenceCard
      sentencePair={sentencePairs[sentencePairIndex]}
      inputText={inputText}
      onInputChange={handleInputChange}
      onKeyDown={handleKeyDown}
    />
  );
}

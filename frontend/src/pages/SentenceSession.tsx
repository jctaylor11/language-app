import { useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";

import { fetchSentencePairs, sendSentenceResult } from "../api";
import type { SentencePair } from "../types";

function SentenceControl({
  proportionValue,
  onProportionChange,
  onStart,
}: {
  proportionValue: number;
  onProportionChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onStart: () => void;
}) {
  return (
    <div className="flex justify-center bg-[#dddddd] w-120 mx-auto px-10 py-5">
      <div className="flex flex-col text-[14px] w-90">
        <h1 className="text-[28px] font-bold">Sentence Generation</h1>
        <p className="mb-4">Based on the words you know.</p>
        <div>
          <label className="block mb-2">
            Select desired % of known words in the sentence:
          </label>
          <input
            className="w-full"
            type="range"
            min="0"
            max="100"
            step="20"
            value={proportionValue}
            onChange={(e) => onProportionChange(e)}
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
}: {
  sentencePair: SentencePair;
  inputText: string;
  onInputChange: (input: string) => void;
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
      />
    </div>
  );
}

export default function SentenceSession() {
  const [knownProportion, setKnownProportion] = useState(80);
  const [started, setStarted] = useState(false);
  const [inputText, setInputText] = useState("");
  const [sentencePairIndex, setSentencePairIndex] = useState(0);

  const {
    data: sentencePairsData,
    fetchNextPage,
    isLoading,
    isFetchingNextPage,
  } = useInfiniteQuery({
    // useInfiniteQuery appends batches instead of replace on refetch
    queryKey: ["sentencePairs", knownProportion],
    queryFn: () => fetchSentencePairs(knownProportion),
    initialPageParam: 0,
    getNextPageParam: (_, __, lastPageParam) => lastPageParam + 1,
    staleTime: Infinity, // Prevent background refetching mid-session
    enabled: started, // Otherwise it will defalt to true on mount, which will cause it to fetch sentences before the user has submitted preferences (e.g knownProportion)
  });

  const sentencePairs = sentencePairsData?.pages.flat() ?? []; // Pages only needed so refetch doesn't replace data

  function advanceSentencePair() {
    const nextIndex = sentencePairIndex + 1;

    setInputText("");
    setSentencePairIndex(nextIndex);

    if (sentencePairs.length - nextIndex <= 3) {
      fetchNextPage();
    }
  }

  function handleInputChange(input: string) {
    setInputText(input);

    const cleanedSourceSentence = sentencePairs[sentencePairIndex].source
      .toLowerCase()
      .replace(/[^\w\s]/g, "");
    const cleanedInput = input.toLowerCase().replace(/[^\w\s]/g, "");

    if (cleanedInput === cleanedSourceSentence) {
      const completedSentenceId = sentencePairs[sentencePairIndex].id; // Need to save the value before its incremented in advanceSentencePair
      advanceSentencePair(); // Placed before addUserSentence to prioritise what the user sees

      sendSentenceResult(completedSentenceId, "correct"); // Consider awaiting (investigate any race condition)
    }
  }

  if (started) {
    if (
      isLoading ||
      (isFetchingNextPage && !sentencePairs[sentencePairIndex])
    ) {
      // && required else it will show 'loading' whenever refetch is happening in background
      return <div>Loading...</div>;
    }
    return (
      <SentenceCard
        sentencePair={sentencePairs[sentencePairIndex]}
        inputText={inputText}
        onInputChange={handleInputChange}
      />
    );
  }

  return (
    <SentenceControl
      proportionValue={knownProportion}
      onProportionChange={(e) => setKnownProportion(Number(e.target.value))}
      onStart={() => setStarted(true)}
    />
  );
}

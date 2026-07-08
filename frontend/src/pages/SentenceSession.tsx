import { useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";

import { generateSentences, sendSentenceResult } from "../api";
import type { SentencePair } from "../types";

const NUM_WORDS = 5;

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
    queryKey: ["sentencePairs"],
    queryFn: () => generateSentences(NUM_WORDS),
    initialPageParam: 0,
    getNextPageParam: (_, __, lastPageParam) => lastPageParam + 1,
    staleTime: Infinity, // Prevent background refetching mid-session
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
      // Consider awaiting (investigate any race condition)
      sendSentenceResult(completedSentenceId, "correct");
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
    <div className="flex items-center justify-center pt-60">
      <button
        onClick={() => setStarted(true)}
        className="border px-6 py-1 rounded cursor-pointer hover:bg-gray-100 active:bg-gray-200"
      >
        Generate Sentences
      </button>
    </div>
  );
}

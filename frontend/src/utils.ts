import type { WordPair } from "./types";

export function normaliseAnswer(answer: string): string {
  const lowerCased = answer.toLowerCase().trim();
  const singleSpaced = lowerCased.replace(/\s+/g, " ");
  const withoutInfinitive = singleSpaced.replace(/^to /, ""); // "to eat" and "eat" are the same answer
  return withoutInfinitive;
}

export function getAcceptedGlosses(word: WordPair): string[] {
  return [...word.primary_glosses, ...word.tolerated_glosses];
}

export function isAcceptedAnswer(input: string, word: WordPair): boolean {
  const normalisedInput = normaliseAnswer(input);
  const acceptedGlosses = getAcceptedGlosses(word);

  for (const gloss of acceptedGlosses) {
    if (normaliseAnswer(gloss) === normalisedInput) {
      return true;
    }
  }
  return false;
}

export function calcIncorrectInput(
  acceptedAnswers: string[],
  allKeystrokes: string,
): string | null {
  const normalisedKeystrokes = normaliseAnswer(allKeystrokes);

  // Clean only if the keystrokes are exactly an accepted answer - any correction is recorded as ⌫, so it can't match
  for (const answer of acceptedAnswers) {
    if (normaliseAnswer(answer) === normalisedKeystrokes) {
      return null;
    }
  }
  return allKeystrokes;
}

export function formatSessionDate(isoTimestamp: string): string {
  const sessionDate = new Date(isoTimestamp);
  return sessionDate.toLocaleDateString("en-GB", {
    month: "short",
    day: "numeric",
  });
}

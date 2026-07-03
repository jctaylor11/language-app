import type { CredentialResponse } from "@react-oauth/google";

import type {
  WordPair,
  WordsResponse,
  SessionResponse,
  VocabResults,
  SentencePair,
  WordEntry,
  DashboardHeroMetrics,
  WordChartDataPoint,
} from "./types";

const BASE_URL = "http://127.0.0.1:8000";

export async function fetchWords(userId: number): Promise<WordPair[]> {
  const wordsUrl = `${BASE_URL}/words?user_id=${userId}`;
  const response = await fetch(wordsUrl, { method: "GET" });
  const wordsData: WordsResponse = await response.json();
  return wordsData.word_batch;
}

export async function fetchSession(userId: number): Promise<number> {
  const sessionUrl = `${BASE_URL}/sessions?user_id=${userId}`;
  const response = await fetch(sessionUrl, { method: "POST" });
  const sessionData: SessionResponse = await response.json();
  console.log("Session", sessionData);
  return sessionData.session_id;
}

export async function getOrCreateSession(userId: number): Promise<number> {
  const storedSession = sessionStorage.getItem("sessionId"); // So sessionId persists across refresh - session defined as tab session currently
  if (!storedSession) {
    const fetchedSession = await fetchSession(userId);
    sessionStorage.setItem("sessionId", String(fetchedSession));
    return fetchedSession;
  } else {
    return Number(storedSession);
  }
}

export async function sendVocabResults(
  userId: number,
  vocabResults: VocabResults,
): Promise<void> {
  try {
    const vocabResultsUrl = `${BASE_URL}/vocab-results?user_id=${userId}`;
    const response = await fetch(vocabResultsUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(vocabResults),
    });
    const vocabResultsData = await response.json();
    console.log("POST response: ", response.status, vocabResultsData);
  } catch (error) {
    console.error("Failed to send results:", error);
  }
}

export async function generateSentences(
  userId: number,
  numWords: number,
): Promise<SentencePair[]> {
  try {
    const sentencesUrl = `${BASE_URL}/sentences?user_id=${userId}`;
    const response = await fetch(sentencesUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        num_words: numWords,
      }),
    });
    const sentencesData = await response.json();
    return sentencesData.sentences;
  } catch (error) {
    console.error("Failed to get sentences:", error);
    return [];
  }
}

export async function sendSentenceResult(
  userId: number,
  sentenceId: number,
  status: string,
): Promise<void> {
  try {
    const userSentencesUrl = `${BASE_URL}/sentence-results?user_id=${userId}`;
    const response = await fetch(userSentencesUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sentence_id: sentenceId,
        status: status,
      }),
    });
    const addUserSentenceConfirmation = await response.json();
    console.log(addUserSentenceConfirmation);
  } catch (error) {
    console.error("Failed to add to user_sentence:", error);
  }
}

export async function getWordEntries(userId: number): Promise<WordEntry[]> {
  try {
    const wordEntriesUrl = `${BASE_URL}/dashboard/words?user_id=${userId}`;
    const response = await fetch(wordEntriesUrl, { method: "GET" });
    const wordEntries = await response.json();
    return wordEntries.words;
  } catch (error) {
    console.log("Failed to get word entries:", error);
    return [];
  }
}

export async function getHeroMetrics(
  userId: number,
): Promise<DashboardHeroMetrics> {
  const heroMetricsUrl = `${BASE_URL}/dashboard/hero-metrics?user_id=${userId}`;
  const response = await fetch(heroMetricsUrl, { method: "GET" });

  if (!response.ok) {
    throw new Error(`Failed to get hero metrics: ${response.status}`);
  }

  const heroMetrics = await response.json();

  return heroMetrics.metrics;
}

export async function getWordChartData(
  userId: number,
): Promise<WordChartDataPoint[]> {
  const wordChartDataUrl = `${BASE_URL}/dashboard/word-chart-data?user_id=${userId}`;
  const response = await fetch(wordChartDataUrl, { method: "GET" });

  if (!response.ok) {
    throw new Error(`Failed to get word chart data: ${response.status}`);
  }

  const wordChartData = await response.json();

  return wordChartData.cumulative_words;
}

export async function getJWTFromGoogleToken(credential: string) {
  const authGoogleUrl = `${BASE_URL}/auth-google`;
  const response = await fetch(authGoogleUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ credential }),
  });
  const userData = await response.json();

  return userData.token;
}

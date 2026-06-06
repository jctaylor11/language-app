import type {
  WordPair,
  WordsResponse,
  SessionResponse,
  SessionResults,
  SentencePair,
} from "./types";

const BASE_URL = "http://127.0.0.1:8000";

export async function fetchWords(): Promise<WordPair[]> {
  const wordsUrl = `${BASE_URL}/words`;
  const response = await fetch(wordsUrl, { method: "GET" });
  const wordsData: WordsResponse = await response.json();
  return wordsData.word_batch;
}

export async function fetchSession(): Promise<number> {
  const sessionUrl = `${BASE_URL}/sessions`;
  const response = await fetch(sessionUrl, { method: "POST" });
  const sessionData: SessionResponse = await response.json();
  console.log("Session", sessionData);
  return sessionData.session_id;
}

export async function getOrCreateSession(): Promise<number> {
  const storedSession = sessionStorage.getItem("sessionId"); // So sessionId persists across refresh - session defined as tab session currently
  if (!storedSession) {
    const fetchedSession = await fetchSession();
    sessionStorage.setItem("sessionId", String(fetchedSession));
    return fetchedSession;
  } else {
    return Number(storedSession);
  }
}

export async function sendResults(
  sessionResults: SessionResults,
): Promise<void> {
  try {
    const sessionResultsUrl = `${BASE_URL}/session-results`;
    const response = await fetch(sessionResultsUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sessionResults),
    });
    const sessionResultsData = await response.json();
    console.log("POST response: ", response.status, sessionResultsData);
  } catch (error) {
    console.error("Failed to send results:", error);
  }
}

export async function generateSentences(
  numWords: number,
): Promise<SentencePair[]> {
  try {
    const sentencesUrl = `${BASE_URL}/sentences?num_words=${numWords}`;
    const response = await fetch(sentencesUrl, { method: "GET" });
    const sentencesData = await response.json();
    return sentencesData.sentences;
  } catch (error) {
    console.error("Failed to get sentences:", error);
    return [];
  }
}

export async function addUserSentence(
  userId: number,
  sentenceId: number,
): Promise<void> {
  try {
    const userSentencesUrl = `${BASE_URL}/user_sentences`;
    const response = await fetch(userSentencesUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, sentence_id: sentenceId }),
    });
    const addUserSentenceConfirmation = await response.json();
    console.log(addUserSentenceConfirmation);
  } catch (error) {
    console.error("Failed to add to user_sentence:", error);
  }
}

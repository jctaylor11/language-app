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

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("jwt");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchWords(): Promise<WordPair[]> {
  const wordsUrl = `${BASE_URL}/words`;
  const response = await fetch(wordsUrl, {
    method: "GET",
    headers: authHeaders(),
  });
  const wordsData: WordsResponse = await response.json();
  return wordsData.word_batch;
}

export async function fetchSession(): Promise<number> {
  const sessionUrl = `${BASE_URL}/sessions`;
  const response = await fetch(sessionUrl, {
    method: "POST",
    headers: authHeaders(),
  });
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

export async function sendVocabResults(
  vocabResults: VocabResults,
): Promise<void> {
  try {
    const vocabResultsUrl = `${BASE_URL}/vocab-results`;
    const response = await fetch(vocabResultsUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(vocabResults),
    });
    const vocabResultsData = await response.json();
    console.log("POST response: ", response.status, vocabResultsData);
  } catch (error) {
    console.error("Failed to send results:", error);
  }
}

export async function generateSentences(
  numWords: number,
): Promise<SentencePair[]> {
  try {
    const sentencesUrl = `${BASE_URL}/sentences`;
    const response = await fetch(sentencesUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
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
  sentenceId: number,
  status: string,
): Promise<void> {
  try {
    const userSentencesUrl = `${BASE_URL}/sentence-results`;
    const response = await fetch(userSentencesUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
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

export async function getWordEntries(): Promise<WordEntry[]> {
  try {
    const wordEntriesUrl = `${BASE_URL}/dashboard/words`;
    const response = await fetch(wordEntriesUrl, {
      method: "GET",
      headers: authHeaders(),
    });
    const wordEntries = await response.json();
    return wordEntries.words;
  } catch (error) {
    console.log("Failed to get word entries:", error);
    return [];
  }
}

export async function getHeroMetrics(): Promise<DashboardHeroMetrics> {
  const heroMetricsUrl = `${BASE_URL}/dashboard/hero-metrics`;
  const response = await fetch(heroMetricsUrl, {
    method: "GET",
    headers: authHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to get hero metrics: ${response.status}`);
  }

  const heroMetrics = await response.json();

  return heroMetrics.metrics;
}

export async function getWordChartData(): Promise<WordChartDataPoint[]> {
  const wordChartDataUrl = `${BASE_URL}/dashboard/word-chart-data`;
  const response = await fetch(wordChartDataUrl, {
    method: "GET",
    headers: authHeaders(),
  });

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

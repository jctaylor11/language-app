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

const BASE_URL = "http://localhost:8000";

// Wrapper API to call endpoints with auth and retry with refresh token if 401 response
export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  let response = await fetch(url, { ...options, credentials: "include" });

  // Only intended to catch instance where the access token has expires and the refresh token is still active - hence refresh and retry
  if (response.status != 401) {
    return response;
  } else {
    const refreshAuthUrl = `${BASE_URL}/auth/refresh`;
    const refreshResponse = await fetch(refreshAuthUrl, {
      method: "POST",
      credentials: "include",
    });

    // Refresh token is invalid
    if (refreshResponse.status != 200) {
      throw new Error(
        "Refresh token is invalid or expired. Please log in again.",
      );
    }

    response = await fetch(url, { ...options, credentials: "include" });

    return response;
  }
}

export async function fetchWords(): Promise<WordPair[]> {
  const wordsUrl = `${BASE_URL}/words`;
  const response = await fetchWithAuth(wordsUrl, {
    method: "GET",
  });
  const wordsData: WordsResponse = await response.json();
  return wordsData.word_batch;
}

export async function fetchSession(): Promise<number> {
  const sessionUrl = `${BASE_URL}/sessions`;
  const response = await fetchWithAuth(sessionUrl, {
    method: "POST",
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
    const response = await fetchWithAuth(vocabResultsUrl, {
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
  numWords: number,
): Promise<SentencePair[]> {
  try {
    const sentencesUrl = `${BASE_URL}/sentences`;
    const response = await fetchWithAuth(sentencesUrl, {
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
  sentenceId: number,
  status: string,
): Promise<void> {
  try {
    const userSentencesUrl = `${BASE_URL}/sentence-results`;
    const response = await fetchWithAuth(userSentencesUrl, {
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

export async function getWordEntries(): Promise<WordEntry[]> {
  try {
    const wordEntriesUrl = `${BASE_URL}/dashboard/words`;
    const response = await fetchWithAuth(wordEntriesUrl, {
      method: "GET",
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
  const response = await fetchWithAuth(heroMetricsUrl, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Failed to get hero metrics: ${response.status}`);
  }

  const heroMetrics = await response.json();

  return heroMetrics.metrics;
}

export async function getWordChartData(): Promise<WordChartDataPoint[]> {
  const wordChartDataUrl = `${BASE_URL}/dashboard/word-chart-data`;
  const response = await fetchWithAuth(wordChartDataUrl, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Failed to get word chart data: ${response.status}`);
  }

  const wordChartData = await response.json();

  return wordChartData.cumulative_words;
}

export async function authenticateWithGoogleToken(
  credential: string,
): Promise<void> {
  const authGoogleUrl = `${BASE_URL}/auth-google`;
  const response = await fetch(authGoogleUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ credential }),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to authenticate with Google token: ${response.status}`,
    );
  }
}

export async function checkAuth(): Promise<boolean> {
  const response = await fetchWithAuth(`${BASE_URL}/auth/me`, {
    method: "GET",
  });
  return response.ok;
}

export async function logoutUser(): Promise<void> {
  const response = await fetch(`${BASE_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Failed to logout: ${response.status}`);
  }
}

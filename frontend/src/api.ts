import type {
  WordPair,
  WordsResponse,
  SessionResponse,
  VocabResults,
  SentencePair,
  WordEntry,
  DashboardHeroMetrics,
  WordChartDataPoint,
  ReviewChartDataPoint,
  SentenceEntry,
  SessionRequest,
  VocabSessionSummary,
  SentenceResults,
  SentenceSessionSummary,
  SessionLogEntry,
  AuthStatus,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL;

let refreshInFlight: Promise<boolean> | null = null; // Shared so concurrent 401s wait on one refresh, since the refresh token is single-use

async function requestTokenRefresh(): Promise<boolean> {
  const refreshAuthUrl = `${BASE_URL}/auth/refresh`;
  const refreshResponse = await fetch(refreshAuthUrl, {
    method: "POST",
    credentials: "include",
  });

  return refreshResponse.status === 200;
}

function refreshAccessToken(): Promise<boolean> {
  // If there is already a request in flight, the current promise will be returned - hence concurrent requests share the same request
  if (refreshInFlight === null) {
    refreshInFlight = requestTokenRefresh().finally(() => {
      refreshInFlight = null; // Cleared once settled so the next expiry triggers a fresh refresh
    });
  }

  return refreshInFlight;
}

// Wrapper API to call endpoints with auth and retry with refresh token if 401 response
export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  let response = await fetch(url, { ...options, credentials: "include" });

  // Only intended to catch instance where the access token has expired and the refresh token is still active - hence refresh and retry
  if (response.status != 401) {
    return response;
  } else {
    const refreshSucceeded = await refreshAccessToken();

    // Refresh token is invalid
    if (refreshSucceeded === false) {
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

export async function fetchSession(
  sessionRequest: SessionRequest,
): Promise<number> {
  const sessionUrl = `${BASE_URL}/sessions`;
  const response = await fetchWithAuth(sessionUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sessionRequest),
  });
  const sessionData: SessionResponse = await response.json();
  console.log("Session", sessionData);
  return sessionData.session_id;
}

export async function completeSession(sessionId: number): Promise<void> {
  const completeSessionUrl = `${BASE_URL}/sessions/${sessionId}/complete`;
  const response = await fetchWithAuth(completeSessionUrl, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Failed to complete session: ${response.status}`);
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

export class NotEnoughIntroducedWordsError extends Error {} // Its own type so the page can tell this 409 apart from other failures

export async function fetchSentencePairs(
  sentencesAlreadyQueued: number[] = [],
): Promise<SentencePair[]> {
  const sentencesUrl = `${BASE_URL}/sentences`;
  const response = await fetchWithAuth(sentencesUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sentences_already_queued: sentencesAlreadyQueued,
    }),
  });

  if (response.status === 409) {
    throw new NotEnoughIntroducedWordsError(
      "Not enough introduced words to build sentences",
    );
  }

  if (!response.ok) {
    throw new Error(`Failed to get sentences: ${response.status}`);
  }

  const sentencesData = await response.json();
  console.log("Fetched sentences:", sentencesData);
  return sentencesData.sentences;
}

export async function sendSentenceResult(
  sentenceResults: SentenceResults,
): Promise<void> {
  try {
    const userSentencesUrl = `${BASE_URL}/sentence-results`;
    const response = await fetchWithAuth(userSentencesUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sentenceResults),
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

export async function getReviewChartData(): Promise<ReviewChartDataPoint[]> {
  const reviewChartDataUrl = `${BASE_URL}/dashboard/review-chart-data`;
  const response = await fetchWithAuth(reviewChartDataUrl, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Failed to get review chart data: ${response.status}`);
  }

  const reviewChartData = await response.json();

  return reviewChartData.daily_reviews;
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

  if (!response.ok) {
    return false;
  }

  // Body checked rather than status alone, since a misrouted request (e.g a rewrite serving index.html) also returns 200
  const authStatus: AuthStatus = await response.json();
  return authStatus.authenticated === true;
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

export async function getSentenceEntries(): Promise<SentenceEntry[]> {
  const sentenceEntriesUrl = `${BASE_URL}/dashboard/sentences`;
  const response = await fetchWithAuth(sentenceEntriesUrl, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Failed to get sentence entries: ${response.status}`);
  }

  const sentenceEntries = await response.json();

  return sentenceEntries.sentences;
}

export async function getVocabSummary(
  sessionId: number,
): Promise<VocabSessionSummary> {
  const vocabSessionSummaryUrl = `${BASE_URL}/vocab-sessions/${sessionId}/summary`;
  const response = await fetchWithAuth(vocabSessionSummaryUrl, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Failed to get vocab session summary: ${response.status}`);
  }

  const vocabSummary = await response.json();

  return vocabSummary.summary;
}

export async function getSentencesSummary(
  sessionId: number,
): Promise<SentenceSessionSummary> {
  const sentenceSessionSummaryUrl = `${BASE_URL}/sentence-sessions/${sessionId}/summary`;
  const response = await fetchWithAuth(sentenceSessionSummaryUrl, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(
      `Failed to get sentence session summary: ${response.status}`,
    );
  }

  const sentenceSummary = await response.json();

  return sentenceSummary.summary;
}

export async function getSessionLog(): Promise<SessionLogEntry[]> {
  const sessionLogUrl = `${BASE_URL}/sessions/log`;
  const response = await fetchWithAuth(sessionLogUrl, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Failed to get session log: ${response.status}`);
  }

  const sessionLog = await response.json();

  return sessionLog.session_log;
}

export async function getSessionOverview(sessionId: number): Promise<string[]> {
  const sessionOverviewUrl = `${BASE_URL}/sessions/overview/${sessionId}`;
  const response = await fetchWithAuth(sessionOverviewUrl, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Failed to get session overview: ${response.status}`);
  }

  const sessionOverview = await response.json();

  return sessionOverview.session_overview;
}

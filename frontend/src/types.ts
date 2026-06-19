export type WordPair = {
  id: number;
  target: string;
  source: string;
};

export type WordsResponse = {
  word_batch: WordPair[];
};

export type SessionResponse = {
  session_id: number;
};

export type WordResults = {
  word_id: number;
  response_time_ms: number | null;
  answered_at: string | null;
  raw_keystrokes: string | null;
  status: string;
  session_position: number;
};

export type VocabResults = {
  session_id: number;
  word_results: WordResults[];
};

export type SentencePair = {
  id: number;
  target: string;
  source: string;
};

export type WordEntry = {
  id: number;
  target: string;
  source: string;
  times_reviewed: number;
  av_s_per_syllable: number;
  accuracy: number;
};

export type DashboardHeroMetrics = {
  total_words: number;
  words_reviewed: number;
  accuracy: number;
};

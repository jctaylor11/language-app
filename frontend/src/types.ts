export type Word = {
  id: number,
  target: string,
  source: string
}

export type WordsResponse = {
  word_batch: Word[]
}

export type SessionResponse = {
  session_id: number
}

export type WordResults = {
  word_id: number,
  response_time_ms: number | null,
  answered_at: string | null,
  pre_correction_input: string | null,
  status: string,
  session_position: number
}

export type SessionResults = {
  session_id: number,
  word_results: WordResults[]
}

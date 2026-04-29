import type { Word, WordsResponse, SessionResponse, SessionResults } from './types'

const BASE_URL = "http://127.0.0.1:8000"

  export async function fetchWords(): Promise<Word[]> {
    const wordsUrl = `${BASE_URL}/words`
    const response = await fetch(wordsUrl, {method: "GET"})
    const wordsData: WordsResponse = await response.json()
    return wordsData.word_batch
  }

  
export async function fetchSession() {
    const sessionUrl = `${BASE_URL}/sessions`
    const response = await fetch(sessionUrl, {method: "POST"})
    const sessionData: SessionResponse = await response.json()
    console.log("Session", sessionData)
    return sessionData.session_id
}

export async function sendResults(sessionResults: SessionResults) {
    try {
        const sessionResultsUrl = `${BASE_URL}/session-results`
        const response = await fetch(sessionResultsUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sessionResults)
        })
        const responseBody = await response.json()
        console.log("POST response: ", response.status, responseBody)
    } catch (error) {
        console.error("Failed to send results:", error)
    }
  }
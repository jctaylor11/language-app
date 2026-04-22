import { useEffect } from "react"
import { useState } from "react"

type Word = {
  word_id: string,
  target: string,
  source: string
}

type WordResults = {
  word_id: number,
  response_time_ms: number | null,
  answered_at: string | null,
  pre_correction_input: string | null,
  status: string,
  session_position: number
}

type SessionResults = {
  session_id: number,
  word_results: WordResults[]
}


export default function App() {
  const [session, setSession] = useState<number | null>(null)
  const [words, setWords] = useState<Word[]>([])
  const [inputText, setInputText] = useState<string>('')

  async function fetchWords(): Promise<Word[]> {
    const wordsUrl = "http://127.0.0.1:8000/words"
    const response = await fetch(wordsUrl, {method: "GET"})
    const wordsData = await response.json()
    return wordsData.word_batch
  }

  useEffect(() => {
    const sessionUrl = "http://127.0.0.1:8000/sessions"
    async function fetchSession() {
      const response = await fetch(sessionUrl, {method: "POST"})
      const sessionData  = await response.json()
      console.log("Data", sessionData)
      setSession(sessionData.session_id)
    }

    async function init() {    // Init function used so that fetchWords can be awaited
      await fetchSession()
      const word_batch = await fetchWords()
      setWords(word_batch)
    }

    init()
  }, [])

  const targetWord = words[0]?.target
  const sourceWord = words[0]?.source


  async function handleInputChange(input: string) {

    async function sendResults() {

      // Packs the results for the word
      const wordResults: WordResults = {
        word_id: 1,
        response_time_ms: null,
        answered_at: null,
        pre_correction_input: null,
        status: "correct_first_try",
        session_position: 5
      }

      // Packs the result into to sessionResults type (only one item in list for now)
      const sessionResults: SessionResults = {
        session_id: 1,
        word_results: [wordResults]
      }

      // Sends the sessionResults via http POST
      const sessionResultsUrl = "http://127.0.0.1:8000/session-results"
      const response = await fetch(sessionResultsUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sessionResults)
      })
      const responseBody = response.json()
      console.log("POST response: ", response.status, responseBody)
    }

    setInputText(input)

    // Check whether input matches the answer
    if (input === sourceWord) {
      sendResults()
      setInputText('')
      
      // Remove item from array
      const newWords = words.slice(1)

      // Append a new batch to the end of the array if it falls below threshold
      if (newWords.length <= 3) {
        const newBatch = await fetchWords()
        setWords([...newWords, ...newBatch])
      } else {
        setWords(newWords)
      }
    }
  }

  return (
    <>
      <div>{targetWord}</div>
      <div>{sourceWord}</div>
      <form>
        <input 
          type='text' 
          value={inputText}
          onChange={(e) => handleInputChange(e.target.value)}/>
      </form>
    </>
  )
}

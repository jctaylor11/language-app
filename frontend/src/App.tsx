import React, { useEffect } from "react"
import { useState } from "react"
import { useRef } from "react"

type Word = {
  id: number,
  target: string,
  source: string
}

type WordsResponse = {
  word_batch: Word[]
}

type SessionResponse = {
  session_id: number
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
  const keystrokes = useRef<string>('')
  const wordShownTime = useRef<number>(Date.now())

  const storedPosition = sessionStorage.getItem('sessionPosition')
  const sessionPosition = useRef<number>(storedPosition ? Number(storedPosition) : 1)

  useEffect(() => {
    wordShownTime.current = Date.now()
  }, [words[0]?.id])

  async function fetchWords(): Promise<Word[]> {
    const wordsUrl = "http://127.0.0.1:8000/words"
    const response = await fetch(wordsUrl, {method: "GET"})
    const wordsData: WordsResponse = await response.json()
    return wordsData.word_batch
  }

  useEffect(() => {
    const sessionUrl = "http://127.0.0.1:8000/sessions"
    async function fetchSession() {
      const response = await fetch(sessionUrl, {method: "POST"})
      const sessionData: SessionResponse = await response.json()
      console.log("Session", sessionData)
      return sessionData.session_id
    }

    async function init() {    // Init function used so that fetchWords can be awaited
      const storedSessionId = sessionStorage.getItem('sessionId')
      let sessionId = storedSessionId ? Number(storedSessionId) : null

      if (!sessionId) {
        sessionId = await fetchSession()
        sessionStorage.setItem('sessionId', String(sessionId))
      }

      setSession(sessionId)

      const wordBatch = await fetchWords()
      setWords(wordBatch)
    }

    init()
  }, [])


  function calcIncorrectInput(correctWord: string, allKeystrokes: string): string | null {
    if (allKeystrokes === correctWord) {
      return null
    }
    return allKeystrokes
  }

  const currentWord: Word | undefined = words[0]
  const targetWord = currentWord?.target
  const sourceWord = currentWord?.source

  async function advanceWord() {
        // Reset the states for new word
      setInputText('')
      keystrokes.current = ''
      sessionPosition.current += 1
      sessionStorage.setItem('sessionPosition', String(sessionPosition.current))   // sessionStorage only initialised sessionPosition on increment

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


  function buildSessionResults(currentWord: Word, session: number, skipped: boolean = false): SessionResults {
    // Compute results
    const word_id = currentWord.id
    const response_time_ms = Date.now() - wordShownTime.current      
    const answered_at = new Date().toISOString()
    const pre_correction_input =  calcIncorrectInput(currentWord.source, keystrokes.current)

    let status: string
    if (skipped) {
      status = 'skipped'
    } else {
      status = pre_correction_input === null ? 'correct_first_try' : 'corrected'    
    }

    const session_position = sessionPosition.current         
    const session_id = session

    // Packs the results for the words
    const wordResults: WordResults = {
      word_id,
      response_time_ms,
      answered_at,
      pre_correction_input,
      status,
      session_position
    }

    // Packs the result into to sessionResults type (only one item in list for now)
    const sessionResults: SessionResults = {
      session_id,
      word_results: [wordResults]
    }

    return sessionResults
  }


  async function sendResults(sessionResults: SessionResults) {
    try {
      const sessionResultsUrl = "http://127.0.0.1:8000/session-results"
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


  async function handleInputChange(input: string) {
    // Defensively ensure values are valid
    if (!currentWord || session === null) return;

    setInputText(input)

    // Check whether input matches the answer
    if (input === sourceWord) {
      const sessionResults = buildSessionResults(currentWord, session)
      await sendResults(sessionResults)
      await advanceWord()

    }

  }

  async function handleKeyDown(e: React.KeyboardEvent) {
    if (!currentWord || session === null) return;

    const key = e.key
    if (key === 'Escape' || key === 'Tab') {
      e.preventDefault()

      // Skip word - Builds response before advanceWord for response time integrity considering useEffect dependency on words[0] 
      const skipped = true
      const sessionResults = buildSessionResults(currentWord, session, skipped)
      await advanceWord()    // advanceWord before network request to priorise UI speed
      await sendResults(sessionResults)
    }

    // Filter out meaningless keys, replace Backspace with a clean and distinct symbol
    if (key.length !== 1 && key !== 'Backspace') return
    const recorded = key === 'Backspace' ? '⌫' : key

    // Update the ref
    keystrokes.current = keystrokes.current + recorded
  }

  return (
    <>
      <div>{targetWord}</div>
      <div>{sourceWord}</div>
      <input 
        type='text' 
        value={inputText}
        onChange={(e) => handleInputChange(e.target.value)}
        onKeyDown={(e) => handleKeyDown(e)}/>  {/* Full event object needed to disable default Tab behaviour*/}
    </>
  )
}

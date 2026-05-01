import React, { useEffect, useState, useRef } from "react"

import type { Word, WordResults, SessionResults } from './types'
import { fetchWords, fetchSession, sendResults } from "./api"
import { calcIncorrectInput } from "./utils"

export default function App() {
  const [session, setSession] = useState<number | null>(null)
  const [words, setWords] = useState<Word[]>([])
  const [inputText, setInputText] = useState<string>('')

  const keystrokes = useRef<string>('')
  const wordShownTime = useRef<number>(Date.now())
  
  const currentWord: Word | undefined = words[0]
  const targetWord = currentWord?.target
  const sourceWord = currentWord?.source

  useEffect(() => {
    wordShownTime.current = Date.now()
  }, [words[0]?.id])

  useEffect(() => {
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

  function getSessionPosition(): number {
    const stored = sessionStorage.getItem('sessionPosition')
    return stored ? Number(stored) : 1
  }

  function advanceSessionPosition() {
    const newSessionPosition = getSessionPosition() + 1
    sessionStorage.setItem('sessionPosition', String(newSessionPosition))
  }

  async function advanceWord() {
    // Reset the states for new word
    setInputText('')
    keystrokes.current = ''
    advanceSessionPosition()

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
    const word_id = currentWord.id
    const response_time_ms = Date.now() - wordShownTime.current      
    const answered_at = new Date().toISOString()
    const pre_correction_input = calcIncorrectInput(currentWord.source, keystrokes.current)
    const session_position = getSessionPosition()

    let status: string
    if (skipped) {
      status = 'skipped'
    } else {
      status = pre_correction_input === null ? 'correct_first_try' : 'corrected'    
    }

    // Pack results for the words
    const wordResults: WordResults = {
      word_id,
      response_time_ms,
      answered_at,
      pre_correction_input,
      status,
      session_position
    }

    // Pack words into SessionResults (only one item in list for now)
    const sessionResults: SessionResults = {
      session_id: session,
      word_results: [wordResults]
    }

    return sessionResults
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
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-200 gap-8 pb-48">
      <div className="text-center">
        <h1 className="text-4xl font-medium tracking-wide">{targetWord}</h1>
        <p>{sourceWord}</p>
      </div>
      <input 
        type='text' 
        value={inputText}
        onChange={(e) => handleInputChange(e.target.value)}
        onKeyDown={(e) => handleKeyDown(e)}    /* Full event object needed to disable default Tab behaviour*/
        className="bg-transparent border-t border-b text-center border-gray-500 outline-none w-64 text-xl"
      />  
    </div>
  )
}



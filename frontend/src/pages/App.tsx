import React, { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router'

import type { Word, WordResults, SessionResults } from '../types'
import { fetchWords, getOrCreateSession, sendResults } from "../api"
import { calcIncorrectInput } from "../utils"

import { useQuery } from '@tanstack/react-query'

export default function App() {
  const [words, setWords] = useState<Word[]>([])
  const [inputText, setInputText] = useState<string>('')

  const keystrokes = useRef<string>('')
  const wordShownTime = useRef<number>(Date.now())
  
  const currentWord: Word | undefined = words[0]
  const targetWord = currentWord?.target
  const sourceWord = currentWord?.source

  const {data: session} = useQuery({
    queryKey: ['session'],
    queryFn: getOrCreateSession,
  })

  useEffect(() => {
    wordShownTime.current = Date.now()
  }, [words[0]?.id])

  useEffect(() => {
    async function init() {
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
    setWords(newWords)

    // Append a new batch to the end of the array if it falls below threshold
    if (newWords.length <= 3) {
      console.log("Fetching new batch of words")  // Debugging
      const newBatch = await fetchWords()
      setWords((remainingWords) => [...remainingWords, ...newBatch])
    }
  }

  function buildSessionResults(currentWord: Word, session: number, skipped: boolean = false): SessionResults {
    const word_id = currentWord.id
    const response_time_ms = Date.now() - wordShownTime.current      
    const answered_at = new Date().toISOString()
    const raw_keystrokes = calcIncorrectInput(currentWord.source, keystrokes.current)
    const session_position = getSessionPosition()

    let status: string
    if (skipped) {
      status = 'skipped'
    } else {
      status = raw_keystrokes === null ? 'correct_first_try' : 'corrected'    
    }

    // Pack results for the words
    const wordResults: WordResults = {
      word_id,
      response_time_ms,
      answered_at,
      raw_keystrokes,
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
    if (!currentWord || !session) return;

    setInputText(input)

    // Check whether input matches the answer
    if (input === sourceWord) {
      const sessionResults = buildSessionResults(currentWord, session)
      await sendResults(sessionResults)
      await advanceWord()
    }
  }

  async function handleKeyDown(e: React.KeyboardEvent) {
    if (!currentWord || !session) return;

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
    <div className="min-h-screen bg-slate-200 flex flex-col">
      <nav className='flex justify-end p-5 gap-4'>
        <Link to="/sentences">Sentences</Link>
        <Link to="/dashboard">Dashboard</Link>
      </nav>
      <div className="flex-1 flex flex-col items-center justify-center gap-8 pb-48">
        <div className="text-center">
          <h1 className="text-4xl font-medium tracking-wide">{targetWord}</h1>
          <p>{sourceWord}</p>
        </div>
        {/* Full event object needed onKeyDown to disable default Tab behaviour*/}
        <input 
          type='text' 
          value={inputText}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={(e) => handleKeyDown(e)}    
          className="bg-transparent border-t border-b text-center border-gray-500 outline-none w-64 text-xl"
        />  
      </div>
    </div>
  )
}



import { useEffect } from "react"
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
      setSession(sessionData.session_id)
    }

    async function init() {    // Init function used so that fetchWords can be awaited
      await fetchSession()
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


  async function handleInputChange(input: string) {
    // Defensively ensure values are valid
    if (!currentWord || session === null) return;
  
    function buildSessionResults(currentWord: Word, session: number): SessionResults {
      // Compute results
      const word_id = currentWord.id
      const response_time_ms = Date.now() - wordShownTime.current      
      const answered_at = new Date().toISOString()
      const pre_correction_input =  calcIncorrectInput(currentWord.source, keystrokes.current)
      const status = "correct_first_try"  // Hard-coded - This should be a utils function that makes inference based on pre_correction_input
      const session_position = 1          // Hard-coded - Counter for words done in session needs implemenation
      const session_id = session

      // Packs the results for the word
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
      // Sends the sessionResults via http POST
      const sessionResultsUrl = "http://127.0.0.1:8000/session-results"
      const response = await fetch(sessionResultsUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sessionResults)
      })
      const responseBody = await response.json()
      console.log("POST response: ", response.status, responseBody)
    }

    setInputText(input)

    // Check whether input matches the answer
    if (input === sourceWord) {
      const sessionResults = buildSessionResults(currentWord, session)
      await sendResults(sessionResults)

      // Reset the states for new word
      setInputText('')
      keystrokes.current = ''

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

  function handleKeyDown(key: string) {
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
      <form>
        <input 
          type='text' 
          value={inputText}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={(e) => handleKeyDown(e.key)}/>
      </form>
    </>
  )
}

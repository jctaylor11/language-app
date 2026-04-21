import { useEffect } from "react"
import { useState } from "react"

type Word = {
  word_id: string,
  target: string,
  source: string
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
      fetchSession()
      const word_batch = await fetchWords()
      setWords(word_batch)
    }

    init()
  }, [])

  const targetWord = words[0]?.target
  const sourceWord = words[0]?.source


  async function handleInputChange(input: string) {
    setInputText(input)

    // Check whether input matches the answer
    if (input === sourceWord) {
      setInputText('')
      
      // Remove item from array
      const newWords = words.slice(1)

      // Append a new batch to the end of the array if it falls below threshold
      if (newWords.length <= 3) {
        const newBatch = await fetchWords()
        setWords([...newWords, ...newBatch])
      } else {
        setWords(words.slice(1))
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

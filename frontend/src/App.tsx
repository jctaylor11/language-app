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

  async function fetchWords() {
    const wordsUrl = "http://127.0.0.1:8000/words"
    const response = await fetch(wordsUrl, {method: "GET"})
    const wordsData = await response.json()
    setWords(wordsData.word_batch)
  }

  useEffect(() => {
    const sessionUrl = "http://127.0.0.1:8000/sessions"
    async function fetchSession() {
      const response = await fetch(sessionUrl, {method: "POST"})
      const sessionData  = await response.json()
      console.log("Data", sessionData)
      setSession(sessionData.session_id)
    }

    console.log(session)

    fetchSession()
    fetchWords()
  }, [])

  const targetWord = words[0]?.target
  const sourceWord = words[0]?.source

  return (
    <>
      <div>
        {targetWord}
      </div>
      <div>
        {sourceWord}
      </div>
    </>
  )
}
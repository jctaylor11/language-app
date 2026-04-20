import { useEffect } from "react"

export default function App() {
  useEffect(() => {
    const sessionUrl = "http://127.0.0.1:8000/sessions"
    async function fetchSession() {
      const response = await fetch(sessionUrl, {method: "POST"})
      const session  = await response.json()
      console.log(session)
    }

    fetchSession()
    fetchWords()
  }, [])

  async function fetchWords() {
    const wordsUrl = "http://127.0.0.1:8000/words"
    const response = await fetch(wordsUrl, {method: "GET"})
    const words = await response.json()
    console.log(words)
  }

  return null
}
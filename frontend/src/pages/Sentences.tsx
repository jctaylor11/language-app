import { useState, useEffect } from 'react'

import { generateSentences } from '../api'
import type { SentencePair } from '../types'


function SentenceInput({ sentence, inputText, handleKeyDown }: { sentence: string, inputText: string, handleKeyDown: (input: string) => void}) {
    return (
        <div className='flex flex-col items-center justify-center pt-60 '>
            <h1>{sentence}</h1>
            <input
                type='text'
                className='bg-transparent border-t border-b text-center border-gray-500 outline-none w-64 text-xl'
                value={inputText}
                onChange={(e) => handleKeyDown(e.target.value)}
            />
        </div>
    )}

export default function Sentences() {
    const [started, setStarted] =  useState(false)
    const [inputText, setInputText] = useState('')

    const [sentencePairs, setSentencePairs] = useState<SentencePair[] | null>(() => {
        const storedSentencePairs = sessionStorage.getItem('sentencePairs')
        return storedSentencePairs ? JSON.parse(storedSentencePairs) : null
    })

    useEffect(() => {
        async function init() {
            if (!sentencePairs) {
                const generatedSentencePairs = await generateSentences(10)
                sessionStorage.setItem('sentencePairs', JSON.stringify(generatedSentencePairs))

                setSentencePairs(generatedSentencePairs)
            }
        }

        init()

    }, [])

    console.log(sentencePairs)  // Just for testing it's been wired through


    function handleKeyDown(input: string) {
        setInputText(input)
    }

    if (started) {
        return <SentenceInput sentence={sentence} inputText={inputText} handleKeyDown={handleKeyDown} />
    }

    return(
        <div className="flex items-center justify-center pt-60">
            <button onClick={() => setStarted(true)} className='border px-6 py-1 rounded cursor-pointer hover:bg-gray-100 active:bg-gray-200'>Generate Sentences</button>
        </div>
    )
}
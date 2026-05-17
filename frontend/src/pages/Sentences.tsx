import { useState, useEffect } from 'react'

import { generateSentences } from '../api'


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

    const sentence = "This is a placeholder for a Korean sentence"

    useEffect(() => {
        async function init() {

            if (!sessionStorage.getItem('sentences')) {
                const sentences = await generateSentences(10)
                sessionStorage.setItem('sentences', JSON.stringify(sentences))
            }

            // For testing
            const savedSentences = sessionStorage.getItem('sentences')
            console.log(JSON.parse(savedSentences!))
        }

        init()

    }, [])

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
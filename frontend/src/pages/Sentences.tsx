import { useState } from 'react'

import { generateSentences } from '../api'
import type { SentencePair } from '../types'
import { useQuery } from '@tanstack/react-query'

const NUM_WORDS = 5


function SentenceCard({ sentencePair, inputText, handleKeyDown }: {sentencePair: SentencePair, inputText: string, handleKeyDown: (input: string) => void}) {
    const targetSentence = sentencePair.target 
    const sourceSentence = sentencePair.source

    return (
        <div className='flex flex-col items-center justify-center pt-60 '>
            <h1 className='text-2xl font-medium tracking-wide'>{targetSentence}</h1>
            <p>{sourceSentence}</p>
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
    const [sentencePairsOffset, setSentencePairsOffset] = useState(0)

    const { data: sentencePairs} = useQuery({
        queryKey: ['sentencePairs'], 
        queryFn: () => generateSentences(NUM_WORDS)
    })


    function advanceSentencePair() {
        if (!sentencePairs) {
            console.error("sentencePairs list is empty")  // Defensive, this shouldn't happen
            return
        }

        setInputText('')
        setSentencePairsOffset(prev => prev + 1)

        // TODO: Add the fetch logic for a new batch whenever the number of items gets down to x
    }

    function handleKeyDown(input: string) {
        if (!sentencePairs) return  // Defensive
        
        setInputText(input)

        const cleanedSourceSentence = sentencePairs[sentencePairsOffset].source.toLowerCase().replace(/[^\w\s]/g,"")
        const cleanedInput = input.toLowerCase().replace(/[^\w\s]/g,"")

        if (cleanedInput === cleanedSourceSentence) {
            advanceSentencePair()
        }
    }

    if (started) {
        if (!sentencePairs) {
            return <div>Loading...</div>
        }
        return <SentenceCard sentencePair={sentencePairs[sentencePairsOffset]} inputText={inputText} handleKeyDown={handleKeyDown} />
    }

    return(
        <div className="flex items-center justify-center pt-60">
            <button onClick={() => setStarted(true)} className='border px-6 py-1 rounded cursor-pointer hover:bg-gray-100 active:bg-gray-200'>Generate Sentences</button>
        </div>
    )
}
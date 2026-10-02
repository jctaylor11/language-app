# Sentences feature reference (current state)

## Frontend

- SentenceSession uses useInfiniteQuery hook to fetch sentences: pages append and not replaced
- staleTime: Infinity means no automatic refetch. After the initial render, the next page is only explicitly fetched with fetchNextPage
- fetchNextPage is only fired when the (total - current index) <= 3
- fetchNextPage hits fetchSentencePairs, which hits POST /sentences
- The known-word proportion is fixed at >= 80%. Since this is fixed, the sentences can be prefetched on mount (before the user starts the session) so the user (hopefully) doesn't have to wait.
- handleKeyDown adds 'skipped' status if tab is pressed. Adds 'peeked' status if esc is pressed, and reveals the answer for as long it is held
- answerRevealed is set false on keyup or on blur in case focus is lost mid session
- Esc and tab both guard on e.repeat, so a held key counts once
- The input autofocuses, and blur refocuses it so typing isn't lost mid-session
- completedSentencesCount still increments on a peeked sentence, since it is progress towards the five rather than a score

## Backend (POST /sentences)

1. sample_introduced_words_for_generation - random 10 from introduced_words (TODO: make it constraint aware [Design idea](sentences.md#constraint-aware-eligibility-query))
2. get_eligible_sentences - check cache for sentences that meet requirements
3. if >= 3 eligible sentences, return them with id (early exit, no LLM generation)
4. else generate_sentences (LLM)
5. lemmatise_sentences - allows the words to be standardised and matched to the words in words table
6. insert_sentences - inserts sentence and gets IDs back
7. insert_sentences_words - inserts the words for said sentences
8. Sentence evaluation through get_eligible_sentences refetch - the updated cache should now contain eligible sentences from the generation, and therefore serves as an evaluation of the generated sentences
9. returns the sentences with their newly assigned id

## Edge cases

- lemma_count could be inflated since one surface word can be split into multiple lemmas (e.g 공부해 -> 공부 + 하다), and therefore a user who knows 공부 only gets half credit. TODO: verify the extract_lemmas output and test proportions are as expected.
- The threshold is a floor with no upper bound, so fully known sentences with no new words stay eligible
- If the generated sentences are not eligible, the get_eligible_sentences refetch will return a placeholder. How this is handled needs to be solved - [Design ideas](sentences.md#handling-ineligible-generated-sentences)
- A peeked sentence excludes all of its words from total_reviewed, not just the word that blocked the user - [Design idea](sentences.md#hovering-over-an-individual-word-shows-the-translation-of-that-specific-word)

## Design ideas

### Consider semantic priming - generated sentences should be evaluated for having their words connected

For example, it's easier to remember "the doctor and nurse went to hospital" than "the artist and driver went to the supermarket". I should have a syste in place to filter out sentences which seems like a random jumble of words.

### The number of words due for review should be made clear, and made obvious that sentences is an efficient way to review them

This is particularly in consideration of [Log entry](log.md#2026-09-29---sentences-top-priority-is-words-that-are-due-for-review-by-selection-algorithm), where it's evident that the core value of the sentences features is to efficiently get through words that are due for review and avoid falling behind. This should be made very obvious, for example with a count of words due for review (similar to how in Anki it says the number you need to work through), and make it obvious this is being rapidly deducted from with each sentence - since the sentences should be composed of words due for review as much as possible.

### Hovering over an individual word shows the translation of that specific word

Currently the peek option has a wide impact radius - in that if a user is blocked by a single word and they peek to resolve that word, the whole sentence gets 'peeked'. Instead it would be good to allow a user to see a specific word's translation. This could be done by returning each sentence as an array of work objects rather than a complete string, which each carring the displayed surface form, the lemma, and the lemmas translation. This can be resolved in one batched query, and since the frontend would render one element per word the hovering would be instant. A challenge is that the surface form has the partical etc, whereas the words database would just be the lemma - therefore, the tooltip can show for 공원에서, e.g 공원: Park. This also adds scope to add something additional for -에서 if I decide to implement this - but for now vocab lemma acts as a fair nudge.

### Guard against inflating total reviewed count from peeking sentences - for example, minimum individual words hovered over and attempt before peeking enables

I think it's very important that the 'total reviewed' count isn't super easy to increase. E.g, someone should not be able to peek at a sentence immediately, type it, and have the total reviewed count increase by 10 words or something. They need to work for it, otherwise there is not pride in a high number. On top of individual word hovering, there could additionally be some sort of guard to prevent 'peeking' on the whole sentence too soon - hence encourages people to actually try, rather than to flick through them. For example, they need to have typed at least something AND have viewed a certain proportion of individual lemmas - only then they can ESC to see the answer, and in that case the whole sentences is 'peeked'. Would be reasonable therefore to discount all words as 'reviewed' (or something similar) to maintain 'total reviewed' integrity. If not 'peeked' on the whole sentence (ESC), on the specific words they hovered over could get a 'peeked' status. This would require a migration to save which words in a sentence have been peeked, such as another table where the grain is each sentence's word and the individual status.

### Word tagging for user-steered content

- Tags table (many per word). The user states preference in plain English and an LLM maps that to EXISTING tags only (backend injects tag list — never free-form from user input for safety). Words can then be filtered by matched tags. Requires focus on how the words get tagged and how granular - perhaps a batch job by LLM and whenever a new words gets added.

### Constraint-aware eligibility query

- Currently the user words samples are random. However they should be constrained. This should be modular to make it easy to add more constraints in the future (such as sentence tags). Currently:
  - Proportion of user’s words to new words
  - Approx length of sentence
- Refinement: Instead of simply pulling a proportion of their introduced_words, there should be a per-word threshold (applied in get_eligible_sentences' user_introduced_words CTE). ie, the proportion of known words above a threshold confidence score that match the total number of lemmas in the sentence. This is unblocked after word confidence scoring is implemented.
- Refinement: Sample the words weighted by most due for review rather than at random, so the small generation sample is at least a purposeful one. Also depends on word confidence scoring.

### Handling ineligible generated sentences

- Solutions could include dropping a constraint, or increasing the number of generated sentences

### Skip budget and sentence budget

- For sentences, I need to add some sort of skip guard - e.g if a user continuously presses skip, they could continuously up LLM credits to no end. There could perhaps be something like, the user gets only 5 skips in a days or something. Similarly, there should be a sentence budget - perhaps more generous, like they can do 100 sentences a day.

### Skip is marked with timestamp

Currently (as planned) if a sentence is skipped, it will be excluded forever - the user will never see the sentence again. This is inefficient and more likely to lead to unnecessary LLM calls. Therefore, it could be better to mark a skip with a timestamp and after a set period it becomes available in the pool again.

## Open questions

### What happens to new words that arise in sentences

Current thoughts are that they are marked and given priority in the algorithm's selection of the next word. Therefore, the user can see them in sentences, and are more likely to see it again in the vocab session - but is not added to their vault/known words pipeline until it does come up.

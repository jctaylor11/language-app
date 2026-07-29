# Sentences feature reference (current state)

## Frontend

- SentenceSession uses useInfiniteQuery hook to fetch sentences: pages append and not replaced
- staleTime: Infinity means no automatic refetch. After the initial render, the next page is only explicitly fetched with fetchNextPage
- fetchNextPage is only fired when the (total - current index) <= 3
- fetchNextPage hits fetchSentencePairs, which hits POST /sentences
- The percentage of known words is selected as a range using a slider of width 20%, and is sent to backend as a point. The backend derives the upper and lower bounds

## Backend (POST /sentences)

1. sample_user_words - random 10 (TODO: make it constraint aware [Design idea](sentences.md#constraint-aware-eligibility-query))
2. get_eligible_sentences - check cache for sentences that meet requirements
3. if >= 3 eligible sentences, return them with id (early exit, no LLM generation)
4. else generate_sentences (LLM)
5. TODO: [Design idea](sentences.md#sentence-evals)
6. lemmatise_sentences - allows the words to be standardised and matched to the words in words table
7. insert_sentences - inserts sentence and gets IDs back
8. insert_sentences_words - inserts the words for said sentences
9. returns the sentences with their newly assigned id

## Edge cases

- lemma_count could be inflated since one surface word can be split into multiple lemmas (e.g 공부해 -> 공부 + 하다), and therefore a user who knows 공부 only gets half credit. TODO: verify the extract_lemmas output and test proportions are as expected.
- Extreme values on the band (e.g 80-100%) include fully known sentences with no new words

## Design ideas

### Word tagging for user-steered content

- Tags table (many per word). The user states preference in plain English and an LLM maps that to EXISTING tags only (backend injects tag list — never free-form from user input for safety). Words can then be filtered by matched tags. Requires focus on how the words get tagged and how granular - perhaps a batch job by LLM and whenever a new words gets added.

### Constraint-aware eligibility query

- Currently the user words samples are random. However they should be constrained. This should be modular to make it easy to add more constraints in the future (such as sentence tags). Currently:
  - Proportion of user’s words to new words
  - Approx length of sentence
- Refinement: Instead of simply pulling a proportion of their user_words, there should be a per-word threshold. ie, the proportion of known words above a threshold confidence score that match the total number of lemmas in the sentence. This is unblocked after word confidence scoring is implemented.

### Sentence evals

- Eval on the sentences generated to see if they can be returned. Even if they do not meet user's constraints, they should still be cached if they are correct as a Korean sentence

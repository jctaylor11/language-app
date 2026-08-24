# Sentences feature reference (current state)

## Frontend

- SentenceSession uses useInfiniteQuery hook to fetch sentences: pages append and not replaced
- staleTime: Infinity means no automatic refetch. After the initial render, the next page is only explicitly fetched with fetchNextPage
- fetchNextPage is only fired when the (total - current index) <= 3
- fetchNextPage hits fetchSentencePairs, which hits POST /sentences
- The known-word proportion is fixed at >= 80%. Since this is fixed, the sentences can be prefetched on mount (before the user starts the session) so the user (hopefully) doesn't have to wait.

## Backend (POST /sentences)

1. sample_user_words_for_generation - random 10 (TODO: make it constraint aware [Design idea](sentences.md#constraint-aware-eligibility-query))
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

## Design ideas

### Word tagging for user-steered content

- Tags table (many per word). The user states preference in plain English and an LLM maps that to EXISTING tags only (backend injects tag list — never free-form from user input for safety). Words can then be filtered by matched tags. Requires focus on how the words get tagged and how granular - perhaps a batch job by LLM and whenever a new words gets added.

### Constraint-aware eligibility query

- Currently the user words samples are random. However they should be constrained. This should be modular to make it easy to add more constraints in the future (such as sentence tags). Currently:
  - Proportion of user’s words to new words
  - Approx length of sentence
- Refinement: Instead of simply pulling a proportion of their user_words, there should be a per-word threshold. ie, the proportion of known words above a threshold confidence score that match the total number of lemmas in the sentence. This is unblocked after word confidence scoring is implemented.
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

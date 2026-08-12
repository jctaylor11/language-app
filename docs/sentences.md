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
5. lemmatise_sentences - allows the words to be standardised and matched to the words in words table
6. insert_sentences - inserts sentence and gets IDs back
7. insert_sentences_words - inserts the words for said sentences
8. Sentence evaluation through get_eligible_sentences refetch - the updated cache should now contain eligible sentences from the generation, and therefore serves as an evaluation of the generated sentences
9. returns the sentences with their newly assigned id

## Edge cases

- lemma_count could be inflated since one surface word can be split into multiple lemmas (e.g 공부해 -> 공부 + 하다), and therefore a user who knows 공부 only gets half credit. TODO: verify the extract_lemmas output and test proportions are as expected.
- Extreme values on the band (e.g 80-100%) include fully known sentences with no new words
- Since the generation prompt only takes a sample of words, the lower end of the preferred percentage of known words becomes increasingly less reliable, especially for more advanced users, since the chance of using a known word outside of the sample increases. TODO: [Design idea](sentences.md#known-percent-band-accuracy-for-generated-sentences)
- If the generated sentences are not eligible, the get_eligible_sentences refetch will return a placeholder. How this is handled needs to be solved - [Design ideas](sentences.md#handling-ineligible-generated-sentences)

## Design ideas

### Word tagging for user-steered content

- Tags table (many per word). The user states preference in plain English and an LLM maps that to EXISTING tags only (backend injects tag list — never free-form from user input for safety). Words can then be filtered by matched tags. Requires focus on how the words get tagged and how granular - perhaps a batch job by LLM and whenever a new words gets added.

### Constraint-aware eligibility query

- Currently the user words samples are random. However they should be constrained. This should be modular to make it easy to add more constraints in the future (such as sentence tags). Currently:
  - Proportion of user’s words to new words
  - Approx length of sentence
- Refinement: Instead of simply pulling a proportion of their user_words, there should be a per-word threshold. ie, the proportion of known words above a threshold confidence score that match the total number of lemmas in the sentence. This is unblocked after word confidence scoring is implemented.

### Known percent band accuracy for generated sentences

- The generation prompt only sees NUM_WORDS_SAMPLED words, so the LLM aims at the band using a fraction of the vocabulary the filter measures against. Sending the full vault instead was rejected - see log 2026-07-31. Current considerations for resolving requested band accuracy:
  - Generate more sentences than the batch needs and let the eligibility filter cull the ones that miss the band. Treats the symptom rather than the cause, and a request for a low known percentage may leave too few survivors
  - Sample the words most due for review rather than at random, so a small sample is at least a purposeful one. Depends on word confidence scoring - see [Constraint-aware eligibility query](sentences.md#constraint-aware-eligibility-query)

### Handling ineligible generated sentences

- Solutions could include dropping a constraint, or increasing the number of generated sentences

### Remove user's option to choose % of known words in the sentences

- Instead, it should just be a button that generates sentences using words that they know. Reasons behind this consideration are as follows:
  - Low reliability, leading to low integrity - for example, it may be difficult to guarantee '40-60%' of the sentence is known
  - The choice is arbitrary. Why would a user specifically want 40-60%? More likely to cognitive overload from choice.
  - The actual purpose of the program is comprehensible input, which the research supports is 80% known. One brain can fill in the other 20% from context. Therefore, it should really be 80% minimum - and evaluation can just check that 80% are known
  - Resolves the issue around what happens
  - New words should be considered a 'reward' for doing well, rather than abundant - having the option to generate sentences with 0% known words defeats this and makes it complicated about what happens with those new words.
  - Keeping it 80% minimum keeps things simple and focused on comprehensible input and word review, which is the primary purpose of the sentence generation. Leave word exploration to the vocab algorithm.

### Skip budget and sentence budget

- For sentences, I need to add some sort of skip guard - e.g if a user continuously presses skip, they could continuously up LLM credits to no end. There could perhaps be something like, the user gets only 5 skips in a days or something. Similarly, there should be a sentence budget - perhaps more generous, like they can do 100 sentences a day.

### Skip is marked with timestamp

Currently (as planned) if a sentence is skipped, it will be excluded forever - the user will never see the sentence again. This is inefficient and more likely to lead to unnecessary LLM calls. Therefore, it could be better to mark a skip with a timestamp and after a set period it becomes available in the pool again.

## Open questions

### What happens to new words that arise in sentences

Current thoughts are that they are marked and given priority in the algorithm's selection of the next word. Therefore, the user can see them in sentences, and are more likely to see it again in the vocab session - but is not added to their vault/known words pipeline until it does come up.

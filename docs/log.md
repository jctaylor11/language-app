### 2026-08-01 - sentences: queued sentence in frontend get sent in payload to sentences API

When finding eligible sentences, the SQL query first looks at sentences in the cachewhich contain a target percentage of known words from the user's word vault and excludes the sentences they've already done by looking at the user's sentence results. The eligible sentences are then queued in the frontend. As the user works through the sentences, another batched is refetched when then remaining sentences in the queue hit a threshold number (e.g 3 remaining). The sentences in the queue will not be in the sentence results, and therefore the refetch could still select these queued sentences. In doing so, the user would see the same sentence twice. Therefore, the payload for the fetchSentencePairs client API must be changed to send the IDs of sentences which are in the queue, and these will be excluded in the cache path query when fetching sentences.

Outcome: Implemented.

### 2026-07-31 - sentences: filter generated sentences based on known percent request using same cache query, after generated sentences are cached

The LLM is unrealiable, especailly since it only sees a sample of known words rather than the full thing. The generated sentences therefore cannot be returned directly, and they must be evaluated deterministically. More sentences than required are therefore generated and the eligible ones are returned. Since the generated sentences are processed and added to the sentences cache with their words mapped in sentence_words table, the same cache path that previously returned no results (calling get_eligible_sentences) will now surface the generated sentences (assuming they are eligible). This same function therefore serves as an evaluation to filter the eligible sentences, which keeps the sentence eligibility logic in one place, and keeping the vocab in the SQL.

Consequences: The connection to the function was changed from read_conn to write_conn, since it must be the same connection as the one that writes the generated sentences to the database - since the transaction is only committed when the endpoint returns.

Rejected alternatives:

- A dedicated function that would count the proportion of known lemmas, taking the user's full vocab vault into consideration. This would create two different implementations of the same rule, and would require all vocab to be queried from the database and compared in python.

Outcome: Implemented.

### 2026-07-31 - sentences: generation prompt keeps a sampled vocabulary

The generation prompt only sees a sample of the user's words, while the eligibility check measures the known proportion against all of their user_words. The LLM fills the rest of each sentence from general Korean, and some of those words will happen to be ones the user already knows, so actual coverage lands at or above the requested percentage. As the user's vault grows,the number of chance of general collision colliding with user words outside of the sample increases, especailly at the low end of the slider (e.g 0-20% known requested). Generating words a user does not know requires knowing which words they do know, which the LLM does not have a complete picture of. The solution to this is an open question, with considerations in [design ideas](sentences.md#known-percent-band-accuracy-for-generated-sentences)

The rejected consideration was to add more context by sending the full vocabulary in the prompt. This is not viable since it increases cost and reduces instruction adherence since. LLMs (especially cheap and fast models) are not optimised for counting and selectively focus attention (e.g they'll ingore words at the end of the list). Design consideration for resolving this are in [Known percent band accuracy for generated sentences](sentences.md#known-percent-band-accuracy-for-generated-sentences).

### 2026-07-28 - sentences: generation slider input kept as integer

Generation target percentage is kept as an integer instead of a float and evaluated as integers (by multuiplying by 100 instead of dividing). This avoids floating point imprecision when adding/substracting the bounds, which would cause proportions to be incorrectly evaluated. For example, a lower bound of 0.7 would be marginally higher with the floating point imprecision, and therefore a sentence with 70% known lemmas would return false (e.g 0.700000000 < 0.700000001).

Outcome: Implemented.

### 2026-07-28 - sentences: generation slider shifts inwards

At the extreme ends of the slider, e.g at 100% known words in the generated sentence, the bounds should slide inwards so that that lower bound is -20, instead of -10 (since the upper bound cannot +10 to 110%). By making it shift inwards by another 10 it keeps the band constant at 20%. The rejected alternative was to truncate the band, but this would make the width inconsistent.

Outcome: Implemented.

### 2026-07-23 - dashboard: add page to display sentences seen by user

All sentences seen by the user are displayed in the Sentence Vault page of the dashboard. Sentences are currently not shown again once they're already seen, and sentence accuracy/time data isn't their purpose - vocab is the main driver of data, whereas sentences are just intended as a way to review those individual vocab words in context (with 'comprehensible input'). Therefore this page just serves as a collection/reference of sentences the user should be familiar with, rather than for any analysis, and there is no real need to display anything more than the sentences themselves. Possibly 'answered_at' field could be added though.

Outcome: Implemented.

### 2026-07-21 - sentences: control slider has wide step

The step for the slider for proportion of known words for the sentence generation has a wide step of 20 due to precision. Anything lower would imply more precision of what we can gaurantee. A tolerance of ±10% seems feasible. 20 was also chosen since it covers 80% - which research suggests is the optimal percentage for comprehensible input.
Update: Step changed to 10, band set to 20. The band slider of width 20% dropped the 80% midpoint, and setting a step of 10 now restores it.

Outcome: Implemented.

### 2026-07-19 - sentences: sentence cache path as single query

I can just keep the fetching applicable user words and searching for eligible sentences all to just one SQL query. This also works better to keep everything in the database, remove a moving part, and the match runs as a hash join instead of passing a list of keys (more efficient than two queries, one to fetch, and searching with that list). The query look something like this:

1. A CTE that contains all the of the user's words - (user_words where user_id = :user_id)
2. JOIN sentences + sentence_words + user_words: There will be one row per (sentence, matched word from user_words CTE)
3. WHERE to filter for the NOT EXISTS in the user’s current sentences
4. COUNT the rows, aggregated by sentence ID (ie, it will collapse sentence ID and show a count for how many user_words matched up with sentence_words for that table)
5. `HAVING COUNT(*) >= 0.8 * s.lemma_count` - this avoids division to avoid division by zero error and integer division, and filters for sentences with over threshold proportion of known words

Outcome: Implemented.

### 2026-07-19 - sentences: cache search uses all user words

The cache search should not take a certain number of words. I should take as many words as are applicable and then use that to search the cache for any sentences. To start, I will take ALL the words in their user_words. Later, I can whittle it down weighted by whatever the algorithm I build considers are the best words to be reviewed by the user.

However, I should still constrain the user words for the sentence generation path, since it is unnecessary to pass excessive words and costs credits for the API.

Outcome: Implemented.

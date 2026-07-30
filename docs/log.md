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

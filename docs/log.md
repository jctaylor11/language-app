### 2026-07-19 - sentences: sentence cache path as single query

I can just keep the fetching applicable user words and searching for eligible sentences all to just one SQL query. This also works better to keep everything in the database, remove a moving part, and the match runs as a hash join instead of passing a list of keys (more efficient than two queries, one to fetch, and searching with that list). The query look something like this:

1. A CTE that contains all the of the user's words - (user_words where user_id = :user_id)
2. JOIN sentences + sentence_words + user_words: There will be one row per (sentence, matched word from user_words CTE)
3. WHERE to filter for the NOT EXISTS in the user’s current sentences
4. COUNT the rows, aggregated by sentence ID (ie, it will collapse sentence ID and show a count for how many user_words matched up with sentence_words for that table)
5. `HAVING COUNT(*) >= 0.8 * s.lemma_count` - this avoids division to avoid division by zero error and integer division, and filters for sentences with over threshold proportion of known words

### 2026-07-19 - sentences: cache search uses all user words

The cache search should not take a certain number of words. I should take as many words as are applicable and then use that to search the cache for any sentences. To start, I will take ALL the words in their user_words. Later, I can whittle it down weighted by whatever the algorithm I build considers are the best words to be reviewed by the user.

However, I should still constrain the user words for the sentence generation path, since it is unnecessary to pass excessive words and costs credits for the API.

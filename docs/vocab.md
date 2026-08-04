# Vocab feature reference (current state)

## Frontend

- On mount, getOrCreateSession reads sessionId from sessionStorage. If none,a creates one with POST /sessions. Session is defined as a browser tab.
- useInfiniteQuery hook is used to fetch words, in pages (appended, not replaced). staleTime: Infinity means no automatic refetch - only fetched with fetchNextPage when remaining words <= 3
- fetchNextPage hits fetchWords, which hits GET /words - a random batch of 5, with no level or review awareness yet (TODO: [Design idea](vocab.md#add-vocab-control))
- Word pages are flattened into one array and wordIndex is an index into it
- inputText is state rather than a ref so the input stays controlled and each keypress re-renders the card
- Each keypress runs handleInputChange, which compares the input against currentWord.source. If it matches, it builds the results, advances the word, then sends them oer POST /vocab-results. Results are built before advanceWord (which resets wordShownTime) and sendVocabResults is awaited after it, so the response time stays accurate and the UI isn't held up
- handleKeyDown catches tab/esc with preventDefault and advances word with 'skipped' status
- keystrokes and wordShownTime are refs to avoid a re-render per keypress
- sessionPosition storesd in sessionStorage to survive reload alongside sessionId
- if currentWord is undefined, the Loading... branch is rendered

## Backend (GET /words, POST /vocab-results)

### GET /words

1. user_id is injected from decode_access_token
2. sample_word_batch samples 5 words from the user_words (currently at random - selection algorithm to be added)
3. Rows are returned as word_batch with id, target and source. The id is used for sending the results back in payload

### POST /vocab-results

1. Result parameters from the user's input are built one dict per word result, with user_id from the token and session_id from the payload merged into each row, so the insert is a single executemany
2. insert_vocab_results inserts batch of results into vocab_results. It is the raw data for everything derived later (e.g dashboard, confidence scoring)
3. sessions.completed_at is re-stamped with NOW() on every flush, so it currently means 'last activity' gets updated until it is truly the last activity
4. Returns the number of results saved

## Edge cases

## Design ideas

### Add vocab control

- Similar to the sentence generation control in Sentences. Bounding the start has benefits:
  - Informs about the page/purpose of so the user understand the program better (ie algorithm automatically selects which word - either review word or a new work - based on their data, SRS etc. They just need to focus on what it throws at them and the algorithm handles the rest)
  - Hides the 'loading' transition which fetching from database - words could be fetched the moment the page mounts.
  - Provides scope for options. [Open question known split](#session-known-vs-unknown-option)

### Assess response time with time-into-session

- It's possible the time into the session may influence the user's response - e.g rushing at the end to get more words in, or feeling fresh at the start to go faster. This data should be considered - and if there are negative patterns (e.g rushing at the end), could neglect this data.

### Clear 'Go again' CTA along with the session summary

- It's very easy to do just a 2 minute session, less easy to commit to a 10 minute session. However, someone who starts the 2 minutes is likely to continue - and they could do 10 minutes with 5x 2 minutes. Which also equate to 5 summaries (ie 5 rewards), which will likely keep them engaged.

## Open questions

### Session known vs unknown option?

Should there be an option for a user to just cycle through words to review, or to only get new words? If only the algorithm can decide, then progress could feel too fast or too slow. There needs to be some way to calibrate or control this.

### User editing vocab vault

The user should be able to alter the data in their vocab vault - they should have full access to add or delete words, make assertions etc on confidence, and the algorithm adapts.

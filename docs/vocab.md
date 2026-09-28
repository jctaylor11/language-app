# Vocab feature reference (current state)

## Frontend

- VocabStart is rendered until a session exists. Its onStart calls sessionMutate directly
- The mutation calls fetchSession, which POSTs to /sessions with bound_type and bound_value (currently time and 120 for vocab sessions). sessionId is held in the mutation's data so that a refresh resets it
- Session creation is a useMutation rather than a useQuery because it writes. A query would re-run on window focus, retry and StrictMode, creating a session row each time
- onSuccess holds all of the session setup, so nothing is initialised for a session that failed to be created
- useInfiniteQuery hook is used to fetch words, in pages (appended, not replaced). staleTime: Infinity means no automatic refetch - only fetched with fetchNextPage when remaining words <= 3
- fetchNextPage hits fetchWords, which hits GET /words - a random batch of 5, with no level or review awareness yet (TODO: [Design idea](vocab.md#add-vocab-control))
- Word pages are flattened into one array and wordIndex is an index into it
- inputText is state rather than a ref so the input stays controlled and each keypress re-renders the card
- Each keypress runs handleInputChange, which compares the input against currentWord.source. If it matches, it builds the results, advances the word, then sends them over POST /vocab-results. Results are built before advanceWord since advanceWord resets the wordShownTime
- handleKeyDown catches tab with preventDefault and advances word with 'skipped' status
- handleKeyDown catches esc with preventDefault and reveals the source word for as long as it is held. answerRevealed is set false on keyup or on blur in case focus is lost mid session
- Both guard on e.repeat for idempotency
- keystrokes and wordShownTime are refs to avoid a re-render per keypress. wordShownTime starts at 0 so time spent on the VocabStart isn't counted into the first word
- Timer derives timeRemaining from the sessionStartTime prop against Date.now() rather than decrementing a counter to avoid drift
- SessionSummary fetches metrics from database with useQuery to ensure faithful representation by gating on the number of in-flight requests being 0 (from useIsMutating)
- 'New Session' calls sessionMutate again. onSuccess resets sessionFinished
- Timer onFinish increments wordIndex so the first word of the new session is fresh
- A score is incremented and displayed top right for each non-skipped and non-cheated word submitted

## Backend (GET /words, POST /vocab-results, GET /vocab-sessions/{session_id}/summary)

### GET /words

1. user_id is injected from decode_access_token
2. sample_word_batch samples 5 words from all words (placeholder at random - selection algorithm to be added, which will choose whether to review or introduce a word)
3. Rows are returned as word_batch with id, target and source. The id is used for sending the results back in payload

### POST /vocab-results

1. Result parameters from the user's input are built one dict per word result, with user_id from the token and session_id from the payload merged into each row, so the insert is a single executemany
2. insert_vocab_results inserts batch of results into vocab_results. It is the raw data for everything derived later (e.g dashboard, confidence scoring)
3. sessions.completed_at is re-stamped with NOW() on every flush, so it currently means 'last activity' gets updated until it is truly the last activity
4. Returns the number of results saved

### GET /vocab-sessions/{session_id}/summary

1. session_results CTE narrows vocab_results to that session and user, excluding skipped and cheated
2. total_reviewed counts every row, so the same word answered twice in one session counts twice
3. new_words counts distinct words with no earlier non-skipped result from another session
4. Returns both as summary metrics

## Edge cases

- The current word when the timer ends is dropped and skipped intentionally - 2 minute session time is protected, and having it as the first word for the next would systematically lower response time since the user has already seen it
- Words can current repeat in the same session. This raises the consideration regarding 'words reviewed'. Currently, two of the same words coming in the same session count as two reviewed.

## Design ideas

### Quitting a session early drops the data from that session

Originally I've been thinking to make it save the data continuously - if they do 10 words in 20 seconds and quit before the 2 minute timer is over, it would still increase 'total reviewed' by 10. However, I realise this reduces the integrity of a session being 2 minutes, and changes it to a session being 'maximum 2 minutes'. This could result to a decrease in motivation also, where there is no drive to complete a session. The 'reward' for completing a session is having that data saved. Else, it becomes optional.

### Include skipped words in the session overview, but have another visual state

Currently skipped words are not included since skipped signals complete distinterest. However, it may actually be useful to see that record. For example, they could have another visual state which references the word but makes it clear it was skipped (e.g even more greyed out than a cheated word).

### Cheated words are displayed in session log's session overview, but are greyed out to separate them

The cheated words should be included in the session overview as per [log decision](log.md#2026-08-29---vocab-cheated-words-are-shown-in-the-session-log-overview-but-do-not-count-as-a-review-point-or-a-new-word) - but they should not be indistinguishable. They should be greyed out, or italicised or something like this.

### Add vocab control

- Similar to the sentence generation control in Sentences. Bounding the start has benefits:
  - Informs about the page/purpose of so the user understand the program better (ie algorithm automatically selects which word - either review word or a new work - based on their data, SRS etc. They just need to focus on what it throws at them and the algorithm handles the rest)
  - Hides the 'loading' transition which fetching from database - words could be fetched the moment the page mounts.
  - Provides scope for options. [Open question known split](#session-known-vs-unknown-option)

### Assess response time with time-into-session

- It's possible the time into the session may influence the user's response - e.g rushing at the end to get more words in, or feeling fresh at the start to go faster. This data should be considered - and if there are negative patterns (e.g rushing at the end), could neglect this data.

### Clear 'Go again' CTA along with the session summary

- It's very easy to do just a 2 minute session, less easy to commit to a 10 minute session. However, someone who starts the 2 minutes is likely to continue - and they could do 10 minutes with 5x 2 minutes. Which also equate to 5 summaries (ie 5 rewards), which will likely keep them engaged.

### Words being reviewed can only appear once in one session

- Currently words can get sampled twice in the same session, and therefore the user could review the same word multiple times and this counts as multiple reviews for that session. However, seeing the same word twice in quick succession is redundant. There could be a filter that stops the same word from appearing twice in the same session. This would keep integrity with the 'words reviewed' metric in the session summary. However one consideration - what about for new users where they don't have many words? Though, arguable, if they don't have many words, that is a time moreso for exploration of words to guage their level (Bayesian priors) rather than focusing on review. Exploration is more valuable earlier on, and review is more valuable later on.

### Set timer from backend variable, rather than trusting frontend

Currently the timer is set by a variable passed in from the frontend.

## Open questions

### Session known vs unknown option?

Should there be an option for a user to just cycle through words to review, or to only get new words? If only the algorithm can decide, then progress could feel too fast or too slow. There needs to be some way to calibrate or control this.

### User editing vocab vault

The user should be able to alter the data in their vocab vault - they should have full access to add or delete words, make assertions etc on confidence, and the algorithm adapts.
